# chore(epic-TSE-0001): standardize validation scripts across ecosystem

## Summary

This PR standardizes git quality standards infrastructure by updating validation scripts to match the ecosystem-wide standards established in audit-correlator-go.

**Key Changes:**
- Replaced all validate-all.sh files with standardized version
- Replaced symlinks with actual file copies for better portability
- Removed deprecated validate-repository.sh files
- Updated TODO.md to document git quality standards completion

## What Changed

### Validation Scripts Standardization

**validate-all.sh Updates:**
- Simplified PR documentation matching: exact branch name with slash-to-dash conversion only
- Added TODO.md OR TODO-MASTER.md check (supports both TODO journal patterns)
- Removed complex PR prefix mapping and epic pattern matching
- Consistent markdown linting and documentation validation
- Identical version across all 18 repositories (checksum: 3af7df6d89aedddb74d7c3ddf1c9924c)

**PR Documentation Matching (Simplified):**
```bash
# Old (removed): Complex fallback with PR prefix mapping, epic patterns, manual selection
# New (simple): Exact branch name with slash-to-dash conversion
BRANCH_FILENAME=$(echo "$CURRENT_BRANCH" | sed 's/\//-/g')
Expected file: docs/prs/${BRANCH_FILENAME}.md
```

**Symlink Replacement:**
- Replaced symbolic links in scripts/ directory with actual file copies
- Improves portability across different filesystems and deployment scenarios
- Eliminates broken symlink issues in CI/CD environments

**Deprecated Files Removed:**
- Removed validate-repository.sh from both scripts/ and .claude/plugins/ directories
- Functionality consolidated into validate-all.sh for simplicity

### TODO.md Updates

Added completed milestone section documenting:
- Git Quality Standards foundation work
- All standardization tasks completed
- Completion date: 2025-10-29

### Repository Context

This is part of epic TSE-0001 Foundation work to establish consistent git workflows, validation standards, and documentation practices across all repositories in the trading ecosystem (18 total repositories standardized).

## Testing

### Validation Tests
- [x] Run `bash scripts/validate-all.sh` - passes all checks
- [x] Verify PR documentation exists for current branch
- [x] Confirm markdown linting passes
- [x] Verify TODO.md exists and is valid
- [x] Test pre-push hook logic (if applicable)
- [x] Verify all validate-all.sh files have identical checksums across ecosystem

### Cross-Repository Verification
- [x] Verified checksums match across all 18 repositories
- [x] Confirmed symlink replacement successful in 11 repositories
- [x] Validated deprecated files removed from 17 repositories
- [x] Tested validation in multiple repositories (audit-correlator-go, custodian-simulator-go, risk-monitor-py)

## Related Issues

- Epic TSE-0001: Foundation - Git Quality Standards
- Standardizing validation scripts across 18 repositories
- TODO journal system implementation

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
