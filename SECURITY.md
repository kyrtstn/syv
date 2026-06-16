# Security Policy for syv ⚡

## Supported Versions

Currently, the `syv` daemon provides security updates and patches for the following major versions. Because `syv` strictly adheres to a **zero-dependency architecture**, our supply-chain attack surface is inherently minimal. 

We encourage all users to migrate to the `5.0.x Ultimate` architecture for the highest level of stability and CI/CD safety.

| Version | Supported          | Description |
| ------- | ------------------ | ----------- |
| 5.0.x   | :white_check_mark: | Active development and enterprise CI/CD standards. |
| 4.1.x   | :white_check_mark: | Legacy stable version. Critical security patches only. |
| 4.0.x   | :x:                | Unsupported. Please upgrade. |
| < 4.0   | :x:                | Unsupported. Please upgrade. |

## Reporting a Vulnerability
 
Security is a core tenet of the `syv` architecture. As a daemon that handles raw file system operations (I/O) and network requests (SSG scraping), we take potential attack vectors very seriously.

If you discover a vulnerability—particularly involving **Path Traversal** during file compression or **SSRF (Server-Side Request Forgery)** during the localhost scraping phase—we want to know about it immediately.

**🛑 CRITICAL: Please DO NOT open a public GitHub Issue for security vulnerabilities.**

### How to Report
Please report security issues using **GitHub Private Vulnerability Reporting**:
1. Go to the **Security** tab of the `syv` repository.
2. Click on **Advisories** in the left sidebar.
3. Click the **Report a vulnerability** button.
4. Provide a detailed explanation, including your OS environment, the specific `syv` command used, and a Proof of Concept (PoC) if possible.

### What to Expect
* **Acknowledgement:** We will acknowledge receipt of your vulnerability report within 48 hours.
* **Triage & Patch:** We will attempt to reproduce the issue and notify you of the severity. If verified, a patch will be developed using strictly standard Python libraries.
* **Release & Credit:** The patch will be pushed in the next immediate version bump. If you wish, you will be publicly credited in the GitHub Security Advisory and Release Notes for helping secure the `syv` ecosystem.
