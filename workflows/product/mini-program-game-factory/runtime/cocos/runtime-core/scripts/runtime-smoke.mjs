import { createHash } from 'node:crypto';
import { readFile } from 'node:fs/promises';

import { normalizeContentPack } from '../dist/content-pack.js';
import { applyAction, createGame, evaluateState, scoreState } from '../dist/gameplay-kernel.js';
import { LocalPlatformStub } from '../dist/local-platform-stub.js';

const contentUrl = new URL('../../../../evidence/cocos-sample-candidate/generated/content-pack.json', import.meta.url);
const content = normalizeContentPack(JSON.parse(await readFile(contentUrl, 'utf8')));
let state = createGame(content, 20260727);
let actionCount = 0;
for (const tile of state.tiles) {
  while (state.status === 'playing' && state.tiles[tile.index].rotation !== 0) {
    state = applyAction(state, { type: 'rotate_node', index: tile.index });
    actionCount += 1;
  }
}
const evaluation = evaluateState(state);
const platform = new LocalPlatformStub('douyin');
const ad = await platform.showRewardedAd('continue');
const stateDigest = createHash('sha256').update(JSON.stringify(state)).digest('hex');
const receipt = {
  closure_state: 'node_runtime_smoke_passed',
  runtime: { name: 'node', version: process.version, executable: process.execPath },
  content_id: content.contentId,
  kernel_id: state.kernelId,
  seed: state.seed,
  action_count: actionCount,
  final_status: state.status,
  score: scoreState(state),
  all_targets_connected: evaluation.allTargetsConnected,
  short_circuit: evaluation.shortCircuit,
  platform_stub: {
    platform: 'douyin',
    official_sdk: platform.capabilities().officialSdk,
    rewarded_ad_result: ad,
  },
  state_sha256: stateDigest,
  authority: { creator_runtime_verified: false, platform_sdk_verified: false, may_publish: false },
};
if (state.status !== 'won' || !evaluation.allTargetsConnected || evaluation.shortCircuit || ad.ok) {
  throw new Error(`runtime smoke failed: ${JSON.stringify(receipt)}`);
}
console.log(JSON.stringify(receipt, null, 2));
