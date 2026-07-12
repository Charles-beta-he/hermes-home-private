# Scoped reference: 中国本地生活、社媒旅游与无人机官方 API 核验

> **Scope / applicability:** 仅用于研究中国大陆本地餐饮、POI、社媒旅游内容及民用无人机官方数字服务的 API 合法性与准入边界。这里的 URL 和平台事实是截至核验时的证据索引，每次使用必须重新打开官方页面确认现状。
>
> **Anti-conditions:** 不推广为全球 API 调研规则；不把本文中的“未核实到”固化成永久不存在；不将平台事实复制进通用 SKILL.md；不把搜索摘要、爬虫、App 抓包、签名逆向或私有 JSON 端点当作合法公开 API。

## 可复用核验程序

1. 只接受平台官方域名、官方开发者文档、政府/监管机构网站和正式法规。
2. 区分：文档可浏览、普通开发者可自助取得 Key、特定企业/行业/城市/合作方经审批取得权限。文档公开不等于数据权限公开。
3. 逐平台记录主体、认证、应用审核、OAuth/特殊 scope、授权城市/字段、配额及缓存展示限制。
4. 出现 `appkey/appsecret/session`、特殊权限、授权城市、线下沟通或商务合作，应判为审批/合作制，而非普通公共 API。
5. 无普通开发者准入证据时写“未在官方来源核实到”，不得写成绝对不存在。

## 官方证据索引与当时边界

### 高德 POI
- 平台：https://lbs.amap.com/
- 获取 Key：https://lbs.amap.com/api/webservice/guide/create-project/get-key
- POI 2.0：https://lbs.amap.com/api/webservice/guide/api-advanced/newpoisearch
- 可注册、创建应用并申请 Web 服务 Key；提供关键词、周边、多边形、ID 搜索。高级能力、商业使用、配额和许可应现场复核；不是全量数据库导出。

### 美团/大众点评
- 技术服务合作中心：https://developer.meituan.com/docs
- 生态开放平台：https://openapi.meituan.com/
- 点评 POI 导航：https://poiopen.dianping.com/instructions/guide.html
- POI 搜索：https://poiopen.dianping.com/instructions/doc/poisearch.html
- POI 数据：https://poiopen.dianping.com/instructions/doc/poi.html
- UGC：https://poiopen.dianping.com/instructions/doc/ugc.html
- 菜品：https://poiopen.dianping.com/instructions/doc/dish.html
- 实时数据：https://poiopen.dianping.com/instructions/doc/coop.html
- 文档显示签名、授权城市、字段申请和线下沟通等合作方特征。潜在字段含 POI、地址坐标、营业信息、评论、图片、推荐菜；实际范围必须以正式授权为准。

### 小红书
- 开放平台：https://open.xiaohongshu.com/
- 开发者文档：https://open.xiaohongshu.com/document/developer/file/42
- API 文档：https://open.xiaohongshu.com/document/api
- 公开能力主要偏商家、电商、商品、订单、库存、物流、售后。核验时未找到普通开发者自助使用的全站笔记/旅游内容搜索、评论读取或博主历史内容 API。

### 抖音
- 开放平台：https://developer.open-douyin.com/
- OpenAPI 列表：https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/list
- POI 查询：https://developer.open-douyin.com/docs/resource/zh-CN/dop/develop/openapi/video-management/douyin/search-video/video-poi
- `poi.search` 为特殊权限；官方当时说明定向媒体行业第三方，其他行业可申请。获批后可返回 POI ID、名称、行政区、地址、坐标等。其他内容能力分别受 OAuth、应用类型和业务准入约束。

### 无人机空域/UOM
- UOM：https://uom.caac.gov.cn/
- 《无人驾驶航空器飞行管理暂行条例》：https://www.gov.cn/zhengce/content/202306/content_6888799.htm
- 官方服务面向实名登记、资质、运营和飞行活动监管。核验时未找到普通开发者可申请 Key 的全国实时空域 API；管制空域还可能由地方政府公布或临时增加，产品不能仅凭静态地图或厂商围栏断言合法可飞。

## 输出检查表
- 官方结论：自助公开 / 审批制 / 商务合作 / 未核实到；
- 官方 URL；主体与认证；scope/OAuth/城市/字段/配额；可返回数据；产品建议；
- 明示爬虫、抓包、逆向、Cookie 模拟、验证码或风控绕过不等于合法 API。