# Test Suite Bootstrapping for Existing Codebases

## Overview

When inheriting or revisiting a codebase with zero tests, you need a bootstrapping pattern distinct from greenfield TDD. The goal is to establish a regression safety net quickly, then iterate toward full coverage.

## Pattern: Self-Check Pipeline

### 1. Test File Structure

```
project/
├── test_core_components.py    # Core component tests
├── self_check.py              # Automated health check
├── self_check_report.json     # Generated report
└── src/
    ├── component_a.py
    └── component_b.py
```

### 2. Test Suite Template

```python
#!/usr/bin/env python3
"""
Core component test suite
"""

import unittest
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class TestComponentA(unittest.TestCase):
    """Component A tests"""
    
    def setUp(self):
        from component_a import ComponentA
        self.component = ComponentA()
    
    def test_basic_operation(self):
        """Test basic operation"""
        result = self.component.do_something()
        self.assertIsNotNone(result)
    
    def test_error_handling(self):
        """Test error handling"""
        with self.assertRaises(ValueError):
            self.component.do_something(invalid=True)

def run_tests():
    """Run tests"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestComponentA))
    
    runner = unittest.TextTestRunner(verbosity=2)
    return runner.run(suite)

if __name__ == "__main__":
    result = run_tests()
    print(f"\nTests: {result.testsRun}, Failures: {len(result.failures)}, Errors: {len(result.errors)}")
```

### 3. Self-Check Script

```python
#!/usr/bin/env python3
"""
Self-check pipeline for project health
"""

import os
import sys
import json
import subprocess
from datetime import datetime

class SelfChecker:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.results = {}
    
    def check_test_coverage(self):
        """Check test file coverage"""
        test_files = [f for f in os.listdir(self.project_dir) 
                     if f.startswith("test_") and f.endswith(".py")]
        source_files = [f for f in os.listdir(self.project_dir) 
                       if f.endswith(".py") and not f.startswith("test_")]
        
        coverage = len(test_files) / len(source_files) * 100 if source_files else 0
        return {
            "test_files": len(test_files),
            "source_files": len(source_files),
            "coverage": coverage,
            "status": "PASS" if coverage > 50 else "FAIL"
        }
    
    def check_code_quality(self):
        """Check Python syntax"""
        errors = 0
        for f in os.listdir(self.project_dir):
            if f.endswith(".py"):
                result = subprocess.run(
                    ["python3", "-m", "py_compile", os.path.join(self.project_dir, f)],
                    capture_output=True
                )
                if result.returncode != 0:
                    errors += 1
        
        return {"syntax_errors": errors, "status": "PASS" if errors == 0 else "FAIL"}
    
    def check_component_integration(self):
        """Check core components exist"""
        core = ["component_a.py", "component_b.py"]
        missing = [c for c in core if not os.path.exists(os.path.join(self.project_dir, c))]
        
        return {
            "total": len(core),
            "missing": missing,
            "status": "PASS" if len(missing) == 0 else "FAIL"
        }
    
    def run_tests(self):
        """Run test suite"""
        test_file = os.path.join(self.project_dir, "test_core_components.py")
        if not os.path.exists(test_file):
            return {"status": "SKIP"}
        
        result = subprocess.run(
            ["python3", test_file],
            capture_output=True,
            text=True,
            cwd=self.project_dir
        )
        
        return {
            "status": "PASS" if "OK" in result.stdout else "FAIL",
            "returncode": result.returncode
        }
    
    def run_full_check(self):
        """Run all checks"""
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "checks": {
                "test_coverage": self.check_test_coverage(),
                "code_quality": self.check_code_quality(),
                "component_integration": self.check_component_integration(),
                "tests": self.run_tests()
            }
        }
        
        all_passed = all(
            c.get("status") == "PASS" 
            for c in self.results["checks"].values()
            if c.get("status") != "SKIP"
        )
        self.results["overall_status"] = "PASS" if all_passed else "FAIL"
        
        return self.results

if __name__ == "__main__":
    checker = SelfChecker("/path/to/project")
    results = checker.run_full_check()
    
    with open("self_check_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"Overall: {results['overall_status']}")
    for name, check in results["checks"].items():
        print(f"  {name}: {check['status']}")
```

## Interface Discovery Pattern

When testing components with unknown interfaces:

```python
# 1. Discover the interface
grep -n "def " component.py | head -20

# 2. Test with discovered methods
def test_component(self):
    from component import Component
    c = Component()
    
    # Use actual method names from grep
    result = c.actual_method_name()
    self.assertIsNotNone(result)
```

## Common Pitfalls

1. **Assuming interfaces** — Always grep/discover first
2. **Testing implementation details** — Test behavior, not internals
3. **Skipping integration tests** — Unit tests alone miss interaction bugs
4. **No self-check automation** — Manual checks are unreliable

## Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | >50% | test_files / source_files |
| Syntax errors | 0 | py_compile check |
| Component integration | 100% | Core components exist |
| Test success rate | 100% | All tests pass |

## Integration with TDD

After bootstrapping:
1. New features → Use strict TDD (RED-GREEN-REFACTOR)
2. Bug fixes → Write failing test first, then fix
3. Refactoring → Ensure tests pass before and after

The bootstrapping pattern establishes the safety net; TDD maintains it.
