import { readFile } from 'node:fs/promises';
import assert from 'node:assert/strict';
import test from 'node:test';

import {
  applyAction,
  createGame,
  evaluateState,
  scoreState,
} from '../dist/gameplay-kernel.js';
import { normalizeContentPack, validateContentPack } from '../dist/content-pack.js';

const content = {
  contentId: 'data-center-repair-zh-cn',
  kernelId: 'circuit-untangle',
  locale: 'zh-CN',
  theme: '数据中心抢修',
  copy: { title: '链路抢修', win: '供电恢复', lose: '抢修超时' },
  levelParameters: { gridSize: 5, moves: 28, targetCount: 4 },
  assets: [{ ref: 'brief://rack-node', license: 'original-required' }],
};

test('compiled candidate content pack normalizes into the runtime contract', async () => {
  const url = new URL('../../../../evidence/cocos-sample-candidate/generated/content-pack.json', import.meta.url);
  const raw = JSON.parse(await readFile(url, 'utf8'));
  assert.deepEqual(normalizeContentPack(raw), content);
});

test('same seed produces exactly the same initial state', () => {
  const first = createGame(content, 20260727);
  const second = createGame(content, 20260727);
  assert.deepEqual(first, second);
});

test('rotating every path tile into its goal orientation wins', () => {
  let state = createGame(content, 7);
  for (const tile of state.tiles) {
    while (state.status === 'playing' && state.tiles[tile.index].rotation !== 0) {
      state = applyAction(state, { type: 'rotate_node', index: tile.index });
    }
  }
  const evaluation = evaluateState(state);
  assert.equal(evaluation.allTargetsConnected, true);
  assert.equal(evaluation.shortCircuit, false);
  assert.equal(state.status, 'won');
  assert.ok(scoreState(state) > 0);
});

test('a mismatched powered connection is not a win', () => {
  let state = createGame(content, 1);
  state = {
    ...state,
    tiles: state.tiles.map((tile) => tile.index === 0 ? { ...tile, rotation: 1 } : { ...tile, rotation: 0 }),
    status: 'playing',
  };
  const evaluation = evaluateState(state);
  assert.equal(evaluation.allTargetsConnected && !evaluation.shortCircuit, false);
});

test('using the last move without solving loses', () => {
  const initial = createGame({ ...content, levelParameters: { ...content.levelParameters, moves: 5 } }, 11);
  const state = { ...initial, movesLeft: 1, status: 'playing' };
  const next = applyAction(state, { type: 'rotate_node', index: 0 });
  assert.equal(next.movesLeft, 0);
  assert.equal(next.status, 'lost');
});

test('content parameters outside kernel bounds are rejected', () => {
  assert.throws(
    () => validateContentPack({ ...content, levelParameters: { ...content.levelParameters, gridSize: 9 } }),
    /gridSize/,
  );
});

test('actions do not mutate prior state', () => {
  const state = createGame(content, 42);
  const snapshot = structuredClone(state);
  applyAction(state, { type: 'request_hint' });
  assert.deepEqual(state, snapshot);
});
