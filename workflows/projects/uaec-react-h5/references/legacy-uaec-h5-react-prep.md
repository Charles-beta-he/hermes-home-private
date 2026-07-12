# UAEC React H5 开发准备包

生成时间: 2026-07-09
目标: 开始开发 `/Users/charles/Desktop/folder/work/uaec-react-h5`；业务逻辑优先对齐 `/Users/charles/Desktop/folder/work/uaec-android`；进度对齐 UAEC H5 15 条任务清单。

## 1. 当前证据

- React H5 repo: `/Users/charles/Desktop/folder/work/uaec-react-h5`
  - branch: `main`
  - last commit: `9a76f12 feat: 修改配置`
  - `git status --short`: clean before/after build
  - `pnpm -s build`: PASS，Vite 6.3.6，12669 modules transformed，PWA generated；存在 chunk > 500k 与 Browserslist 数据过期 warning。
- Android 参考 repo: `/Users/charles/Desktop/folder/work/uaec-android`
  - branch: `global`
  - last commit: `37afd65e Revert "fix(strings): 链上转出扫一扫相机权限弹窗文案按品牌指引修复 (t104285)"`
  - working tree: `?? .hermes.md`，不要纳入业务改动。
- H5 进度基线: `/Users/charles/.hermes/workflows/projects/uaec-h5/tasks/v1.2.0-h5-tasks-15.inventory.md`
  - 总数 15：P0 1，P1 9，P2 5。
  - 旧 26 条 inventory 已标 SUPERSEDED，只作扩展参考，当前主进度以 15 条为准。

## 2. React H5 架构落点

- 技术栈: React 18 + TypeScript + Vite + MUI + Zustand + React Router + PWA。
- 路由总入口: `src/router/router.tsx`
  - 动态加载 `src/router/modules/*.route.tsx`。
  - auth 走 `PrivateRoute` / `AuthRoute`，高级/实名认证可通过 route meta 控制。
- 底部主导航: `src/config/tabBar.ts`
  - 首页 `/`
  - 行情 `/market`
  - 交易 `/trade`
  - 合约 `/contract`
  - 资产 `/asset`
- 页面目录: `src/pages/*`
  - 已有首页、行情、现货交易、合约、资产、消息、扫码、邀请、KYC、理财、客服、公告等页面。
- API 层: `src/api/*Api.ts` + `src/api/apiClient.ts`
  - 已拆成 common/user/asset/spot/contract/personal/home/message/kyc/finance/cms 等模块。
  - 共扫描到约 213 个 endpoint 引用。
- Service 层: `src/services/*Service.ts`
  - 页面一般通过 service 包装 API，开发优先复用 service，不直接散落 axios。
- 状态: `src/store/authStore.ts`
  - token/user、refreshUser、logout、认证状态类型守卫。
- WebSocket: `src/WebSocketLayer/*`
  - 已有管理器、实例、fallback/merge 策略，但存在 TODO/console 调试点。

## 3. Android 对齐锚点

- API/域名权威入口: `uaec-android/app/src/main/java/com/uu/market/UrlContent.java`
  - `BASE_URL = https://{BASE_DOMAIN}/v1/rest/app/`
  - debug domain `test.uaec.cc`，release domain `app.uaec.net`
  - WS: market/asset/userdata/contract/ims/option 等常量集中在同文件。
- Android 网络封装: `uaec-android/app/src/main/java/com/uu/market/network/OkHttp.java`
  - 自动签名、公共 headers、meta.success/meta.code 业务错误处理、401 登录处理、证书 pinning/retry/cookie。
- 业务域参考目录:
  - 首页/个人中心: `home`, `mine`
  - 行情/K线: `market`, `kline`
  - 现货: `bbtrade`
  - 合约: `contract`
  - 资产: `property`, `assets`
  - C2C/法币: `legalTender`
  - KYC: `kycmanage`
- 认证状态对齐点:
  - Android 多处使用 `advancedAuth` 值 `pass / notPass / waitVeritfy`。
  - React H5 `authStore.ts` 也已使用 `realNameAuth: y/n` 与 `advancedAuth: pass/notPass/waitVeritfy`，后续不要改状态机名。

## 4. 15 条任务映射到 React H5 落点

### P0

1. Banner 外部跳转 RWA/活动详情带 token
   - 任务: `fb3406dd-8c4a-40d4-b37a-a52601d15e05`
   - React 落点: `src/pages/HomePage/*`, `src/services/homeService.ts`, `src/api/homeApi.ts`, 可能涉及公告/RWA/IEO 跳转工具。
   - Android 对齐: `UrlContent.java` webview/RWA/IEO URL 拼接方式、token/language/baseURL 传参模式。
   - 验收: 自有域名外链才追加 token；第三方外链禁止泄露 token；内部跳转不再错误拼成公告详情。

### P1

2. 首页右上角通知中心 + 扫码登录
   - React 已有: `/message`, `/scan`, `src/pages/MessagePage/*`, `src/pages/ScanPage/*`, `QRCodeScanner`。
   - 落点: 首页顶部入口 + 通知中心分类/扫码登录协议。
   - Android 对齐: 系统消息、扫码登录/WebView/二维码相关页面。

3. 新增/修正移动端一致行情页
   - React 已有: `/market`, `src/pages/MarketCenterPage/*`, `src/api/spotApi.ts` 中 `moveHomeMarket`, `tradeType/newForumList`。
   - Android 对齐: `market`, `kline`, `UrlContent.AREA_LIST`, `market/moveHomeMarket`。
   - 验收: 自选/全部/主板区/RWA区；分区由后台配置，可增减；进入不报系统异常。

