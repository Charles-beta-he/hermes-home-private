# 本地实现证据

## 验证命令

```bash
cd /Users/charles/.hermes/workflows/product/mini-program-game-factory/07-build
python3 -m py_compile work_package_compiler.py batch_compile.py test_work_package_compiler.py test_batch_compile.py
python3 -m unittest -v test_batch_compile.py test_work_package_compiler.py
python3 work_package_compiler.py --seed sample-seed.json --routing ../model-routing.json --output ../evidence/sample-work-package.json
python3 batch_compile.py --batch sample-batch.json --routing ../model-routing.json --output ../evidence/sample-batch-receipt.json
```

## Fresh result

- Python compilation: PASS
- Unit tests: 12/12 PASS
- JSON parse/readback: 8 files PASS
- Single candidate route: `low_cost`
- Single closure: `work_package_compiled`
- Single compile digest: `5cf24b21beab6258d18b07291406c3c5ff04d00ad83e4fd0666bf6ff890eb6e0`
- Batch summary: accepted 2, rejected 1, total 3
- Batch digest: `c482efd446d3422c33bc22ebbb2869add9eeb4365e7d78a4eda1d63841bd5e64`
- Rejected candidate: `invalid-oversized-grid` → `parameter grid_size out of bounds: 100`
- External publish/platform submission/credential/payment authority: all false

## 市场观测→研发 loop 全量验证（2026-07-26）

```bash
python3 -m unittest discover -v -s . -p 'test_*.py'
python3 -c 'import pathlib,py_compile; files=sorted(pathlib.Path(".").glob("*.py")); [py_compile.compile(str(p), doraise=True) for p in files]'
python3 hot_game_observatory.py ../evidence/hot-game-snapshot-2026-07-26.json --as-of 2026-07-26T12:00:00+08:00 --output ../evidence/hot-game-receipt-2026-07-26.json
python3 market_loop_gate.py \
  --snapshot ../evidence/hot-game-snapshot-2026-07-26.json \
  --hypotheses ../evidence/market-kernel-hypotheses-2026-07-26.json \
  --routing ../model-routing.json \
  --as-of 2026-07-26T12:00:00+08:00 \
  --output ../evidence/market-loop-receipt-2026-07-26.json
```

- Python compilation: 10 files PASS
- Full unit suite: 68/68 PASS
  - 观测台 35 项；直接媒体绑定 7 项；市场 loop 12 项；编译器 11 项；批处理 3 项。
  - 两轮延迟返回的旧树独立审查均作为有效 finding lead 而非当前通过票处理：除同媒体跨角色与隐藏保护面外，还指出非 direct `source_type/evidence_level` 错配、未绑定 canonical source registry、可替换 routing 配置、符号链接媒体路径，以及非 low-cost 编译结果不再标记 candidate 的缺口。
  - 当前本地修复要求榜单/试玩摘要隔离、7 天内试玩 `captured_at`、摘要绑定且类型一致的人工 `content_review`，并禁止 intake 接受预填复核；所有来源必须匹配 canonical registry 的类型/平台并使用精确 evidence-level 映射；本地直接媒体拒绝符号链接并使用 `O_NOFOLLOW` + fd/path 双重稳定身份；市场门禁与编译器拒绝非 canonical routing；全部编译产物在缺少后续 promotion receipt 时保持 candidate-only。对应负例已加入并通过；新精确提交独立复审仍为 PENDING。
- JSON parse/readback: PASS
- Capability graph node/dependency/wrapper references: PASS
- `git diff --check`: PASS
- Market receipt: `verified_current_hot=0`, `recent_market_lead=2`, `stale_lead=1`, `unranked_lead=0`
- Market snapshot canonical digest: `4d145d8148ce1054bffa1e9395fffc92db3b464078c760cc711f4d4f1aa75b1f`
- Market snapshot file SHA-256: `a1d786bbe19c3e3c8e6c33a4d3a0586c2c63aa1eb42071dad52610c63c621795`
- Market receipt digest: `607435cc60584e6cf84396a83926e2a1a8634e5594ca34d94fab6d55788d1668`
- Real snapshot hypotheses: accepted 0, rejected 2；均为 `source_observation_not_verified_current_hot`。
- Hypotheses digest: `52cf6cbc4849cab07b1c2ad136b1b95a2bf144d8b15caf92017e7290a23896e3`
- Routing digest: `518b9f693b308766227babd7c5b7bcd566b125d4481ca458b25d1fed08ed6db1`
- Loop receipt digest: `e6343a8a808cb014478cbecdd759ab429dd74833259ce585c0b3f3cd277cecfd`
- Receipt/gate adversarial tests: snapshot 物料变化、被拒候选变化、来源主体错配、旧来源伪装新信号、弱发现来源凑 quorum、direct/non-direct 等级伪装、canonical registry/routing 替换、本地媒体摘要错配与符号链接、榜单/试玩复用摘要、过期试玩时间、缺失/错误人工分类、预填人工复核、缺失 proposed changes、抽象机制夹带保护面及非 low-cost 产物越过 candidate-only 均 fail closed。
- `may_freeze_kernel=false`, `may_compile_work_package=false`, all external authorities false

## Claim boundary

证明：canonical 本地路由、来源注册绑定、字段隔离、参数边界、确定性候选编译、批次失败隔离和副作用关闭；热门玩法观测会按时间失效、独立来源和直接试玩门禁 fail closed；未经 `verified_current_hot` 的市场线索不能进入 `kernel_hypothesis`，而通过该门禁也不会自动冻结内核或编译工作包。

不证明：调用者身份或人工复核者的密码学认证、函数返回后的路径永久不可变、当前平台完整榜单、任何游戏已经达到 `verified_current_hot`、玩法有趣、Cocos 运行时正确、真实平台 SDK/审核/广告、真实用户指标或商业结果。
