# Security Policy

Thank you for helping keep SentioGate and its users safe. This policy covers every public repository in the
[SentioGate](https://github.com/SentioGate) organization that does not have its own `SECURITY.md`.

## Supported versions

Security fixes are made against the latest release of each project. Please confirm the issue on the latest version
before reporting.

| Project | Package | Supported |
| --- | --- | --- |
| [sentiogate-js](https://github.com/SentioGate/sentiogate-js) | `@sentiogate/sdk` on npm | Latest published version |
| [sentiogate-python](https://github.com/SentioGate/sentiogate-python) | `sentiogate-python` on PyPI | Latest published version |
| [llm-routing-benchmarks](https://github.com/SentioGate/llm-routing-benchmarks) | n/a | `main` branch |
| [sentiogate.github.io](https://github.com/SentioGate/sentiogate.github.io) | n/a | `main` branch |

Older versions do not receive security fixes; upgrading to the latest version is the supported remediation.

## Reporting a vulnerability

**Please do not report security vulnerabilities through public GitHub issues, discussions or pull requests.**

Report them privately through GitHub's private vulnerability reporting:

1. Open the affected repository on GitHub and go to the **Security** tab.
2. Click **Report a vulnerability** to open a private security advisory draft.
3. Describe the issue (see below). Only you and the maintainers can see the report.

If you are not sure which repository is affected, report it on the repository that seems closest; we will move it
if needed.

Please include as much of the following as you can:

- The affected repository, package and version (or commit).
- The type of issue (for example: credential exposure, injection, authentication bypass, insecure default).
- Step-by-step instructions to reproduce it, and a minimal proof of concept if you have one.
- The impact you believe it has and how an attacker could use it.

**Never include real API keys, provider keys or other secrets in a report.** If a key may have been exposed,
rotate it first, then tell us about the exposure without sharing the key itself.

## What to expect

- We will acknowledge your report and keep you informed as we investigate.
- If the report is confirmed, we will work on a fix and coordinate the timing of public disclosure with you.
- We are happy to credit you in the published advisory once a fix is released, unless you prefer to stay anonymous.

Please give us a reasonable opportunity to address the issue before any public disclosure.

## Scope

This policy covers the code in SentioGate's public GitHub repositories (the client SDKs, the benchmark demo and the
developer hub). Issues with the hosted SentioGate service at [sentiogate.app](https://sentiogate.app) can be
reported the same way, on the repository closest to the problem.

Out of scope: reports that require a compromised user device, social engineering of SentioGate staff or users, and
denial-of-service through traffic volume.
