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
- Full unit suite: 52/52 PASS
  - 观测台 25 项；直接媒体绑定 6 项；市场 loop 9 项；原编译器/批处理 12 项。
  - 独立审查发现并修复受保护面大小写/空白/连字符/Unicode 分隔符绕过，以及空机制字段满足 direct gameplay 的问题；修复后 fresh 只读复审结论为 `no material findings`。
- JSON parse/readback: PASS
- Capability graph node/dependency/wrapper references: PASS
- `git diff --check`: PASS
- Market receipt: `verified_current_hot=0`, `recent_market_lead=2`, `stale_lead=1`, `unranked_lead=0`
- Market snapshot digest: `7d3f4b2c31ab5e90c84f5da6cf8b2078a5a7f9dcb35886dd55c43f1351533e0a`
- Market receipt digest: `3ff542da33cec341651a9472c14c2a29eb9d8dd62be140f4d0a0cea6511a68b7`
- Real snapshot hypotheses: accepted 0, rejected 2；均为 `source_observation_not_verified_current_hot`。
- Hypotheses digest: `4e9c570bed230c2aa4c85d5bd136f3f0fd37c76be7c594ffb4b71ac6e2251dfb`
- Loop receipt digest: `caf3826ca56c6ddb4b7f001c34f6e443d6e77e2b399244e10cc30e5be930fcbd`
- Receipt binding adversarial tests: snapshot 物料变化、被拒候选变化、来源主体错配、旧来源伪装新信号、弱发现来源凑 quorum、直接来源等级伪装、本地媒体摘要错配均 fail closed。
- `may_freeze_kernel=false`, `may_compile_work_package=false`, all external authorities false

## Claim boundary

证明：本地路由、字段隔离、参数边界、确定性编译、批次失败隔离和副作用关闭；热门玩法观测会按时间失效、独立来源和直接试玩门禁 fail closed；未经 `verified_current_hot` 的市场线索不能进入 `kernel_hypothesis`，而通过该门禁也不会自动冻结内核或编译工作包。

不证明：当前平台完整榜单、任何游戏已经达到 `verified_current_hot`、玩法有趣、Cocos 运行时正确、真实平台 SDK/审核/广告、真实用户指标或商业结果。
