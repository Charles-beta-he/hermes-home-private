import {
  LoginResult,
  PlatformCapabilities,
  PlatformId,
  PlatformPort,
  RewardedAdResult,
  ShareResult,
} from './platform-port.js';

export class LocalPlatformStub implements PlatformPort {
  private readonly storage = new Map<string, string>();

  public constructor(private readonly platform: PlatformId) {}

  public capabilities(): PlatformCapabilities {
    return {
      platform: this.platform,
      officialSdk: false,
      storage: true,
      login: false,
      rewardedAds: false,
      share: false,
    };
  }

  public async save(key: string, value: string): Promise<void> {
    this.storage.set(key, value);
  }

  public async load(key: string): Promise<string | null> {
    return this.storage.get(key) ?? null;
  }

  public async remove(key: string): Promise<void> {
    this.storage.delete(key);
  }

  public async login(): Promise<LoginResult> {
    return { ok: false, code: 'OFFICIAL_SDK_UNAVAILABLE', platform: this.platform };
  }

  public async showRewardedAd(_placement: string): Promise<RewardedAdResult> {
    return {
      ok: false,
      code: 'OFFICIAL_SDK_UNAVAILABLE',
      rewardGranted: false,
      platform: this.platform,
    };
  }

  public async share(_payload: { title: string; imageUrl?: string }): Promise<ShareResult> {
    return { ok: false, code: 'OFFICIAL_SDK_UNAVAILABLE', platform: this.platform };
  }
}
