# Contributing to SentioGate

Thanks for your interest in improving SentioGate's open-source projects. This guide applies to every public
repository in the [SentioGate](https://github.com/SentioGate) organization that does not have its own
`CONTRIBUTING.md`.

By taking part you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## Ways to contribute

- **Report a bug**: open an issue with the **Bug report** template on the affected repository.
- **Suggest a feature**: open an issue with the **Feature request** template.
- **Improve the docs**: fixes to READMEs, examples and changelogs are always welcome.
- **Send a pull request**: for anything beyond a small fix, please open an issue first so we can agree on the
  approach before you spend time on it.

**Security issues are different**: never report them in a public issue or pull request. Follow the
[Security Policy](SECURITY.md) instead.

## Ground rules

- **Never commit secrets.** No real SentioGate API keys, provider keys, tokens or `.env` files in code, tests,
  issues, logs or screenshots. Tests use fake keys and mocked HTTP; keep it that way.
- **Keep the SDKs dependency-free.** Both client SDKs ship with zero runtime dependencies. Please do not add one
  without discussing it in an issue first.
- **Keep changes focused.** One logical change per pull request makes review faster.
- **Add or update tests** for any behaviour you change, and make sure the full test suite passes locally.
- **Update the docs and `CHANGELOG.md`** when you change public behaviour (new options, renamed methods, changed
  defaults or error handling).
- **Don't bump the version or publish.** Releases are cut by maintainers.

## Workflow

1. Fork the repository and create a branch from `main` (for example `fix/stream-timeout`).
2. Make your change, with tests.
3. Run the repository's test command (see below) and make sure it passes.
4. Commit with a clear message, for example `fix: handle empty SSE lines in stream()`.
5. Open a pull request against `main` and fill in the pull request template.

Continuous integration runs the tests on every pull request. A maintainer will review your pull request; please
respond to review comments and keep the branch up to date with `main`.

By contributing, you agree that your contributions are licensed under the license of the repository you are
contributing to (Apache-2.0 for the client SDKs).

## Repository guides

### sentiogate-js (`@sentiogate/sdk` on npm)

JavaScript / TypeScript client SDK. Plain ES modules with a CommonJS wrapper and hand-written type definitions; no
build step and no runtime dependencies.

- **Requirements:** Node.js 18 or later (CI tests Node 18, 20 and 22).
- **Layout:**
  - `src/index.js`: the SDK (ES module).
  - `src/index.cjs`: the CommonJS entry, which re-exports from `index.js`. Export anything new here too.
  - `src/index.d.ts`: TypeScript types. Keep them in step with `index.js`.
  - `test/*.test.js`: tests using the built-in `node:test` runner.
- **Run the tests:**

  ```bash
  git clone https://github.com/<your-username>/sentiogate-js.git
  cd sentiogate-js
  npm test            # runs: node --test test/*.test.js
  ```

  There are no dependencies to install.
- **Notes:** `VERSION` in `src/index.js` must match `version` in `package.json` (a test checks this). Maintainers
  update both when they cut a release.

### sentiogate-python (`sentiogate-python` on PyPI)

Python client SDK, standard library only.

- **Requirements:** Python 3.8 or later (CI tests 3.8 to 3.13).
- **Layout:**
  - `sentiogate/client.py`: the SDK.
  - `sentiogate/__init__.py`: public exports. Add anything new here too.
  - `tests/test_client.py`: tests using `unittest` with mocked HTTP.
- **Run the tests:**

  ```bash
  git clone https://github.com/<your-username>/sentiogate-python.git
  cd sentiogate-python
  python -m unittest discover -s tests -v
  ```

  No packages are needed to run the tests. To check that the package still builds:

  ```bash
  python -m pip install build twine
  python -m build
  twine check dist/*
  ```
- **Notes:** keep the package free of third-party runtime dependencies (`dependencies = []` in `pyproject.toml`) and
  keep the `py.typed` marker and type hints accurate. `VERSION` in `sentiogate/client.py` and `version` in
  `pyproject.toml` are updated by maintainers at release time.

### llm-routing-benchmarks

A small, offline synthetic demonstration script. It makes no network requests and does not measure real provider
latency; live metrics are on [sentiogate.app/benchmarks](https://sentiogate.app/benchmarks).

- **Requirements:** Python 3.10 or later.
- **Run it:**

  ```bash
  pip install -r requirements.txt
  python benchmark_runner.py --iterations 50
  ```
- **Notes:** contributions must keep the script offline and must not present its synthetic output as measurements
  of SentioGate or any provider.

### sentiogate.github.io

The developer hub at [sentiogate.github.io](https://sentiogate.github.io): a single static `index.html` with no build
step. Open it in a browser to preview your change; GitHub Pages deploys `main` automatically.

## Questions

For usage questions about the SentioGate API, see the [documentation](https://sentiogate.app/docs) first. If the docs
don't answer it, open an issue on the most relevant repository.
