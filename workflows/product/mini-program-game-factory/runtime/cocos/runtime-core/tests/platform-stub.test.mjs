import assert from 'node:assert/strict';
import test from 'node:test';

import { LocalPlatformStub } from '../dist/local-platform-stub.js';

test('local storage round-trips without claiming an official platform', async () => {
  const platform = new LocalPlatformStub('douyin');
  await platform.save('state', '{"level":1}');
  assert.equal(await platform.load('state'), '{"level":1}');
  assert.equal(platform.capabilities().officialSdk, false);
});

test('rewarded ads fail typed and never grant a reward', async () => {
  const platform = new LocalPlatformStub('wechat');
  const result = await platform.showRewardedAd('continue');
  assert.deepEqual(result, {
    ok: false,
    code: 'OFFICIAL_SDK_UNAVAILABLE',
    rewardGranted: false,
    platform: 'wechat',
  });
});

test('login fails typed instead of fabricating an identity', async () => {
  const platform = new LocalPlatformStub('douyin');
  const result = await platform.login();
  assert.equal(result.ok, false);
  assert.equal(result.code, 'OFFICIAL_SDK_UNAVAILABLE');
  assert.equal('userId' in result, false);
});
