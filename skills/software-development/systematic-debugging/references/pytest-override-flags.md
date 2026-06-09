# Pytest override flags for xdist-configured projects

## Pitfall: `-p no:xdist` does NOT clear `-n auto` from pyproject.toml

When `pyproject.toml` or `setup.cfg` sets `addopts = -n auto`, passing `-p no:xdist` to pytest
disables the plugin but pytest still tries to parse `-n` from the config, causing:

```
__main__.py: error: unrecognized arguments: -n
```

### Fix: override addopts entirely

```bash
# WRONG — -n auto still injected from config
pytest -p no:xdist tests/foo.py

# RIGHT — clears the config-level addopts
pytest -o "addopts=" tests/foo.py

# RIGHT — run serially with specific tests
pytest -o "addopts=" tests/foo.py::TestClass::test_method -v --tb=long
```

### When to use

- Running a single test file or small subset (serial is fine, xdist overhead not needed)
- Debugging with `--tb=long` (xdist truncates tracebacks)
- Needing `--pdb` or interactive debugging (incompatible with xdist)

### Quick reference

| Goal | Command |
|------|---------|
| Clear addopts, run serial | `pytest -o "addopts=" tests/` |
| Clear + verbose + long tracebacks | `pytest -o "addopts=" -v --tb=long tests/` |
| Target specific tests serially | `pytest -o "addopts=" tests/foo.py::X::y -v` |
| Still use xdist but override count | `pytest -o "addopts=-n 4" tests/` |
