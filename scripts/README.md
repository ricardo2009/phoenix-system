# 🛠️ Phoenix System Scripts

This directory contains utility scripts for maintaining and validating the Phoenix System workflows.

## Scripts

### `check-workflows.sh`

A comprehensive health check script for GitHub Actions workflows.

**Usage:**
```bash
./scripts/check-workflows.sh
```

**Features:**
- ✅ YAML syntax validation
- ✅ Check for unsupported GitHub Actions expressions
- ✅ Detect complex JSON parsing that might fail
- ✅ Find division operations in templates (not shell scripts)
- ✅ Identify overly long lines

**Exit Codes:**
- `0` - All checks passed
- `1` - Issues found that need attention

**Example Output:**
```
🔍 Phoenix System Workflow Health Check
=====================================

📁 Checking workflow directory...
✅ Workflow directory found

📝 Validating YAML syntax...
  Testing phoenix-basic.yml... ✅ Valid
  ...

🎉 All checks passed! Workflows are healthy.
```

## Development Workflow

1. **Before committing workflow changes:**
   ```bash
   ./scripts/check-workflows.sh
   ```

2. **If issues are found:**
   - Review the flagged items
   - Fix any actual problems (unsupported expressions, syntax errors)
   - Note: Division in shell scripts (`$(echo "scale=2; $x / 100" | bc)`) is acceptable

3. **After fixes:**
   ```bash
   ./scripts/check-workflows.sh
   git add .github/workflows/
   git commit -m "fix: resolve workflow issues"
   ```

## Notes

- The script may flag division operations in bash command substitutions - these are typically fine
- Complex expressions in GitHub Actions templates should be avoided
- Prefer simple, static configurations over dynamic calculations where possible

---
*For more information, see [WORKFLOW_FIXES.md](../docs/WORKFLOW_FIXES.md)*