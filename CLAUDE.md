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
