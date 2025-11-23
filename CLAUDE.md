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
   - `tagger.rb`: Homebrew formula URL tag
   - All three must match for releases

2. **CI Version Check**
   - `.github/workflows/ci.yml` automatically verifies version consistency
   - Checks that `tagger` script and `setup.py` have matching versions

3. **Release Process**
   - Update version in BOTH `tagger` and `setup.py`
   - Commit and push to main
   - Create new tag: `git tag vX.Y.Z && git push origin vX.Y.Z`
   - Update Homebrew formula (`tagger.rb`) with new tag and SHA256
   - Create GitHub release

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
- Always create PRs for review before merging to main

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
