# Publishing Taskra to PyPI

This project uses **Poetry** and **GitHub Actions** to automate version bumping and publishing to PyPI.

---

## Automated publishing workflow

### How it works
- When you **merge or push to the `main` branch**, GitHub Actions will:
  1. **Bump the patch version** in `pyproject.toml`
  2. **Commit** the new version and **create a git tag**
  3. **Build** the package
  4. **Publish** the package to PyPI

### Setup required
1. **Create a PyPI API token**:
   - Log in to [pypi.org](https://pypi.org)
   - Go to **Account settings > API tokens**
   - Create a new token (preferably scoped to this project)

2. **Add the token to GitHub repository secrets**:
   - Go to **GitHub repo > Settings > Secrets and variables > Actions**
   - Click **New repository secret**
   - Name: `PYPI_API_TOKEN`
   - Value: *paste your PyPI token*

3. **Enable workflow permissions**:
   - Go to **GitHub repo > Settings > Actions > General**
   - Under **Workflow permissions**, select **Read and write permissions**

---

## Manual publishing (alternative)

If you want to publish manually from your local machine:

1. **Set your PyPI token as an environment variable**:

```bash
export POETRY_PYPI_TOKEN_PYPI=your-pypi-token
```

2. **Run the Makefile target**:

```bash
make publish
```

This will:
- Bump the patch version
- Build the package
- Publish it to PyPI

---

## Notes
- The automated workflow bumps **patch** version by default. You can change this in `.github/workflows/publish.yml`.
- The commit message for version bump includes `[skip ci]` to avoid triggering another workflow run.
- Tags are created automatically for each release.

---

## Summary
- **Merge to `main`** → **Auto bump version + tag + publish to PyPI**
- **PyPI token stored securely in GitHub secrets**
- **Manual publish also supported via `make publish`**
