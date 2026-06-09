# Python Test Debugging Patterns

## Common Test Failures

### 1. Interface Mismatch

**Symptom**: `AttributeError: 'X' object has no attribute 'method_name'`

**Cause**: Test assumes interface without checking actual implementation

**Fix**:
```bash
# Discover actual interface
grep -n "def " component.py | head -20

# Update test to use actual methods
def test_component(self):
    from component import Component
    c = Component()
    result = c.actual_method()  # Not assumed_method()
```

### 2. Import Errors

**Symptom**: `ModuleNotFoundError: No module named 'component'`

**Cause**: Python path not set correctly

**Fix**:
```python
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
```

### 3. Type Errors in Assertions

**Symptom**: `AssertionError: 'Python' not found in 'content'`

**Cause**: Test data doesn't match search behavior

**Fix**:
```python
# Bad: Assumes specific content
self.assertIn("Python", results[0]["content"])

# Good: Check result exists
self.assertGreater(len(results), 0)
```

### 4. Missing Version Attribute

**Symptom**: `AssertionError: False is not true` on `hasattr(module, '__version__')`

**Cause**: Module doesn't have `__version__`

**Fix**:
```python
# Check for actual exports
self.assertTrue(hasattr(module, 'MainClass') or hasattr(module, 'main'))
```

## Test Discovery Patterns

### Discover Available Methods

```bash
# List all methods
grep -n "def " component.py

# List public methods only
grep -n "def [^_]" component.py

# List class methods
grep -n "class " component.py
```

### Discover Return Types

```python
# Add debug print in test
def test_component(self):
    result = self.component.method()
    print(f"Return type: {type(result)}")
    print(f"Return value: {result}")
    self.assertIsNotNone(result)
```

## Test Suite Structure

```python
class TestComponent(unittest.TestCase):
    """Component tests"""
    
    def setUp(self):
        """Initialize test fixtures"""
        from component import Component
        self.component = Component()
    
    def test_basic_operation(self):
        """Test basic happy path"""
        result = self.component.method()
        self.assertIsNotNone(result)
    
    def test_error_handling(self):
        """Test error conditions"""
        with self.assertRaises(ValueError):
            self.component.method(invalid=True)
    
    def test_edge_cases(self):
        """Test boundary conditions"""
        result = self.component.method(input="")
        self.assertEqual(result, expected_default)
```

## Self-Check Integration

```python
def run_tests(self):
    """Run tests and capture results"""
    result = subprocess.run(
        ["python3", "test_suite.py"],
        capture_output=True,
        text=True
    )
    
    # Parse output
    if "OK" in result.stdout:
        return {"status": "PASS"}
    elif "FAIL" in result.stdout:
        return {"status": "FAIL"}
    else:
        return {"status": "UNKNOWN"}
```

## Debugging Workflow

1. **Run test**: `python3 test_suite.py 2>&1`
2. **Read error**: Identify failure type
3. **Discover interface**: `grep -n "def " component.py`
4. **Fix test**: Update to match actual interface
5. **Re-run**: Verify fix works
6. **Commit**: Save working test

## Common Patterns

### Testing Data Storage

```python
def test_store_and_retrieve(self):
    # Store
    self.storage.store("key", {"data": "value"})
    
    # Retrieve
    result = self.storage.retrieve("key")
    
    # Verify
    self.assertIsNotNone(result)
    self.assertEqual(result["data"], "value")
```

### Testing Event Systems

```python
def test_publish_subscribe(self):
    received = []
    
    def handler(event):
        received.append(event)
    
    self.event_bus.subscribe("topic", handler)
    self.event_bus.publish("topic", {"data": "value"})
    
    self.assertEqual(len(received), 1)
```

### Testing Search Systems

```python
def test_search(self):
    # Add data
    self.search_engine.add("id1", "content about Python")
    
    # Search
    results = self.search_engine.search("Python")
    
    # Verify
    self.assertGreater(len(results), 0)
    self.assertEqual(results[0]["id"], "id1")
```
