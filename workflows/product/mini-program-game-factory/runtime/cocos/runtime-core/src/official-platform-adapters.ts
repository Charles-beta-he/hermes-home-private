import {
  LoginResult,
  PlatformCapabilities,
  PlatformId,
  PlatformPort,
  RewardedAdResult,
  ShareResult,
} from './platform-port.js';

interface LoginResponse {
  code?: string;
}

interface RewardedVideoAd {
  onClose(handler: (result: { isEnded?: boolean }) => void): void;
  offClose(handler: (result: { isEnded?: boolean }) => void): void;
  onError(handler: (error: unknown) => void): void;
  offError(handler: (error: unknown) => void): void;
  load(): Promise<void>;
  show(): Promise<void>;
}

export interface MiniGameSdk {
  setStorageSync(key: string, value: string): void;
  getStorageSync(key: string): unknown;
  removeStorageSync(key: string): void;
  login(options: {
    success(result: LoginResponse): void;
    fail(error: unknown): void;
  }): void;
  shareAppMessage(payload: { title: string; imageUrl?: string }): void;
  createRewardedVideoAd(options: { adUnitId: string }): RewardedVideoAd;
}

abstract class OfficialMiniGamePlatformAdapter implements PlatformPort {
  protected constructor(
    private readonly platform: PlatformId,
    private readonly sdk: MiniGameSdk,
  ) {}

  public capabilities(): PlatformCapabilities {
    return {
      platform: this.platform,
      officialSdk: true,
      storage: true,
      login: true,
      rewardedAds: true,
      share: true,
    };
  }

  public async save(key: string, value: string): Promise<void> {
    this.sdk.setStorageSync(key, value);
  }

  public async load(key: string): Promise<string | null> {
    const value = this.sdk.getStorageSync(key);
    return typeof value === 'string' ? value : null;
  }

  public async remove(key: string): Promise<void> {
    this.sdk.removeStorageSync(key);
  }

  public async login(): Promise<LoginResult> {
    return new Promise((resolve) => {
      try {
        this.sdk.login({
          success: (result) => {
            if (typeof result.code !== 'string' || result.code.length === 0) {
              resolve({ ok: false, code: 'PLATFORM_SDK_ERROR', platform: this.platform });
              return;
            }
            resolve({
              ok: true,
              platformLoginCode: result.code,
              identityVerified: false,
            });
          },
          fail: () => resolve({ ok: false, code: 'PLATFORM_SDK_ERROR', platform: this.platform }),
        });
      } catch {
        resolve({ ok: false, code: 'PLATFORM_SDK_ERROR', platform: this.platform });
      }
    });
  }

  public async share(payload: { title: string; imageUrl?: string }): Promise<ShareResult> {
    try {
      this.sdk.shareAppMessage(payload);
      return { ok: true };
    } catch {
      return { ok: false, code: 'PLATFORM_SDK_ERROR', platform: this.platform };
    }
  }

  public async showRewardedAd(placement: string): Promise<RewardedAdResult> {
    const sdkError = (): RewardedAdResult => ({
      ok: false,
      code: 'PLATFORM_SDK_ERROR',
      rewardGranted: false,
      platform: this.platform,
    });
    let ad: RewardedVideoAd;
    try {
      const candidate = this.sdk.createRewardedVideoAd({ adUnitId: placement }) as unknown;
      const methods = ['onClose', 'offClose', 'onError', 'offError', 'load', 'show'] as const;
      if (
        typeof candidate !== 'object'
        || candidate === null
        || methods.some((method) => typeof (candidate as Record<string, unknown>)[method] !== 'function')
      ) {
        return sdkError();
      }
      ad = candidate as RewardedVideoAd;
    } catch {
      return sdkError();
    }
    return new Promise((resolve) => {
      let settled = false;
      const cleanup = (): void => {
        try { ad.offClose(onClose); } catch { /* cleanup must not suppress the receipt */ }
        try { ad.offError(onError); } catch { /* cleanup must not suppress the receipt */ }
      };
      const settle = (result: RewardedAdResult): void => {
        if (settled) return;
        settled = true;
        cleanup();
        resolve(result);
      };
      const onClose = (result: { isEnded?: boolean }): void => {
        settle({ ok: true, rewardGranted: result.isEnded === true });
      };
      const onError = (): void => {
        settle(sdkError());
      };
      try {
        ad.onClose(onClose);
        ad.onError(onError);
        void ad.load().then(() => ad.show()).catch(onError);
      } catch {
        onError();
      }
    });
  }
}

export class WechatPlatformAdapter extends OfficialMiniGamePlatformAdapter {
  public constructor(sdk: unknown) {
    super('wechat', requireSdk(sdk, 'wx'));
  }
}

export class DouyinPlatformAdapter extends OfficialMiniGamePlatformAdapter {
  public constructor(sdk: unknown) {
    super('douyin', requireSdk(sdk, 'tt'));
  }
}

interface MiniGameRuntimeGlobals {
  wx?: unknown;
  tt?: unknown;
}

const REQUIRED_SDK_METHODS = [
  'setStorageSync',
  'getStorageSync',
  'removeStorageSync',
  'login',
  'shareAppMessage',
  'createRewardedVideoAd',
] as const;

function requireSdk(sdk: unknown, globalName: 'wx' | 'tt'): MiniGameSdk {
  if (sdk === undefined || sdk === null) {
    throw new Error(`${globalName} official SDK unavailable`);
  }
  if (
    typeof sdk !== 'object'
    || REQUIRED_SDK_METHODS.some((method) => typeof (sdk as Record<string, unknown>)[method] !== 'function')
  ) {
    throw new Error(`${globalName} official SDK invalid`);
  }
  return sdk as MiniGameSdk;
}

export function createWechatPlatformAdapterFromGlobal(
  globals: MiniGameRuntimeGlobals = globalThis as MiniGameRuntimeGlobals,
): WechatPlatformAdapter {
  return new WechatPlatformAdapter(requireSdk(globals.wx, 'wx'));
}

export function createDouyinPlatformAdapterFromGlobal(
  globals: MiniGameRuntimeGlobals = globalThis as MiniGameRuntimeGlobals,
): DouyinPlatformAdapter {
  return new DouyinPlatformAdapter(requireSdk(globals.tt, 'tt'));
}
