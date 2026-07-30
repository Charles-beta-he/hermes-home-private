export type PlatformId = 'wechat' | 'douyin';
export interface PlatformCapabilities {
  platform: PlatformId;
  officialSdk: boolean;
  storage: boolean;
  login: boolean;
  rewardedAds: boolean;
  share: boolean;
}
export type Unavailable = { ok: false; code: 'OFFICIAL_SDK_UNAVAILABLE'; platform: PlatformId };
export type PlatformSdkError = { ok: false; code: 'PLATFORM_SDK_ERROR'; platform: PlatformId };
export type LoginResult =
  | { ok: true; platformLoginCode: string; identityVerified: false }
  | Unavailable
  | PlatformSdkError;
export type RewardedAdResult =
  | { ok: true; rewardGranted: boolean }
  | ((Unavailable | PlatformSdkError) & { rewardGranted: false });
export type ShareResult = { ok: true } | Unavailable | PlatformSdkError;

export interface PlatformPort {
  capabilities(): PlatformCapabilities;
  save(key: string, value: string): Promise<void>;
  load(key: string): Promise<string | null>;
  remove(key: string): Promise<void>;
  login(): Promise<LoginResult>;
  showRewardedAd(placement: string): Promise<RewardedAdResult>;
  share(payload: { title: string; imageUrl?: string }): Promise<ShareResult>;
}
