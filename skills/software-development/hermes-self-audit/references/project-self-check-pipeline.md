# Project-Level Self-Check Pipeline

## Overview

For project-level health checks (not Hermes internal), create a `self_check.py` that validates:
1. Test coverage
2. Code quality
3. Component integration
4. Documentation
5. Deployment readiness

## Template

```python
#!/usr/bin/env python3
"""
Project self-check pipeline
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from typing import Dict, Any

class ProjectSelfChecker:
    def __init__(self, project_dir: str):
        self.project_dir = project_dir
        self.results = {}
    
    def check_test_coverage(self) -> Dict[str, Any]:
        """Check test file coverage"""
        test_files = []
        source_files = []
        
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    if file.startswith("test_"):
                        test_files.append(filepath)
                    elif not file.startswith("__"):
                        source_files.append(filepath)
        
        coverage = len(test_files) / len(source_files) * 100 if source_files else 0
        
        return {
            "test_files": len(test_files),
            "source_files": len(source_files),
            "coverage": round(coverage, 1),
            "status": "PASS" if coverage > 50 else "FAIL"
        }
    
    def check_code_quality(self) -> Dict[str, Any]:
        """Check Python syntax"""
        errors = 0
        error_files = []
        
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    result = subprocess.run(
                        ["python3", "-m", "py_compile", filepath],
                        capture_output=True
                    )
                    if result.returncode != 0:
                        errors += 1
                        error_files.append(file)
        
        return {
            "syntax_errors": errors,
            "error_files": error_files,
            "status": "PASS" if errors == 0 else "FAIL"
        }
    
    def check_component_integration(self, core_components: list) -> Dict[str, Any]:
        """Check core components exist"""
        missing = []
        for component in core_components:
            filepath = os.path.join(self.project_dir, component)
            if not os.path.exists(filepath):
                missing.append(component)
        
        return {
            "total_components": len(core_components),
            "missing_components": missing,
            "status": "PASS" if len(missing) == 0 else "FAIL"
        }
    
    def check_documentation(self) -> Dict[str, Any]:
        """Check documentation exists"""
        readme_exists = os.path.exists(os.path.join(self.project_dir, "README.md"))
        
        md_files = []
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(".md"):
                    md_files.append(file)
        
        return {
            "readme_exists": readme_exists,
            "markdown_files": len(md_files),
            "status": "PASS" if readme_exists else "FAIL"
        }
    
    def check_deployment(self) -> Dict[str, Any]:
        """Check deployment configuration"""
        install_scripts = []
        config_files = []
        
        for root, dirs, files in os.walk(self.project_dir):
            for file in files:
                if file.startswith("install") and file.endswith(".sh"):
                    install_scripts.append(file)
                elif file.endswith((".yaml", ".yml", ".json")):
                    config_files.append(file)
        
        return {
            "install_scripts": len(install_scripts),
            "config_files": len(config_files),
            "status": "PASS" if len(install_scripts) > 0 else "FAIL"
        }
    
    def run_tests(self) -> Dict[str, Any]:
        """Run test suite"""
        test_file = os.path.join(self.project_dir, "test_core_components.py")
        if not os.path.exists(test_file):
            return {"status": "SKIP", "reason": "No test file found"}
        
        result = subprocess.run(
            ["python3", test_file],
            capture_output=True,
            text=True,
            cwd=self.project_dir
        )
        
        # Parse output for test results
        output = result.stdout
        if "OK" in output and "FAIL" not in output:
            status = "PASS"
        elif "FAIL" in output or "ERROR" in output:
            status = "FAIL"
        else:
            status = "UNKNOWN"
        
        return {
            "status": status,
            "returncode": result.returncode,
            "output_tail": output[-500:] if len(output) > 500 else output
        }
    
    def run_full_check(self, core_components: list = None) -> Dict[str, Any]:
        """Run all checks"""
        if core_components is None:
            core_components = []
        
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "project_dir": self.project_dir,
            "checks": {
                "test_coverage": self.check_test_coverage(),
                "code_quality": self.check_code_quality(),
                "component_integration": self.check_component_integration(core_components),
                "documentation": self.check_documentation(),
                "deployment": self.check_deployment(),
                "tests": self.run_tests()
            }
        }
        
        # Calculate overall status
        all_passed = all(
            check.get("status") == "PASS" 
            for check in self.results["checks"].values()
            if check.get("status") != "SKIP"
        )
        self.results["overall_status"] = "PASS" if all_passed else "FAIL"
        
        return self.results
    
    def print_summary(self):
        """Print human-readable summary"""
        print(f"Project: {self.project_dir}")
        print(f"Timestamp: {self.results.get('timestamp', 'N/A')}")
        print()
        
        for name, check in self.results.get("checks", {}).items():
            status = check.get("status", "UNKNOWN")
            print(f"  {name}: {status}")
            
            # Print details for failures
            if status == "FAIL":
                if name == "test_coverage":
                    print(f"    Coverage: {check.get('coverage', 0)}%")
                elif name == "code_quality":
                    print(f"    Syntax errors: {check.get('syntax_errors', 0)}")
                elif name == "component_integration":
                    print(f"    Missing: {check.get('missing_components', [])}")
        
        print()
        print(f"Overall: {self.results.get('overall_status', 'UNKNOWN')}")
    
    def save_report(self, filepath: str = None):
        """Save report to JSON"""
        if filepath is None:
            filepath = os.path.join(self.project_dir, "self_check_report.json")
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"Report saved: {filepath}")

def main():
    """CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Project self-check")
    parser.add_argument("--project-dir", default=".", help="Project directory")
    parser.add_argument("--core-components", nargs="+", help="Core component files")
    parser.add_argument("--output", help="Output report path")
    
    args = parser.parse_args()
    
    checker = ProjectSelfChecker(args.project_dir)
    results = checker.run_full_check(args.core_components or [])
    
    checker.print_summary()
    checker.save_report(args.output)
    
    sys.exit(0 if results["overall_status"] == "PASS" else 1)

if __name__ == "__main__":
    main()
```

## Usage

```bash
# Basic usage
python3 self_check.py

# With core components
python3 self_check.py --core-components component_a.py component_b.py

# Custom output path
python3 self_check.py --output report.json
```

## Integration with CI/CD

```yaml
# .github/workflows/self-check.yml
name: Self Check
on: [push, pull_request]

jobs:
  self-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Run self-check
        run: python3 self_check.py
```

## Quality Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | >50% | test_files / source_files |
| Syntax errors | 0 | py_compile check |
| Component integration | 100% | Core components exist |
| Documentation | 100% | README exists |
| Test success rate | 100% | All tests pass |
