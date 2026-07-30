import assert from 'node:assert/strict';
import test from 'node:test';

import {
  createDouyinPlatformAdapterFromGlobal,
  createWechatPlatformAdapterFromGlobal,
  DouyinPlatformAdapter,
  WechatPlatformAdapter,
} from '../dist/official-platform-adapters.js';

function fakeSdk({ isEnded = true, cleanupThrows = false } = {}) {
  const storage = new Map();
  const calls = [];
  return {
    calls,
    sdk: {
      setStorageSync(key, value) { calls.push(['setStorageSync', key, value]); storage.set(key, value); },
      getStorageSync(key) { calls.push(['getStorageSync', key]); return storage.get(key); },
      removeStorageSync(key) { calls.push(['removeStorageSync', key]); storage.delete(key); },
      login({ success }) { calls.push(['login']); success({ code: 'one-time-login-code' }); },
      shareAppMessage(payload) { calls.push(['shareAppMessage', payload]); },
      createRewardedVideoAd({ adUnitId }) {
        calls.push(['createRewardedVideoAd', adUnitId]);
        let close;
        let error;
        return {
          onClose(handler) { close = handler; },
          offClose(handler) { if (cleanupThrows) throw new Error('offClose failed'); if (close === handler) close = undefined; },
          onError(handler) { error = handler; },
          offError(handler) { if (cleanupThrows) throw new Error('offError failed'); if (error === handler) error = undefined; },
          async load() { calls.push(['load']); },
          async show() { calls.push(['show']); close({ isEnded }); },
        };
      },
    },
  };
}

test('wechat and douyin factories bind only their exact official runtime globals', () => {
  const wechat = fakeSdk();
  const douyin = fakeSdk();
  assert.equal(createWechatPlatformAdapterFromGlobal({ wx: wechat.sdk }).capabilities().platform, 'wechat');
  assert.equal(createDouyinPlatformAdapterFromGlobal({ tt: douyin.sdk }).capabilities().platform, 'douyin');
  assert.throws(() => createWechatPlatformAdapterFromGlobal({ tt: douyin.sdk }), /wx official SDK unavailable/);
  assert.throws(() => createDouyinPlatformAdapterFromGlobal({ wx: wechat.sdk }), /tt official SDK unavailable/);
  assert.throws(() => createWechatPlatformAdapterFromGlobal({ wx: {} }), /wx official SDK invalid/);
  assert.throws(() => createDouyinPlatformAdapterFromGlobal({ tt: {} }), /tt official SDK invalid/);
});

test('direct official adapter construction rejects malformed SDK objects', () => {
  assert.throws(() => new WechatPlatformAdapter({}), /wx official SDK invalid/);
  assert.throws(() => new DouyinPlatformAdapter({}), /tt official SDK invalid/);
});

test('wechat adapter invokes injected official SDK storage without owning gameplay state', async () => {
  const { sdk, calls } = fakeSdk();
  const platform = new WechatPlatformAdapter(sdk);
  await platform.save('state', '{"level":1}');
  assert.equal(await platform.load('state'), '{"level":1}');
  await platform.remove('state');
  assert.equal(await platform.load('state'), null);
  assert.deepEqual(calls.slice(0, 4).map(([name]) => name), [
    'setStorageSync', 'getStorageSync', 'removeStorageSync', 'getStorageSync',
  ]);
  assert.equal(platform.capabilities().officialSdk, true);
});

test('official login returns only a one-time platform code and never fabricates user identity', async () => {
  const { sdk } = fakeSdk();
  const result = await new DouyinPlatformAdapter(sdk).login();
  assert.deepEqual(result, {
    ok: true,
    platformLoginCode: 'one-time-login-code',
    identityVerified: false,
  });
  assert.equal('userId' in result, false);
});

test('synchronous official SDK failures return typed errors without granting identity or reward', async () => {
  const loginFixture = fakeSdk();
  loginFixture.sdk.login = () => { throw new Error('sdk login failed'); };
  assert.deepEqual(await new WechatPlatformAdapter(loginFixture.sdk).login(), {
    ok: false, code: 'PLATFORM_SDK_ERROR', platform: 'wechat',
  });

  const adFixture = fakeSdk();
  adFixture.sdk.createRewardedVideoAd = () => { throw new Error('sdk ad failed'); };
  assert.deepEqual(await new DouyinPlatformAdapter(adFixture.sdk).showRewardedAd('ad-unit-test'), {
    ok: false, code: 'PLATFORM_SDK_ERROR', rewardGranted: false, platform: 'douyin',
  });

  const malformedAdFixture = fakeSdk();
  malformedAdFixture.sdk.createRewardedVideoAd = () => ({});
  assert.deepEqual(await new WechatPlatformAdapter(malformedAdFixture.sdk).showRewardedAd('ad-unit-test'), {
    ok: false, code: 'PLATFORM_SDK_ERROR', rewardGranted: false, platform: 'wechat',
  });
});

test('official share dispatches through the platform SDK', async () => {
  const { sdk, calls } = fakeSdk();
  const result = await new WechatPlatformAdapter(sdk).share({ title: 'Circuit', imageUrl: 'https://example.invalid/card.png' });
  assert.deepEqual(result, { ok: true });
  assert.deepEqual(calls.at(-1), ['shareAppMessage', {
    title: 'Circuit', imageUrl: 'https://example.invalid/card.png',
  }]);
});

test('reward is granted only after the official rewarded-video close receipt says isEnded true', async () => {
  const { sdk, calls } = fakeSdk();
  const result = await new DouyinPlatformAdapter(sdk).showRewardedAd('ad-unit-test');
  assert.deepEqual(result, { ok: true, rewardGranted: true });
  assert.deepEqual(calls.slice(-3), [
    ['createRewardedVideoAd', 'ad-unit-test'], ['load'], ['show'],
  ]);

  const incomplete = fakeSdk({ isEnded: false });
  assert.deepEqual(await new WechatPlatformAdapter(incomplete.sdk).showRewardedAd('ad-unit-test'), {
    ok: true,
    rewardGranted: false,
  });

  const cleanupFailure = fakeSdk({ cleanupThrows: true });
  assert.deepEqual(await new DouyinPlatformAdapter(cleanupFailure.sdk).showRewardedAd('ad-unit-test'), {
    ok: true,
    rewardGranted: true,
  });
});
