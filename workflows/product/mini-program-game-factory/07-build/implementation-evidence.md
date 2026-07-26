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

## 热门玩法观测台验证（2026-07-26T13:49:03Z）

```bash
python3 -m py_compile hot_game_observatory.py test_hot_game_observatory.py work_package_compiler.py batch_compile.py test_work_package_compiler.py test_batch_compile.py
python3 -m unittest -v test_hot_game_observatory.py test_batch_compile.py test_work_package_compiler.py
python3 hot_game_observatory.py ../evidence/hot-game-snapshot-2026-07-26.json --as-of 2026-07-26T12:00:00+08:00 --output ../evidence/hot-game-receipt-2026-07-26.json
```

- Combined unit tests: 22/22 PASS（其中观测台 10 项）
- JSON parse: PASS
- Capability graph node/dependency/wrapper references: PASS
- Market receipt: `verified_current_hot=0`, `recent_market_lead=2`, `stale_lead=1`, `unranked_lead=0`
- Receipt digest: `90a08abc4cda2cd6a64552fbb324a75b5a6432cd42921260e30a8fb751fcc7ec`
- `may_freeze_kernel=false`

## Claim boundary

证明：本地路由、字段隔离、参数边界、确定性编译、批次失败隔离和副作用关闭；热门玩法观测会按时间失效、独立来源和直接试玩门禁 fail closed。

不证明：当前平台完整榜单、任何游戏已经达到 `verified_current_hot`、玩法有趣、Cocos 运行时正确、真实平台 SDK/审核/广告、真实用户指标或商业结果。
