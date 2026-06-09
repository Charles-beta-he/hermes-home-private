# Edge Worker Test Coverage Improvement

## Pattern

When improving test coverage for hermes-edge-worker, follow this systematic approach:

### 1. Baseline Assessment

Run `self_check.py` to establish current coverage:
```bash
cd ~/hermes-edge-worker
python3 self_check.py 2>&1 | head -30
```

Key metrics:
- Test files count
- Source code files count
- Test cases count
- Coverage percentage

### 2. Identify Uncovered Components

Check which components lack tests:
```bash
# List all source files
find scripts/ -name "*.py" ! -name "__init__.py" | sort

# List all test files
find . -name "test_*.py" | sort
```

### 3. Create Component Tests

For each uncovered component, create a test file:

```python
#!/usr/bin/env python3
"""
<ComponentName> tests
提升测试覆盖率
"""

import unittest
import sys
from pathlib import Path

# 添加脚本目录到路径
SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from <component_module> import <ComponentClass>

class Test<ComponentName>(unittest.TestCase):
    """<ComponentName>测试"""
    
    def setUp(self):
        """测试前准备"""
        self.component = <ComponentClass>()
    
    def test_<method>(self):
        """测试<方法>"""
        # Test implementation
        pass

def run_tests():
    """运行测试"""
    loader = unittest.TestLoader()
    test_suite = unittest.TestSuite()
    test_suite.addTests(loader.loadTestsFromTestCase(Test<ComponentName>))
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(test_suite)

if __name__ == "__main__":
    result = run_tests()
    print(f"\n=== 测试结果 ===")
    print(f"运行测试: {result.testsRun}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    print(f"成功率: {(result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100:.1f}%")
```

### 4. Run All Tests

```bash
# Run each test file individually
python3 test_complete.py 2>&1 | tail -5
python3 test_integration.py 2>&1 | tail -5
python3 test_api.py 2>&1 | tail -5
python3 test_multi_site_manager.py 2>&1 | tail -5
python3 test_event_driven.py 2>&1 | tail -5

# Count total test cases
python3 -c "
import unittest
loader = unittest.TestLoader()
suite = unittest.TestSuite()
test_files = ['test_complete.py', 'test_integration.py', 'test_api.py', 
              'test_multi_site_manager.py', 'test_event_driven.py']
for f in test_files:
    try:
        module = __import__(f.replace('.py', ''))
        suite.addTests(loader.loadTestsFromModule(module))
    except: pass
print(f'总测试用例数: {suite.countTestCases()}')
"
```

### 5. Verify Coverage Improvement

```bash
python3 self_check.py 2>&1 | grep "覆盖率"
```

## Pitfalls

1. **Syntax typos**: Always run `python3 -m py_compile <file>` before running tests
2. **Assertion mismatch**: Run tests first (RED) to see actual behavior, then adjust assertions
3. **Import errors**: Ensure `sys.path` includes the scripts directory
4. **Component dependencies**: Some components require initialization (e.g., orchestrator) — test warning paths separately

## Coverage Targets

| Phase | Target | Test Cases |
|-------|--------|------------|
| Initial | 10-15% | 50-80 |
| Phase 1 | 30% | 120 |
| Phase 2 | 50% | 200 |
| Phase 3 | 70% | 280 |
| Phase 4 | 90% | 360 |

## Version Tracking

Update `version.txt` before each commit:
```bash
echo "3.9.0" > version.txt
git add test_*.py version.txt
git commit -m "feat: 测试覆盖率提升"
git push origin main
```
