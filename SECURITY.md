# Security policy

## Supported versions

Security fixes are currently applied to the latest development version on the default branch. The project is an early research prototype; no production or clinical deployment is supported.

## Reporting a vulnerability

Please do not publish exploitable vulnerability details in a public issue.

Use GitHub's private vulnerability reporting or contact the repository maintainers through the private contact mechanism exposed by GitHub. Include:

- affected file, function, and version/commit;
- a concise description of the security impact;
- minimal reproduction steps or a proof of concept that does not expose real patient or laboratory data;
- any suggested mitigation.

Do not include credentials, identifiable patient data, confidential laboratory records, or unapproved animal/human research data in a report.

## Scope

Potentially relevant issues include unsafe parsing of untrusted image files, path traversal or arbitrary file writes, dependency vulnerabilities, and accidental disclosure of sensitive data through logs or metadata.

The software is not designed for use as a medical device or clinical diagnostic system.
