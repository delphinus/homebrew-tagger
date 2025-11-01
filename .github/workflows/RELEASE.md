# Release Process

This repository uses an automated release workflow that updates the Homebrew Formula and creates GitHub releases.

## Prerequisites

### 1. Create a Personal Access Token (PAT)

The release workflow needs to bypass branch protection to update the Formula directly on the main branch.

1. Go to GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click "Generate new token"
3. Configure the token:
   - **Token name**: `homebrew-tagger-release`
   - **Expiration**: Set an appropriate expiration (e.g., 90 days, 1 year)
   - **Repository access**: Only select repositories → Choose `homebrew-tagger`
   - **Permissions**:
     - Repository permissions:
       - **Contents**: Read and write
       - **Metadata**: Read-only (automatically selected)
4. Click "Generate token"
5. Copy the token (you won't be able to see it again!)

### 2. Add PAT to Repository Secrets

1. Go to your repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PAT_TOKEN`
4. Value: Paste the PAT you created
5. Click "Add secret"

## How to Release

### 1. Prepare the Release

Make sure all changes are merged to `main` and tests are passing.

### 2. Trigger the Release Workflow

1. Go to Actions tab in GitHub
2. Select "Release" workflow
3. Click "Run workflow"
4. Enter the version number (e.g., `1.2.6`)
   - Must follow semantic versioning: `MAJOR.MINOR.PATCH`
   - Must not already exist as a tag
5. Click "Run workflow"

### 3. What the Workflow Does

The automated workflow will:

1. ✅ Validate version format
2. ✅ Check if version already exists
3. ✅ Update `setup.py` with new version
4. ✅ Commit version bump to main
5. ✅ Create and push git tag `vX.Y.Z`
6. ✅ Create GitHub release with auto-generated notes
7. ✅ Download release tarball
8. ✅ Calculate SHA256 hash
9. ✅ Update `tagger.rb` (Homebrew Formula)
10. ✅ Commit and push Formula update to main

### 4. Verify the Release

After the workflow completes:

1. Check the GitHub release page: `https://github.com/delphinus/homebrew-tagger/releases`
2. Verify the Homebrew Formula was updated: `tagger.rb` should have the new version and SHA256
3. Test installation (optional):
   ```bash
   brew tap delphinus/delphinus
   brew install tagger
   tagger --help
   ```

## Version Numbering Guidelines

Follow [Semantic Versioning](https://semver.org/):

- **PATCH** (e.g., 1.2.5 → 1.2.6): Bug fixes, no new features
- **MINOR** (e.g., 1.2.6 → 1.3.0): New features, backward compatible
- **MAJOR** (e.g., 1.3.0 → 2.0.0): Breaking changes

## Troubleshooting

### Error: "refusing to allow a Personal Access Token to create or update workflow"

This means the PAT doesn't have the correct permissions. Make sure:
- The PAT has "Contents: Read and write" permission
- The PAT is added as `PAT_TOKEN` in repository secrets

### Error: "Version vX.Y.Z already exists"

The version tag already exists. Choose a different version number or delete the existing tag if it was created by mistake.

### Workflow fails at "Update Homebrew Formula"

Check if the Formula template needs updating. The workflow generates `tagger.rb` with hardcoded dependency URLs and hashes. These may need updating if dependencies change.

## Manual Release (Fallback)

If the automated workflow fails, you can release manually:

1. Update version in `setup.py`
2. Commit: `git commit -am "chore: bump version to X.Y.Z"`
3. Create tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
4. Push: `git push && git push --tags`
5. Create release on GitHub
6. Download tarball and calculate SHA256:
   ```bash
   curl -sL https://github.com/delphinus/homebrew-tagger/archive/refs/tags/vX.Y.Z.tar.gz | shasum -a 256
   ```
7. Update `tagger.rb` with new version and SHA256
8. Create PR for Formula update
9. Merge PR
