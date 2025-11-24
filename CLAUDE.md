# Project Rules for homebrew-tagger

## Critical Git Tag Management Rules

**NEVER DELETE TAGS**
- Always create new tags, never delete existing tags
- If a tag needs to be corrected, create a new version (e.g., v1.11.1 instead of recreating v1.11.0)
- Tags are part of the public API and should be immutable once published
- Users and CI/CD systems may depend on existing tags

## Versioning Workflow

1. **Version Consistency**
   - `tagger` script: `__version__` variable (line 9)
   - `setup.py`: `version` parameter (line 13)
   - `man/tagger.1`: Man page header (line 1, `.TH` directive)
   - `tagger.rb`: Homebrew formula URL tag
   - All four must match for releases

2. **CI Version Check**
   - `.github/workflows/ci.yml` automatically verifies version consistency
   - Checks that `tagger` script and `setup.py` have matching versions

3. **Release Process (CRITICAL: All steps are REQUIRED)**
   - Update version in BOTH `tagger` and `setup.py`
   - Commit and push to main
   - Create new tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
   - **REQUIRED: Update Homebrew formula (`tagger.rb`)**
     - Update URL to new tag
     - Calculate and update SHA256: `curl -sL <URL> | shasum -a 256`
     - Commit and push formula update
   - Create GitHub release with release notes

## Homebrew Formula Testing

- `homebrew-test` workflow installs from the tagged release
- The formula must point to a tag that contains the correct version in the code
- Version mismatches will cause test failures

## Background Task Management

- Monitor and clean up old PR watch processes periodically
- Use `pkill -f "gh pr checks"` to stop unnecessary monitoring
- Keep only active PR monitors running

## Branch Strategy

- `main`: Production-ready code
- `feature/*`: New features (e.g., music recognition)
- `fix/*`: Bug fixes (e.g., version corrections)
- **CRITICAL: ALWAYS create PRs for review before merging to main**
  - **NEVER push directly to main**, even for version bumps or formula updates
  - Current branch protection allows admin bypass - resist the temptation
  - All changes must go through PR workflow with CI checks

## Release and Versioning Rules

### When to Bump Versions (Semantic Versioning)

**Format: MAJOR.MINOR.PATCH**

1. **MAJOR version** (e.g., 1.0.0 → 2.0.0)
   - Breaking changes to public API
   - Incompatible changes to command-line interface
   - Removal of deprecated features
   - Major architectural changes

2. **MINOR version** (e.g., 1.11.0 → 1.12.0)
   - **New features or modules added** (e.g., music recognition)
   - New command-line options or flags
   - Significant enhancements to existing features
   - New optional dependencies

3. **PATCH version** (e.g., 1.11.2 → 1.11.3)
   - Bug fixes only
   - Documentation updates
   - Internal refactoring without behavior changes
   - Dependency updates (without new features)

### Version Consistency Requirements

**CRITICAL: Version numbers must match exactly across all files and tags**

Files that must have matching versions:
- `tagger` script: `__version__` variable (line 9)
- `setup.py`: `version` parameter (line 13)
- `man/tagger.1`: Man page `.TH` header (line 1)
- Git tag: `vX.Y.Z` (exact match)
- Homebrew formula `tagger.rb`: URL tag and SHA256

### Release Workflow (After PR Merge)

**IMPORTANT: Version bump happens AFTER merging PR to main**

1. **Determine Version Bump**
   - Review merged changes
   - Decide MAJOR, MINOR, or PATCH based on rules above
   - Example: New feature → MINOR bump (1.11.2 → 1.12.0)

2. **Update Version Numbers**
   - Create new branch: `git checkout -b release/vX.Y.Z`
   - Update `tagger` script: `__version__ = "X.Y.Z"`
   - Update `setup.py`: `version="X.Y.Z"`
   - Commit: `git commit -m "chore: bump version to X.Y.Z"`
   - Push and create PR
   - Merge after CI passes

3. **Create Git Tag and GitHub Release**
   - After version bump PR is merged:
   - Create tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
   - Tag name MUST exactly match version (e.g., `v1.12.0` for version `1.12.0`)
   - **NO pre-release suffixes** (no `-pr34`, `-beta`, `-rc1`, etc.)
   - Create GitHub release: `gh release create vX.Y.Z --title "vX.Y.Z - Description" --notes "..."`

