// Deterministic gameplay kernel for 叠桥冲刺 (Stack Path Runner).
// Original clean-room design: no source art, geometry, colors or values.
//
// Model: the runner moves forward automatically; the player only steers
// horizontally in [-1, 1]. Pickups add exactly one stack unit each, once.
// Obstacles charge an authored penalty once per obstacle. Entering a gap
// atomically spends its full cost — insufficient units lose before any
// negative stack state can occur. The stack is never negative.

const clamp = (value, lo, hi) => Math.min(hi, Math.max(lo, value));

function pickupLine(prefix, x, startZ, count, spacing) {
  const pickups = [];
  for (let i = 0; i < count; i += 1) {
    pickups.push({ id: `${prefix}${i + 1}`, z: startZ + i * spacing, x });
  }
  return pickups;
}

export const LEVELS = Object.freeze({
  1: Object.freeze({
    id: 'warm-up',
    number: 1,
    speed: 6,
    steerSpeed: 1.6,
    reach: 0.35,
    finish: 40,
    // A centered pickup line overfunds one short bridge: staying centered wins.
    pickups: Object.freeze(pickupLine('c', 0, 4, 6, 2)),
    obstacles: Object.freeze([]),
    gaps: Object.freeze([{ id: 'g1', z: 20, span: 6, cost: 3 }]),
  }),
  2: Object.freeze({
    id: 'skill-gate',
    number: 2,
    speed: 6,
    steerSpeed: 2.2,
    reach: 0.35,
    finish: 66,
    // Pickups split across left and right lanes; a centered obstacle punishes
    // late steering; two gap budgets require actively collecting both lanes.
    pickups: Object.freeze([
      ...pickupLine('L', -0.6, 6, 5, 2),
      ...pickupLine('R', 0.6, 22, 5, 2),
      ...pickupLine('T', -0.6, 42, 3, 2),
    ]),
    obstacles: Object.freeze([{ id: 'ob1', z: 17, x: 0, penalty: 2 }]),
    gaps: Object.freeze([
      { id: 'g1', z: 36, span: 5, cost: 6 },
      { id: 'g2', z: 56, span: 6, cost: 7 },
    ]),
  }),
});

// A deterministic trace ([steer, seconds] segments, 1/120 s step) that wins
// level 2: collect the left lane, cross after the obstacle, collect the right
// lane, then return left for the tail pickups across both gaps.
export const LEVEL2_WINNING_TRACE = Object.freeze([
  [-1, 0.3],
  [0, 2.6],
  [1, 0.6],
  [0, 1.6],
  [-1, 0.6],
  [0, 5.4],
]);

export function createGame(levelNumber) {
  const level = LEVELS[levelNumber];
  if (!level) {
    throw new Error(`unknown level: ${levelNumber}`);
  }
  return {
    levelNumber,
    z: 0,
    x: 0,
    steer: 0,
    stack: 0,
    status: 'running',
    reason: null,
    time: 0,
    collected: {},
    obstaclesCharged: {},
    gapsPaid: {},
  };
}

export function setSteer(state, value) {
  if (!Number.isFinite(value)) {
    throw new Error(`steer must be a finite number, got ${value}`);
  }
  state.steer = clamp(value, -1, 1);
  return state;
}

function crossings(level, state, prevZ, newZ, newX) {
  const events = [];
  for (const pickup of level.pickups) {
    if (
      !state.collected[pickup.id] &&
      prevZ < pickup.z && pickup.z <= newZ &&
      Math.abs(newX - pickup.x) <= level.reach
    ) {
      events.push({ z: pickup.z, order: 0, kind: 'pickup', item: pickup });
    }
  }
  for (const obstacle of level.obstacles) {
    if (
      !state.obstaclesCharged[obstacle.id] &&
      prevZ < obstacle.z && obstacle.z <= newZ &&
      Math.abs(newX - obstacle.x) <= level.reach
    ) {
      events.push({ z: obstacle.z, order: 1, kind: 'obstacle', item: obstacle });
    }
  }
  for (const gap of level.gaps) {
    if (!state.gapsPaid[gap.id] && prevZ < gap.z && gap.z <= newZ) {
      events.push({ z: gap.z, order: 2, kind: 'gap', item: gap });
    }
  }
  events.sort((a, b) => a.z - b.z || a.order - b.order || (a.item.id < b.item.id ? -1 : 1));
  return events;
}

function stepOnce(state, dt) {
  const level = LEVELS[state.levelNumber];
  const prevZ = state.z;
  const newX = clamp(state.x + state.steer * level.steerSpeed * dt, -1, 1);
  const newZ = prevZ + level.speed * dt;

  for (const event of crossings(level, state, prevZ, newZ, newX)) {
    if (event.kind === 'pickup') {
      state.collected[event.item.id] = true;
      state.stack += 1;
    } else if (event.kind === 'obstacle') {
      state.obstaclesCharged[event.item.id] = true;
      if (state.stack < event.item.penalty) {
        state.status = 'lost';
        state.reason = 'insufficient_stack_for_obstacle';
      } else {
        state.stack -= event.item.penalty;
      }
    } else if (state.stack < event.item.cost) {
      // Atomic gap check: never spend part of a cost.
      state.status = 'lost';
      state.reason = 'insufficient_stack_for_gap';
    } else {
      state.stack -= event.item.cost;
      state.gapsPaid[event.item.id] = true;
    }
    if (state.status !== 'running') {
      break;
    }
  }

  state.x = newX;
  state.z = newZ;
  state.time += dt;
  if (state.status === 'running' && newZ >= level.finish) {
    state.status = 'won';
  }
}

export function advance(state, seconds, step = 1 / 120) {
  if (!Number.isFinite(seconds) || seconds < 0) {
    throw new Error(`seconds must be a nonnegative finite number, got ${seconds}`);
  }
  if (!Number.isFinite(step) || step <= 0) {
    throw new Error(`step must be a positive finite number, got ${step}`);
  }
  const steps = Math.round(seconds / step);
  for (let i = 0; i < steps && state.status === 'running'; i += 1) {
    stepOnce(state, step);
  }
  return state;
}

export function runTrace(levelNumber, trace, step = 1 / 120) {
  const state = createGame(levelNumber);
  for (const [steer, seconds] of trace) {
    if (state.status !== 'running') {
      break;
    }
    setSteer(state, steer);
    advance(state, seconds, step);
  }
  return state;
}

export function getPublicState(state) {
  const level = LEVELS[state.levelNumber];
  return {
    levelNumber: state.levelNumber,
    levelId: level.id,
    z: state.z,
    x: state.x,
    steer: state.steer,
    stack: state.stack,
    status: state.status,
    reason: state.reason,
    time: state.time,
    progress: clamp(state.z / level.finish, 0, 1),
    collectedCount: Object.keys(state.collected).length,
    gapsPaidCount: Object.keys(state.gapsPaid).length,
  };
}
