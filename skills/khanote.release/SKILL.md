# khanote.release

Publish a new version of khanote to PyPI and Homebrew.

## When to use

Run this skill when you want to release a new version of khanote.

## Steps

### 1. Bump version

Update the version string in `pyproject.toml`:

```toml
version = "X.Y.Z"
```

Also update `src/khanote/__init__.py` if it has a `__version__`.

### 2. Commit version bump

```bash
git add pyproject.toml src/khanote/__init__.py
git commit -m "chore: bump version to X.Y.Z"
git push
```

### 3. Create tag and GitHub Release

```bash
git tag vX.Y.Z
git push origin vX.Y.Z
```

Then create a release with `gh`:

```bash
gh release create vX.Y.Z --title "vX.Y.Z" --generate-notes
```

This triggers the `publish.yml` workflow which auto-publishes to PyPI.

### 4. Verify PyPI publish

```bash
gh run list --workflow=publish.yml --limit 1
pip install khanote==X.Y.Z --dry-run
```

### 5. Update Homebrew formula

Get the new sha256:

```bash
curl -sL "https://pypi.io/packages/source/k/khanote/khanote-X.Y.Z.tar.gz" | shasum -a 256
```

Then update `Formula/khanote.rb` in the `almost-khan/homebrew-tap` repo:
- Update `url` to the new version
- Update `sha256` to the new hash

Use the GitHub MCP tool `mcp__github__create_or_update_file` to push the update, or commit manually.

### 6. Verify Homebrew

```bash
brew update
brew upgrade khanote
```

## Notes

- PyPI publishing uses Trusted Publisher (no API token needed)
- The `publish.yml` workflow triggers automatically on GitHub Release
- Homebrew formula must be updated manually after each PyPI release
- Semver: patch for fixes, minor for features, major for breaking changes
