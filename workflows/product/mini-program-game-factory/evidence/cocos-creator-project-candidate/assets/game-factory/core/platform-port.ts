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
export type LoginResult = { ok: true; userId: string } | Unavailable;
export type RewardedAdResult = { ok: true; rewardGranted: boolean } | (Unavailable & { rewardGranted: false });
export type ShareResult = { ok: true } | Unavailable;

export interface PlatformPort {
  capabilities(): PlatformCapabilities;
  save(key: string, value: string): Promise<void>;
  load(key: string): Promise<string | null>;
  remove(key: string): Promise<void>;
  login(): Promise<LoginResult>;
  showRewardedAd(placement: string): Promise<RewardedAdResult>;
  share(payload: { title: string; imageUrl?: string }): Promise<ShareResult>;
}
