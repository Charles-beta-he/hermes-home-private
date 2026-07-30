import { ContentPack, validateContentPack } from './content-pack.js';

const UP = 1;
const RIGHT = 2;
const DOWN = 4;
const LEFT = 8;
const DIRECTIONS = [
  { bit: UP, opposite: DOWN, row: -1, col: 0 },
  { bit: RIGHT, opposite: LEFT, row: 0, col: 1 },
  { bit: DOWN, opposite: UP, row: 1, col: 0 },
  { bit: LEFT, opposite: RIGHT, row: 0, col: -1 },
] as const;

export type GameStatus = 'playing' | 'won' | 'lost';
export interface Tile { index: number; goalMask: number; rotation: number; path: boolean }
export interface GameState {
  kernelId: 'circuit-untangle';
  contentId: string;
  gridSize: number;
  movesLeft: number;
  seed: number;
  source: number;
  targets: number[];
  tiles: Tile[];
  hintsUsed: number;
  status: GameStatus;
}
export type GameAction =
  | { type: 'rotate_node'; index: number }
  | { type: 'swap_adjacent'; first: number; second: number }
  | { type: 'request_hint' };
export interface Evaluation { powered: number[]; allTargetsConnected: boolean; shortCircuit: boolean }

function rng(seed: number): () => number {
  let state = seed >>> 0;
  return () => {
    state = (Math.imul(state, 1664525) + 1013904223) >>> 0;
    return state / 0x100000000;
  };
}

function rotateMask(mask: number, turns: number): number {
  let output = mask;
  for (let i = 0; i < turns % 4; i += 1) {
    output = ((output << 1) & 0b1111) | ((output & LEFT) ? UP : 0);
  }
  return output;
}

function position(index: number, size: number): { row: number; col: number } {
  const pathRow = Math.floor(index / size);
  const offset = index % size;
  return { row: pathRow, col: pathRow % 2 === 0 ? offset : size - 1 - offset };
}

function boardIndex(pathIndex: number, size: number): number {
  const point = position(pathIndex, size);
  return point.row * size + point.col;
}

function directionBetween(first: number, second: number, size: number): number {
  const a = { row: Math.floor(first / size), col: first % size };
  const b = { row: Math.floor(second / size), col: second % size };
  if (b.row === a.row - 1 && b.col === a.col) return UP;
  if (b.row === a.row && b.col === a.col + 1) return RIGHT;
  if (b.row === a.row + 1 && b.col === a.col) return DOWN;
  if (b.row === a.row && b.col === a.col - 1) return LEFT;
  throw new Error('generated path is not adjacent');
}

function withStatus(state: GameState): GameState {
  const evaluation = evaluateState(state);
  const status: GameStatus = evaluation.allTargetsConnected && !evaluation.shortCircuit
    ? 'won'
    : state.movesLeft <= 0 ? 'lost' : 'playing';
  return { ...state, status };
}

export function createGame(content: ContentPack, seed: number): GameState {
  const valid = validateContentPack(content);
  if (!Number.isInteger(seed)) throw new Error('seed must be an integer');
  const size = valid.levelParameters.gridSize;
  const pathLength = valid.levelParameters.targetCount + 1;
  const path = Array.from({ length: pathLength }, (_, index) => boardIndex(index, size));
  const random = rng(seed);
  const tiles: Tile[] = Array.from({ length: size * size }, (_, index) => ({
    index,
    goalMask: 0,
    rotation: 0,
    path: false,
  }));
  path.forEach((index, order) => {
    let mask = 0;
    if (order > 0) mask |= directionBetween(index, path[order - 1], size);
    if (order < path.length - 1) mask |= directionBetween(index, path[order + 1], size);
    tiles[index] = { index, goalMask: mask, rotation: Math.floor(random() * 4), path: true };
  });
  if (path.every((index) => tiles[index].rotation === 0)) tiles[path[0]] = { ...tiles[path[0]], rotation: 1 };
  return withStatus({
    kernelId: 'circuit-untangle',
    contentId: valid.contentId,
    gridSize: size,
    movesLeft: valid.levelParameters.moves,
    seed,
    source: path[0],
    targets: path.slice(1),
    tiles,
    hintsUsed: 0,
    status: 'playing',
  });
}

export function evaluateState(state: GameState): Evaluation {
  const powered = new Set<number>([state.source]);
  const queue = [state.source];
  let shortCircuit = false;
  while (queue.length) {
    const current = queue.shift() as number;
    const row = Math.floor(current / state.gridSize);
    const col = current % state.gridSize;
    const mask = rotateMask(state.tiles[current].goalMask, state.tiles[current].rotation);
    for (const direction of DIRECTIONS) {
      if (!(mask & direction.bit)) continue;
      const nextRow = row + direction.row;
      const nextCol = col + direction.col;
      if (nextRow < 0 || nextCol < 0 || nextRow >= state.gridSize || nextCol >= state.gridSize) {
        shortCircuit = true;
        continue;
      }
      const next = nextRow * state.gridSize + nextCol;
      const nextMask = rotateMask(state.tiles[next].goalMask, state.tiles[next].rotation);
      if (!(nextMask & direction.opposite)) {
        shortCircuit = true;
        continue;
      }
      if (!powered.has(next)) {
        powered.add(next);
        queue.push(next);
      }
    }
  }
  return {
    powered: [...powered].sort((a, b) => a - b),
    allTargetsConnected: state.targets.every((target) => powered.has(target)),
    shortCircuit,
  };
}

function adjacent(first: number, second: number, size: number): boolean {
  const rowA = Math.floor(first / size);
  const rowB = Math.floor(second / size);
  const colA = first % size;
  const colB = second % size;
  return Math.abs(rowA - rowB) + Math.abs(colA - colB) === 1;
}

export function applyAction(state: GameState, action: GameAction): GameState {
  if (state.status !== 'playing') throw new Error('cannot act on a terminal state');
  const tiles = state.tiles.map((tile) => ({ ...tile }));
  let movesLeft = state.movesLeft;
  let hintsUsed = state.hintsUsed;
  if (action.type === 'rotate_node') {
    if (!tiles[action.index]) throw new Error('rotate_node index out of range');
    tiles[action.index].rotation = (tiles[action.index].rotation + 1) % 4;
    movesLeft -= 1;
  } else if (action.type === 'swap_adjacent') {
    if (!tiles[action.first] || !tiles[action.second] || !adjacent(action.first, action.second, state.gridSize)) {
      throw new Error('swap_adjacent requires adjacent valid indices');
    }
    const a = tiles[action.first];
    const b = tiles[action.second];
    tiles[action.first] = { ...b, index: action.first };
    tiles[action.second] = { ...a, index: action.second };
    movesLeft -= 1;
  } else {
    const hint = tiles.find((tile) => tile.path && tile.rotation !== 0);
    if (hint) hint.rotation = 0;
    hintsUsed += 1;
  }
  return withStatus({ ...state, tiles, movesLeft, hintsUsed });
}

export function scoreState(state: GameState): number {
  if (state.status !== 'won') return 0;
  return Math.max(1, 1000 + state.movesLeft * 10 - state.hintsUsed * 100);
}