4. 邀请注册输入账号页 logo 禁止跳 PC 首页
   - React 落点: `src/pages/RegisterPage/*`, `src/pages/InvitePage/*`。
   - 验收: 邀请链路中下一步到输入账号页后点击 logo 无跳转、无 PC 首页报错；普通注册流程不被误伤。

5. 合约右上角计算器
   - React 已有: `/contract`, `src/pages/ContractPage/ContractPage.tsx`。
   - Android 对齐: `contract/ContractCalculatorActivity.java`, `CalculateActivity.java`, 合约计算相关类。
   - 验收: 公式/字段/词汇与 Android/PC 对齐，需补 i18n。

6. 合约右上角资金费率 + 市场总览
   - React API 已有: `contract/entrust/FundRate/fundBill`, `contract/market/getTradeTypeTicker`, `contract/market/getTradeTypeList`。
   - Android 对齐: `FundingRateActivity`, `FRRateFragment`, `FRComparedFragment`, `SustainableMarketActivity`。

7. 现货右上角预警设置
   - React 落点: `src/pages/TradingPage/*`, `src/services/spotService.ts`, `src/api/spotApi.ts`。
   - Android 对齐: `bbtrade/TradingFragment.java` 与相关弹窗/预警接口；当前需继续反查 Android 具体 alert endpoint。
   - 验收: 新增/查看/单条删除/全部删除/空状态/异常状态。

8. H5 同步合伙人功能，入口放金刚区
   - React 落点: `src/pages/HomePage/*`, 可能新增 Partner 页面/路由/API。
   - Android 参考: `property/partner/*`, `mine/invitegif/*`。
   - 依赖: 后端接口需确认；没有接口前先做入口/壳会有伪完成风险。

9. 设置内折算货币/语言/涨跌偏好/模式/版本号
   - React 已有: `personalApi.sysconfig/new`, `personalApi.lan/selectList`, `commonService.getExchangeRate`, locales 多语言目录。
   - 落点: `src/pages/HomePage/SecurityDetailPage.tsx` 及 settings config 生成器，必要时抽独立 Settings 页面。
   - Android 对齐: `mine` 设置页、语言/涨跌/主题/版本逻辑。

### P2

10. 全局字体重新定义
   - 落点: `src/styles/globals.css`, `src/theme.ts`, Tailwind/MUI theme。
   - 依赖: 老向/设计提供字体文件或 font-family，不可猜。

11. 首页字体权重
   - 落点: `src/pages/HomePage/*`, 全局 typography token。
   - 验收: 一级 Bold、二级 Regular、三级 Light。

12. 首页 list 间距/涨跌幅块/价格右对齐
   - 落点: 首页行情列表组件；需按 Figma 新版首页截图 diff。

13. 资产页面顶部/小眼睛/涨跌箭头/充值突出
   - 落点: `src/pages/AssetPage/*`, `src/pages/AssetPage/components/*`。
   - Android 对齐: `property`, `assets` 相关页面。

14. 选择币种列表间距/分割线
   - 落点: 币种搜索/选择组件：`CoinSearchPage`, `SearchTradingPairsPage`, 资产充值/提现/划转入口。

15. PWA logo/缓存更新问题
   - 落点: `vite.config.ts`, `public/*`, PWA manifest/sw 生成策略。
   - 当前 build 证据: PWA generateSW 正常生成 `dist/sw.js`；但需要手机/PWA 安装态验收旧 icon 刷新。

## 5. 推荐执行批次

Batch A：低耦合快速降风险
1. 邀请注册 logo 禁跳。
2. Banner/RWA token 跳转表与自有域名 token 附加。
3. PWA 缓存策略诊断，先加版本/更新提示/manifest 图标校验，不盲目强刷用户会话。

Batch B：已具备路由/API 基础的功能补齐
4. 首页通知/扫码入口接入现有 `/message` 和 `/scan`，再补扫码登录协议。
5. 行情页分区配置与进入异常。
6. 资产/币种选择视觉统一。

Batch C：交易核心能力
7. 现货预警设置：先反查 Android endpoint 与 PC/H5 现有接口。
8. 合约资金费率/市场总览。
9. 合约计算器公式 + 页面。

Batch D：依赖接口/设计资源
10. 合伙人功能。
11. 设置全局偏好。
12. 全局字体/首页视觉 1:1。

## 6. 开发红线

- 不从 Android 复制状态机名字后再改名；H5 已有 `realNameAuth` / `advancedAuth` / `paypasswordSet` 类型守卫，沿用。
- 金额、手续费、仓位、价格字段不要用 `Number/toFixed/floor` 做精度决策；保留接口 decimal string，展示层 string truncate/pad。
- token 只允许传 UAEC 自有域名目标；第三方外链不追加。
- Android 是业务逻辑参考，不是直接 UI 真相；UI 以 Figma/任务截图/React 当前交互为验收源。
- 每条任务关闭前至少要有：代码 diff + build/test + 对应页面截图/浏览器读回；PWA/扫码/相机类需要真机或浏览器权限证据。

## 7. 立即可开工的下一步

- 从 Batch A 的“邀请注册 logo 禁跳”开始，风险最低、依赖最少。
- 同时为 Banner/RWA 建跳转判定表：内部公告、内部 RWA、外部 UAEC 自有域、第三方外链、未登录态。
- 对现货预警/合约计算器先跑 Android endpoint 反查，不直接凭 UI 猜接口。
