# Pure Storage Rack Diagram Project - Claude Notes

## Development Environment

### Python Environment
Always use the local Python environment when running tests or development tasks:

```bash
source purerackdiagram_env_local/bin/activate
```

This ensures consistent dependencies and avoids conflicts with system Python packages.

## Test Execution

### Running Tests
When running tests, always specify the git state for proper result tracking:

```bash
# Example: Running tests on a specific commit
python test.py all --git-state 9fc053a

# Use with local environment
source purerackdiagram_env_local/bin/activate && python test.py all --git-state 9fc053a
```

### Git State Management
- Tests are organized by git state (commit hash) in subdirectories under `test_results/`
- Use `--git-state` parameter to specify which commit the tests are being run against
- This helps track changes and regressions across different code versions

## Project Structure

### Test Files
- `test.py` - Main test runner with enhanced features for git-state tracking
- `test_one_offs.py` - Additional test cases (if available)
- `test_results/` - Directory containing test results organized by git state

### Lambda Entry
- `lambdaentry.py` - Main entry point for the Pure Storage rack diagram generator

## Notes
- Always activate the local environment before running any Python commands
- Use git state tracking for all test runs to maintain proper version control of test results