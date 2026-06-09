# Runtime-overlay-sensitive test fix pattern

Use this when a Hermes test asserts behavior around **provider/overlay/runtime discovery** but starts failing because the live environment already contains a synthetic or locally discovered entity.

## Symptom

A test injects a provider/overlay name that should be treated as missing or unknown, but the system under test recognizes it anyway because:
- runtime overlay discovery runs at import time,
- local auth/OAuth sets are populated from the live environment, or
- the test branches on whether the synthetic name already existed.

## Root cause

The assertion is coupled to the host environment instead of the contract.

## Fix sequence

1. **Make the synthetic identity unique**  
   Generate a random name/ID that cannot collide with real registrations.

2. **Seed the mapping explicitly**  
   Build the provider/env/allowlist set from the static source, then inject only the synthetic entry.

3. **Assert the deterministic contract**  
   Choose one stable expectation:
   - unknown-provider is available by default, or
   - known-provider-without-key is unavailable.

4. **Remove environment-dependent branching**  
   Do not keep `if already known ... else ...` assertions; they just reproduce today's host state.

## Verification

- Run the targeted test 3 times locally.
- Run the owning suite once.
- Confirm no new runtime overlay imports remain in the assertion boundary.