4. **Update Homebrew Formula**
   - **REQUIRED for every version bump**
   - Create new branch: `git checkout -b formula/vX.Y.Z`
   - Update `tagger.rb`:
     - URL to new tag: `url "https://github.com/delphinus/homebrew-tagger/archive/refs/tags/vX.Y.Z.tar.gz"`
     - Calculate SHA256: `curl -sL <URL> | shasum -a 256`
     - Update `sha256` field
   - Commit: `git commit -m "chore: update formula to vX.Y.Z"`
   - Push and create PR
   - Test formula installation locally: `brew reinstall --build-from-source ./tagger.rb`
   - Merge after CI passes

### Forbidden Practices

❌ **NEVER do these:**
- **Delete Git tags** (once pushed, tags are immutable - create new versions instead)
- Use pre-release suffixes in production tags (`v1.12.0-pr34`, `v1.12.0-beta`)
- Create tags that don't match code version
- Skip Homebrew formula updates
- Bump version before merging PR
- Create releases without corresponding version bump

✓ **ALWAYS do these:**
- Bump version AFTER merging feature/fix PR
- Match versions exactly across all files
- Create clean tags without suffixes (e.g., `v1.12.0`)
- Update Homebrew formula for every version
- Test formula installation before releasing

### Release Naming Convention

**Format:**
- Git tag: `vX.Y.Z` (exact match with version, NO suffixes)
- Release title: `vX.Y.Z - Brief Description`

**Examples:**
- ✓ Tag: `v1.12.0`, Title: `v1.12.0 - Music Recognition with AcoustID`
- ✓ Tag: `v1.11.3`, Title: `v1.11.3 - Bug Fixes`
- ❌ Tag: `v1.11.2-pr34` (WRONG: has suffix)
- ❌ Tag: `v1.11.2` when code version is `1.12.0` (WRONG: mismatch)

## Development Workflow

1. **Branch Creation**
   - Always create new branches from the latest default branch (main)
   - Pull latest changes before creating fix/feature branches
   - Example: `git checkout main && git pull && git checkout -b fix/issue-name`

2. **Pre-Push Testing**
   - Test locally as much as possible before pushing
   - Eliminate bugs locally to reduce CI failures
   - Run linting, type checking, and tests locally when available

3. **CI Monitoring**
   - Monitor CI checks every 30 seconds after pushing
   - Continue monitoring until all checks complete
   - Do not abandon PRs with pending CI checks
   - Use `gh pr checks <PR#> --watch` or periodic polling

4. **Post-CI Workflow**
   - After all CI checks pass: merge the PR
   - Follow "Release Workflow" above to create version bump and release
   - Clean up feature branch after merge (usually done automatically with --delete-branch)

## Testing Policy

**CRITICAL: NEVER SKIP TESTS**

❌ **ABSOLUTELY FORBIDDEN:**
- Skipping CI tests to "fix them later"
- Disabling test workflows temporarily
- Marking tests as "allowed to fail" without fixing them
- Merging PRs with failing tests
- Bypassing test requirements in any way
- Using `--no-verify` or similar flags to skip tests

✓ **ALWAYS REQUIRED:**
- All CI tests must pass before merging any PR
- All test failures must be investigated and fixed
- Tests must be run on all supported platforms
- New features must include appropriate tests
- Bug fixes should include regression tests

**Rationale:**
- Tests are the safety net that prevents regressions
- Skipping tests compromises code quality and reliability
- "Temporary" test skips often become permanent
- Failed tests indicate real problems that must be addressed

**If tests fail:**
1. Investigate the root cause immediately
2. Fix the underlying issue (not the test itself, unless the test is wrong)
3. Re-run tests to verify the fix
4. Only after all tests pass: proceed with merge

## Documentation Synchronization

**CRITICAL: Keep README and Man Page in Sync**

When making changes that affect user-facing features, command-line options, or behavior:

❌ **FORBIDDEN:**
- Updating only README or only man page
- Leaving documentation inconsistent between files
- Documenting features in one place but not the other
- Assuming "I'll update the other later"

