# Spec Packet — Awesome LLM Apps Absorption

```yaml
spec_packet:
  goal: "source evidence -> capability catalog -> module pool -> loop recommendation -> temporary workflow"
  non_goals:
    - "bulk install or execute upstream apps"
    - "runtime/global canonicalization"
    - "external API, credential, cron, taskpool, AgentOS or publish side effects"
  invariants:
    - "every accepted capability keeps source path evidence"
    - "README claims remain distinct from local runtime proof"
    - "candidate modules cannot be represented as validated/common/canonical"
    - "temporary workflow side-effect flags remain false"
  constraints:
    - "source pinned to commit 426cfa66b5fd832090038c36e50a6aa1dab3119c"
    - "Apache-2.0 root license; dependency/data/model licenses remain separately unverified"
    - "local reversible artifacts only"
  acceptance_criteria:
    - "catalog contains discovered runnable-example directories and capability counts"
    - "module registry passes workflow_module_pool validate for every module"
    - "loop plan selects registered modules for requested functional families"
    - "temporary workflow has stable IO, gates, closure states, authority boundary and source refs"
    - "negative readback proves external/cron/taskpool/agentos flags are false"
  mock_policy: "source-static-evidence-only; no runtime capability acceptance"
  risk_class: "local_reversible"
  evidence_requirements:
    - "git commit readback"
    - "source file/path inventory"
    - "JSON/schema validation"
    - "loop receipt readback"
    - "negative side-effect assertion"
```

## Selected path

采用“静态扫描 + 候选模块池 + 本地 Loop + 临时工作流”路径，而非整库运行或逐应用复刻。它能以最低依赖成本形成可复用导航，并保留后续真实运行验证入口。

## Rejected paths

- 整库批量安装：依赖、凭证和供应商风险过高，且会制造重复能力。
- 只写分析报告：无法验证模块池和 Loop 能否真实消费。
- 直接创建全局 Skill：缺少独立运行验证和路由回归证据。
