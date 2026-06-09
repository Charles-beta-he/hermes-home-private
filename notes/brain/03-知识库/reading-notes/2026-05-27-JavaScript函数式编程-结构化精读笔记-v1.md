---
type: reading-note
source_task: 2026-05-26-精读书籍javascript函数式编程
book: JavaScript函数式编程
created: 2026-05-27T07:01:29+08:00
status: structured-reading-note-v1
source_basis:
  - file:/Users/charles/Downloads/JavaScript函数式编程.pdf
  - artifact:/Users/charles/.hermes/tmp/JavaScript函数式编程-ocr-selected-pages-20260527.txt
  - artifact:/Users/charles/Documents/brain/03-知识库/reading-notes/2026-05-27-JavaScript函数式编程-精读预备与证据边界.md
license_boundary: 仅对本机已有个人副本做本地 OCR 读回；不下载、不再分发 PDF；本笔记只摘录少量结构性信息和自写理解。
acceptance_map:
  chapter_map: done
  key_concepts_examples: 10
  practice_exercises: 3
  application_point: done
---

# 《JavaScript函数式编程》结构化精读笔记 v1

## 证据边界 / Read-back

- 本次用 Swift + PDFKit + Apple Vision 对本机已有 `/Users/charles/Downloads/JavaScript函数式编程.pdf` 进行局部 OCR，产物：`artifact:/Users/charles/.hermes/tmp/JavaScript函数式编程-ocr-selected-pages-20260527.txt`。
- OCR 页范围：封面/封底、内容提要、前言组织结构、目录页、第一章开篇与 1.2.4 附近样页（1,2,5,13,17-30）。
- 来源读回事实：全书 224 页；内容提要称“全书共 9 章”，主题包括 JavaScript 函数式编程、一等函数与 Applicative、作用域/闭包、高阶函数、函数构建函数、递归、纯度/不变性/更改政策、基于流的编程、无类编程。
- 这份 v1 满足任务验收中的结构化笔记要素（章节地图、10 概念/例子、3 练习、1 应用点），但仍建议后续人工/持续 OCR 深读每章代码清单后再沉淀 v2。

## 章节地图（基于 OCR 目录/前言）

1. **JavaScript 函数式编程简介**：说明为什么 JavaScript 适合函数式风格；以函数作为抽象单元、封装/隐藏、行为单位、数据抽象；引入 Underscore 示例。
2. **一等函数与 Applicative 编程**：函数作为一等公民；集合中心编程；用函数映射/转换集合；建立“数据思考”。
3. **变量的作用域和闭包**：全局、词法、动态、函数作用域；闭包的工作机制、使用方式与抽象价值。
4. **高阶函数**：接收函数作为参数、返回函数的函数；通过捕获参数/变量、`fnull`、对象校验器来组织行为。
5. **由函数构建函数**：组合、柯里化、部分应用；把小函数拼成端到端的数据转换链。
6. **递归**：自调用、图遍历、深度优先搜索、Conjoin/Disjoin、相互递归、深克隆、嵌套数组、生成器和蹦床。
7. **纯度、不变性和更改政策**：纯函数、测试、引用透明性、幂等性、不变数据、冻结/克隆、对象不变性、控制变化策略。
8. **基于流的编程**：链接、惰性链、Promise、管道、数据流与控制流，把任务/系统看成数据变换流水线。
9. **无类编程**：数据导向、Mixin、原型修改风险、扁平化层级、通过 Mixin 扩展语义与类型，强调方法是低级操作。
10. **附录**：函数式 JavaScript 库（Functional JavaScript、Underscore-contrib、RxJS、Bilby、allong.es 等）和可编译到 JavaScript 的函数式语言（ClojureScript、CoffeeScript、Roy、Elm），以及推荐书目。

## 10 条关键概念 / 例子

