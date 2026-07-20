# uaec-android 全模块对齐计划

**日期**: 2026-07-16
**目标**: 100% 对齐 uaec-android 所有已有模块

---

## 模块对齐状态

| 模块 | Android 行数 | H5 行数 | 对齐度 | 优先级 |
|------|-------------|---------|--------|--------|
| home (首页) | 9,182 | 2,756 | 30% | P1 |
| market (行情) | 5,729 | 2,010 | 35% | P1 |
| bbtrade (现货交易) | 9,662 | 3,171 | 33% | P1 |
| contract (合约交易) | 37,083 | 5,901 | 16% | P0 |
| assets (资产) | 8,293 | 4,686 | 57% | P1 |
| legalTender (C2C) | 14,525 | 824 | 6% | P0 |
| mine (个人中心) | 19,552 | ~1,000 | 5% | P0 |
| login (登录) | 3,671 | 518 | 14% | P1 |
| property (理财) | 29,255 | 351 | 1% | P0 |

---

## 对齐目标 (按模块)

### 1. contract (合约交易) — P0
Android: 91 files, 37,083 lines
H5: 14 files, 5,901 lines

缺失功能:
- [ ] 合约快速交易模式 (ContractFastFragment 3,703行)
- [ ] K线全屏模式 (KlineFuturesFragment 2,654行)
- [ ] 合约K线Activity (UsdtKlineActivity 2,520行)
- [ ] 合约买入Activity (FuturesBuyActivity 2,139行)
- [ ] 持仓列表Fragment (PositionListFragment 970行)
- [ ] 买入合约Fragment (BuyFuturesFragment 865行)
- [ ] 持仓Fragment (FuturesPositionFragment 855行)
- [ ] 深度Fragment (USDTDepthFragment 803行)
- [ ] 资金流水Fragment (EntrustCapitalFlowFragment 667行)
- [ ] 资金费用Fragment (FundsCostFragment 583行)

### 2. legalTender (C2C) — P0
Android: 27 files, 14,525 lines
H5: 6 files, 824 lines

缺失功能:
- [ ] 一键买币 (OneKeyBuyCoin 1,509行)
- [ ] 商家信息 (BusinessInfoActivity 1,318行)
- [ ] 商家发布挂单 (OTCBuyReleaseOrderFragment 961行)
- [ ] 聊天列表 (ChatListActivity 545行)
- [ ] 订单票据 (OrderTicketFragment 464行)
- [ ] 币种选择 (CurrencyActivity 281行)
- [ ] 筛选对话框 (DialogFiltrateFragment 325行)
- [ ] 商家关注/取关 (OtcFollow/Unfollow 787行)
- [ ] 快捷买卖区 (ExpressAreaFragment 237行)
- [ ] 订单列表Fragment (OrderFragment 622行)

### 3. mine (个人中心) — P0
Android: 70 files, 19,552 lines
H5: ~1,000 lines (UserProfile + SecurityCenter)

缺失功能:
- [ ] 实名认证 (AuthenticationActivity 1,101行)
- [ ] 安全中心完整 (SecurityCentreActivity 869行)
- [ ] 个人中心主页 (MineActivity 809行)
- [ ] 设置页完整 (SettingActivity 713行)
- [ ] 手势密码 (ChaosGestureView 702行)
- [ ] 上传身份证 (UploadIdentityActivity 702行)
- [ ] 反馈 (FeedbackActivity 647行)
- [ ] 支付宝设置 (SettingAliPayActivity 480行)
- [ ] 邀请分享 (DialogShareFragment 469行)
- [ ] 收款方式 (GatheringStyleActivity 454行)
- [ ] 上传护照 (UploadPassportActivity 452行)
- [ ] 广告管理 (AdvertisingManagementFragment 450行)
- [ ] 指纹验证 (VerifyFingerActivity 414行)
- [ ] 邀请好友 (InviteFragment 376行)
- [ ] 重置交易密码 (ResetDealPassWordActivity 366行)

### 4. property (理财) — P0
Android: 93 files, 29,255 lines
H5: 4 files, 351 lines

缺失功能:
- [ ] 新资产账单 (NewAssetBillActivity 939行)
- [ ] 高频交易 (HighFrequencyActivity 871行)
- [ ] 合伙人 (PartnerActivity 764行)
- [ ] 投票列表 (VoteForListActivity 758行)
- [ ] 提币 (MentionMoneyActivity 737行)
- [ ] 合伙人等级 (PartnerLevelActivity 711行)
- [ ] 小额兑换 (SmallExchangeActivity 616行)
- [ ] 资产记录 (AssetsRecordFragment 586行)
- [ ] 理财收益 (NewFinancesActivity 572行)
- [ ] 持仓列表 (SustainableListActivity 543行)
- [ ] 划转记录 (TransferRecordActivity 538行)
- [ ] 我的投票 (MyVoteActivity 532行)
- [ ] 充值收益 (DepositIncomeFragment 528行)

### 5. home (首页) — P1
Android: 34 files, 9,182 lines
H5: 21 files, 2,756 lines

缺失功能:
- [ ] 首页市场Fragment (HomeMarketFragment 423行)
- [ ] 首页市场新版 (HomeMarketNewFragment 408行)
- [ ] 排行榜Fragment (RankListFragment1 64行)
- [ ] 功能Activity (HomeFunctionActivity 52行)
- [ ] 社区加入 (JoinCommunityActivity 31行)
- [ ] 行动中心 (ActionCenterActivity 43行)

### 6. market (行情) — P1
Android: 11 files, 5,729 lines
H5: 5 files, 2,010 lines

缺失功能:
- [ ] 推荐Fragment (RecommendFragment)
- [ ] 选区Fragment (SelectFragment)
- [ ] 板块Fragment (PlateFragment)
- [ ] 搜索Activity (SearchActivity)
- [ ] 批量操作 (MassOperationActivity)

### 7. bbtrade (现货交易) — P1
Android: 15 files, 9,662 lines
H5: 6 files, 3,171 lines

缺失功能:
- [ ] 交易容器Fragment (SpotTradeContainerFragment)
- [ ] 持仓Fragment (SpotPositionFragment)
- [ ] 历史订单Fragment (OrderHistoryFragment)
- [ ] 订单详情Activity (TradeOrderDetailsActivity)
- [ ] 预警设置 (BBWarnSettingActivity)
- [ ] 对手Fragment (AgainstFragment)

### 8. login (登录) — P1
Android: 16 files, 3,671 lines
H5: 2 files, 518 lines

缺失功能:
- [ ] 忘记密码流程
- [ ] 注册流程完整
- [ ] 验证码组件
- [ ] 生物识别登录

### 9. assets (资产) — P1
Android: 20 files, 8,293 lines
H5: 14 files, 4,686 lines

缺失功能:
- [ ] 快速合约Fragment (FastContractFragment)
- [ ] C2C资产Fragment (C2CCurrencyAssetsFragment)
- [ ] 期权资产Fragment (OptionsAssetsFragment)
- [ ] 奖励资产Fragment (AwardAssetsFragment)

---

## 执行计划

Phase 1 (P0): 合约 + C2C + 个人中心 + 理财
Phase 2 (P1): 首页 + 行情 + 现货 + 登录 + 资产

每个模块按 Android 源码结构拆分为子任务，逐个实现 + 验证。
