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
   - Create release if version was bumped
   - Update release page with release notes
   - Clean up feature branch after merge
