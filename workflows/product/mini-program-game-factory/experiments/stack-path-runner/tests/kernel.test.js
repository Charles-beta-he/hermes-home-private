import test from 'node:test';
import assert from 'node:assert/strict';

import {
  LEVELS,
  LEVEL2_WINNING_TRACE,
  createGame,
  setSteer,
  advance,
  getPublicState,
  runTrace,
} from '../src/kernel.js';

const STEP = 1 / 120;

function advanceChecked(state, seconds) {
  // Advance in small slices and assert the nonnegative-stack invariant
  // at every observable point.
  let remaining = seconds;
  while (remaining > 1e-9) {
    const slice = Math.min(remaining, 0.1);
    advance(state, slice, STEP);
    assert.ok(state.stack >= 0, `stack must stay nonnegative, got ${state.stack}`);
    remaining -= slice;
  }
  return state;
}

test('level definitions expose a warm-up and a skill-gate level', () => {
  assert.equal(LEVELS[1].id, 'warm-up');
  assert.equal(LEVELS[2].id, 'skill-gate');
  assert.ok(LEVELS[2].gaps.length === 2, 'level 2 must contain two resource checks');
});

test('createGame rejects unknown levels', () => {
  assert.throws(() => createGame(3));
  assert.throws(() => createGame(0));
});

test('level 1 centered no-input play wins with surplus stack', () => {
  const state = createGame(1);
  advanceChecked(state, 8);
  assert.equal(state.status, 'won');
  assert.equal(Object.keys(state.collected).length, LEVELS[1].pickups.length);
  assert.equal(state.stack, LEVELS[1].pickups.length - LEVELS[1].gaps[0].cost);
});

test('each pickup adds exactly one stack unit and is collected once', () => {
  const state = createGame(1);
  advanceChecked(state, 8);
  const collectedIds = Object.keys(state.collected).sort();
  const levelIds = LEVELS[1].pickups.map((p) => p.id).sort();
  assert.deepEqual(collectedIds, levelIds);
});

test('level 2 no-input play loses', () => {
  const state = createGame(2);
  advanceChecked(state, 14);
  assert.equal(state.status, 'lost');
  assert.ok(state.reason, 'loss must carry a reason');
});

test('level 2 left-only steering loses at the first gap with stack unchanged', () => {
  const state = runTrace(2, [
    [-1, 0.3],
    [0, 20],
  ]);
  assert.equal(state.status, 'lost');
  assert.equal(state.reason, 'insufficient_stack_for_gap');
  // Atomic gap spending: a failed check must not partially spend units.
  assert.equal(state.stack, 5);
  assert.equal(Object.keys(state.gapsPaid).length, 0);
});

test('level 2 right-only steering loses at the first gap', () => {
  const state = runTrace(2, [
    [1, 0.35],
    [0, 20],
  ]);
  assert.equal(state.status, 'lost');
  assert.equal(state.reason, 'insufficient_stack_for_gap');
  assert.equal(state.stack, 5);
});

test('obstacle penalty is charged exactly once', () => {
  // Collect the left lane, then deliberately drift back to center into
  // the obstacle while holding enough stack to survive the hit.
  const trace = [
    [-1, 0.3],
    [0, 2.2],
    [1, 0.3],
    [0, 0.5],
  ];
  const state = runTrace(2, trace);
  assert.equal(state.status, 'running');
  assert.equal(Object.keys(state.obstaclesCharged).length, 1);
  assert.equal(state.stack, 5 - LEVELS[2].obstacles[0].penalty);
  const stackAfterHit = state.stack;
  advanceChecked(state, 1);
  assert.equal(Object.keys(state.obstaclesCharged).length, 1);
  assert.equal(state.stack, stackAfterHit);
});

test('insufficient stack at an obstacle loses', () => {
  const state = createGame(2);
  advanceChecked(state, 14);
  assert.equal(state.status, 'lost');
  assert.equal(state.reason, 'insufficient_stack_for_obstacle');
  assert.equal(state.stack, 0);
});

test('level 2 deterministic winning trace steers both directions and wins', () => {
  const hasLeft = LEVEL2_WINNING_TRACE.some(([steer]) => steer < 0);
  const hasRight = LEVEL2_WINNING_TRACE.some(([steer]) => steer > 0);
  assert.ok(hasLeft && hasRight, 'winning trace must materially steer left and right');

  const state = runTrace(2, LEVEL2_WINNING_TRACE);
  assert.equal(state.status, 'won');
  assert.equal(Object.keys(state.gapsPaid).length, 2);
  assert.equal(Object.keys(state.obstaclesCharged).length, 0);
  assert.ok(state.stack >= 0);
});

test('kernel simulation is deterministic for a fixed trace', () => {
  const first = runTrace(2, LEVEL2_WINNING_TRACE);
  const second = runTrace(2, LEVEL2_WINNING_TRACE);
  assert.deepEqual(JSON.parse(JSON.stringify(first)), JSON.parse(JSON.stringify(second)));
});

test('advancing in different chunk sizes with the same step is identical', () => {
  const whole = createGame(1);
  advance(whole, 3, STEP);
  const chunked = createGame(1);
  for (let i = 0; i < 30; i += 1) {
    advance(chunked, 0.1, STEP);
  }
  assert.deepEqual(JSON.parse(JSON.stringify(whole)), JSON.parse(JSON.stringify(chunked)));
});

test('setSteer clamps input to [-1, 1] and rejects non-finite values', () => {
  const state = createGame(1);
  setSteer(state, 5);
  assert.equal(state.steer, 1);
  setSteer(state, -7);
  assert.equal(state.steer, -1);
  setSteer(state, 0.25);
  assert.equal(state.steer, 0.25);
  assert.throws(() => setSteer(state, Number.NaN));
});

test('a finished game does not advance further', () => {
  const state = createGame(1);
  advanceChecked(state, 8);
  assert.equal(state.status, 'won');
  const frozen = JSON.parse(JSON.stringify(state));
  advance(state, 2, STEP);
  assert.deepEqual(JSON.parse(JSON.stringify(state)), frozen);
});

test('getPublicState reports level, progress, stack and status without internals', () => {
  const state = createGame(2);
  advanceChecked(state, 1);
  const pub = getPublicState(state);
  assert.equal(pub.levelNumber, 2);
  assert.equal(pub.status, 'running');
  assert.equal(typeof pub.stack, 'number');
  assert.ok(pub.progress > 0 && pub.progress < 1);
  assert.ok(!('collected' in pub));
  assert.equal(typeof pub.collectedCount, 'number');
});