1. **函数式编程的核心定义**：书中第 1 章将其概括为“通过使用函数来将值转换成抽象单元，接着用于构建软件系统”。可执行含义：把业务步骤表达为 `input -> transform -> output`，而不是把状态分散在多个对象里。
2. **函数是一等值**：JavaScript 函数既是对象也是值，可作为参数、返回值、数据结构元素。封底示例强调使用“一等函数及 applicative 编程技术”。
3. **`apply` / `call` / `arguments` 体现函数操作能力**：OCR 第 1 章样页给出 `splat(fun)`：把数组展开给函数；`unsplat(fun)`：把任意参数收集成数组再传入函数。这是从“调用语法”抽象出可组合行为的例子。
4. **以函数为抽象单元**：`parseAge` 示例先把日志/警告/错误写死，随后抽取成 `fail`、`warn`、`note`。价值是把可替换策略封装成小函数，而不是散落在业务代码里。
5. **封装不只属于对象**：书中用 Stack 图说明对象封装，再指出 JavaScript 可借助闭包隐藏数据。函数式封装关注“隐藏可变细节，只暴露行为”。
6. **行为单位可被命名和传递**：数组索引本是语法行为，书中抽成 `nth(a,index)`。把语法/模式封成函数后，才能组合、校验、测试和传递。
7. **函数组合是构建更大行为的胶水**：目录第 5 章围绕组合、柯里化、部分应用；第 1 章图示把 `md -> toHTML -> postProcess -> modifyDOM` 视作数据装配线。
8. **减少可见状态修改**：第 1 章对比面向对象系统的“变化网”和函数式系统的“数据转换机器”。实践重点不是完全消灭状态，而是把 mutation 压缩到小边界。
9. **纯度/不变性提升测试与推理能力**：第 7 章目录将纯度与测试、引用透明性、幂等性、不变性、冻结和克隆放在一起；这说明函数式风格的工程收益是可验证性。
10. **流/管道适合 JavaScript 应用复杂度**：第 8 章把任务/系统视作变换数据的装配线；对前端异步、Promise、UI action 和数据清洗尤其可迁移。

## 3 个实践练习

1. **练习 A：抽取副作用边界**
   - 找一个现有 JS 函数，若内部同时做参数解析、日志、默认值、业务计算，把日志/错误/默认值策略抽成 `note/warn/fail/defaultTo` 一类函数。
   - 验收：核心函数可用纯输入输出单测覆盖；副作用函数可替换为测试 spy。

2. **练习 B：实现 `splat` / `unsplat` / `nth` 安全版**
   - `splat(fn)`：把数组参数展开给 `fn`。
   - `unsplat(fn)`：把任意参数收集成数组给 `fn`。
   - `safeNth(a,index)`：先校验 array-like 和边界，再返回值。
   - 验收：包含正常、空数组、越界、非数组输入测试。

3. **练习 C：用组合/管道改写一段数据处理**
   - 选择一个数组数据处理任务（例如 task rows -> filter dispatchable -> sort priority -> map title）。
   - 先写命令式循环版，再写 `filter/map/reduce` 或 `pipe` 版。
   - 验收：两版输出一致；组合版中每个小函数可单独测试。

## 1 个可落地到项目/技能树的应用点

**应用点：Hermes taskpool/dashboard 的 advisory 数据转换链。** 任务池有大量“读入任务 note -> 解析 frontmatter -> 计算 dispatchable/priority -> 输出 dashboard/next JSON”的数据流，适合采用本书的函数式分层：

- 把纯计算函数（状态分类、优先级排序、evidence 规范化、boundary warning 聚合）和副作用（读写 markdown、transition、dashboard write）分离。
- 对纯函数建立 fixture 单测，避免当前控制面中“历史 proof debt / soft warning / hard blocker”互相污染。
- 用显式 pipeline 表达：`loadTasks -> normalizeMissionEnvelope -> classifyBoundary -> selectNext -> renderDashboard`，每一步产出可记录中间 evidence。

## 后续 v2 建议

- 对第 2-9 章各选 3-5 页代码清单做 OCR，补“逐章代码卡片”。
- 将练习 B/C 变成可运行的 JS snippet 与测试，另建实现类任务，不在本阅读任务中自动执行未知第三方代码。

## Closeout evidence for this tranche

- `command:swift_pdfkit_vision_ocr_selected_pages`
- `artifact:/Users/charles/.hermes/tmp/JavaScript函数式编程-ocr-selected-pages-20260527.txt`
- `artifact:/Users/charles/Documents/brain/03-知识库/reading-notes/2026-05-27-JavaScript函数式编程-结构化精读笔记-v1.md`
- `proof:chapter map + 10 key concepts/examples + 3 practice exercises + 1 Hermes skill/taskpool application point recorded from local OCR readback`