✓ **REQUIRED:**
- **ALWAYS update BOTH README.md and man/tagger.1 together**
- Ensure examples are consistent across both documents
- Keep option descriptions identical
- Update version-specific information in both places
- Verify both files before committing

**Files to synchronize:**
- `README.md` - User-facing documentation in Markdown
- `man/tagger.1` - Comprehensive man page in groff format

**When to update both:**
- Adding new command-line options or flags
- Changing behavior of existing features
- Adding new features or modes
- Modifying examples or usage patterns
- Updating supported file formats
- Changing dependencies or requirements
- Fixing errors or clarifying instructions

**Verification checklist:**
1. Does README.md reflect the change?
2. Does man/tagger.1 reflect the change?
3. Are examples consistent between both?
4. Are all options documented in both?
5. Are version numbers updated in both (if applicable)?

**Rationale:**
- Users read different documentation sources
- Man pages are the canonical Unix documentation
- README is often the first thing users see
- Inconsistent docs cause confusion and support burden
- Both are installed and distributed with the package

## Automatic Release Workflow

**CRITICAL: Automate PR to Release Process**

When a PR is merged to main, automatically proceed through the entire release workflow unless specifically instructed otherwise.

✓ **REQUIRED: Complete Release Process**
1. Merge PR after all CI tests pass
2. Determine next version number (check latest release, increment appropriately)
3. Create git tag with version number (e.g., `v1.15.2`)
4. Push tag to GitHub
5. Create GitHub release with tag
6. Update Homebrew formula with new SHA256 if needed
7. Report completion to user

❌ **FORBIDDEN:**
- Waiting for user instruction to proceed with release
- Stopping after PR merge without releasing
- Skipping version tagging or release creation
- Asking "should I create a release?" (unless user explicitly said not to)

**When to skip automatic release:**
- User explicitly says "don't release yet"
- User says "merge but wait on release"
- PR is marked as work-in-progress or draft
- Commit message contains `[skip release]` or `[no release]`

**Release workflow steps:**
```bash
# 1. After PR merge, get latest version
gh release list --limit 1

# 2. Determine next version (patch/minor/major)
# Based on commit messages and changes

# 3. Create and push tag
git tag v1.X.Y
git push origin v1.X.Y

# 4. Create GitHub release
gh release create v1.X.Y --generate-notes

# 5. Update formula if needed (for Homebrew packages)
```

**Proactive status reporting:**
- Report when PR is merged
- Report when tag is created
- Report when release is published
- Don't wait to be asked "what's the status?"

## CI Monitoring Strategy

**CRITICAL: Reliable Continuous Monitoring**

Use continuous monitoring loops instead of one-time delayed checks for CI status.

✓ **REQUIRED: Continuous Loop Monitoring**
```bash
# Good: Continuous monitoring until tests complete
while true; do
    sleep 30
    gh pr checks <PR_NUMBER> || true
done
```

❌ **FORBIDDEN: One-Time Delayed Checks**
```bash
# Bad: Single check after delay (often fails)
sleep 120 && gh pr checks <PR_NUMBER>

# Bad: Using --watch (unreliable in background)
gh pr checks <PR_NUMBER> --watch
```

**Why continuous loops are better:**
- Survive temporary network issues
- Continue monitoring even if one check fails
- Provide regular status updates
- Can detect test completion at any time
- Don't depend on timing assumptions

**Monitoring loop parameters:**
- `sleep 30`: Check every 30 seconds (good balance)
- `|| true`: Don't exit loop if check command fails
- `while true`: Continue until manually stopped or tests complete

**When to stop monitoring:**
- All tests pass (successful)
- Any test fails (needs investigation)
- PR is closed or merged
- User requests to stop

**Implementation:**
```bash
# Start monitoring in background
while true; do
    sleep 30
    STATUS=$(gh pr checks <PR_NUMBER> 2>&1 || true)
    echo "$STATUS"
    if echo "$STATUS" | grep -q "All checks passed"; then
        echo "✓ All tests passed"
        break
    fi
    if echo "$STATUS" | grep -q "Some checks failed"; then
        echo "✗ Tests failed - investigation needed"
        break
    fi
done
```

**Rationale:**
- One-time delayed checks frequently fail due to timing issues
- CI runs can take variable amounts of time
- Network hiccups can cause single checks to fail
- Continuous monitoring is more resilient and reliable
