# ⚡ syv
**The Zero-Dependency Optimization Daemon (v5.1 Ultimate)**

[![Python 3.6+](https://img.shields.io/badge/python-3.6+-blue.svg)](https://www.python.org/downloads/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-0-brightgreen.svg)]()
[![Security Hardened](https://img.shields.io/badge/security-SSRF%20%7C%20Traversal%20Safe-red.svg)]()
[![Platform: Linux | macOS | Windows | Termux](https://img.shields.io/badge/platform-POSIX%20%7C%20NT-lightgrey.svg)]()
[![GitHub Repo stars](https://img.shields.io/github/stars/kyrtstn/syv?style=lightgrey)]()
[![Star Check](https://www.fakestarchecker.com/api/badge/kyrtstn/syv.svg)]()

`syv` is a hyper-lightweight, multi-threaded optimization engine designed to sit between your raw development code and your production web servers. By natively handling **Single Page Application (SPA) payload compression**, **automatic DOM cache-busting injection**, and **Static Site Generation (SSG) caching**, `syv` drastically reduces Time-To-First-Byte (TTFB) and network latency without the bloat of modern JS frameworks.

---

## 🧠 The Philosophy of `syv`

Modern web development suffers from dependency fatigue. Tools like Webpack, Vite, or Next.js are incredibly powerful, but they often require downloading gigabytes of `node_modules` just to perform basic file compression or routing. 

`syv` was built in defiance of this trend, strictly adhering to the following tenets:
1. **The Zero-Dependency Oath:** Written entirely in standard Python 3. No `pip install`, no `npm install`, no virtual environments. You drop the binary into your system, and it runs instantly.
2. **The UNIX Philosophy:** Do one thing, and do it perfectly. `syv` is not a web server. It is a file-generation middleware that generates mathematically hashed payloads and manifests for your actual server (Nginx, Express, FastAPI) to serve.
3. **Bare-Metal Performance:** By utilizing `concurrent.futures` for multi-threading and low-level `os.path` polling for file watching, it maximizes hardware utilization (from 8-core desktop CPUs to ARM-based Termux environments).
4. **Enterprise Reliability:** Built-in self-healing retries, granular POSIX exit codes, and actionable exception handling make `syv` a bulletproof, fault-tolerant addition to any CI/CD pipeline.

---

## ✨ Core Capabilities

### 1. Security Hardening & Pre-flight Validation *(New in v5.1)*
`syv` is built to withstand hostile environments and malicious inputs. The daemon includes strict validation layers:
* **SSRF Prevention:** The SSG scraper strictly validates that all target URLs are localhost-bound (`127.0.0.1` or `::1`), preventing Server-Side Request Forgery attacks.
* **Symlink & Path Traversal Blocking:** Refuses to follow symbolic links during cache removal and rejects manifest keys containing `../`, `/`, or `~` to prevent unauthorized file system access.
* **Pre-flight Checks:** Automatically validates directory read/write permissions and checks `shutil.disk_usage` before initiating massive multi-threaded I/O operations to prevent disk-full crashes.

### 2. Fault-Tolerance & Self-Healing *(New in v5.1)*
Network drops and memory spikes are a reality. `syv` handles them gracefully:
* **Exponential Backoff:** Network operations (like sitemap scraping) utilize a `@with_retry` decorator with exponential backoff to survive temporary server overloads.
* **Graceful Degradation:** If the multi-core `ThreadPoolExecutor` triggers a `MemoryError` on massive directories, `syv` automatically falls back to sequential processing instead of crashing.
* **Unicode Fallback Chain:** Reads legacy files using a smart decoding chain (`UTF-8` → `latin-1` → `cp1252`), preventing pipeline failures due to malformed characters.

### 3. Automatic DOM Cache-Busting Injection *(New in v5.1)*
Injecting hashed asset URLs into your HTML shouldn't require backend logic. After every `syv build`, the **DOM Rewriter** scans all `.html` files in your build directory and rewrites asset references in-place using the generated `build_manifest.json`.

**Before:**
```html
<script src="app.js"></script>
```
**After `syv build`:**
```html
<script src="app.js?v=e3b0c4"></script>
```

### 4. Multi-Core Payload Compression (SPA)
When dealing with hundreds of heavy JavaScript and CSS files, `syv` maps your build directory to an optimized thread pool, utilizing available CPU cores (capped dynamically to prevent resource exhaustion) to calculate MD5 hashes and generate `.gz` gzip streams simultaneously.

### 5. Live Watch Daemon (Developer Experience)
Instead of relying on heavy third-party filesystem event libraries, `syv watch` utilizes a highly optimized `os.path.getmtime` polling loop. It features a `MAX_WATCHED_FILES` limit (100,000 files) and periodic memory cleanup to ensure zero memory leaks during extended development sessions.

### 6. Dynamic API Freezing & Multi-Page SSG
`syv run update` acts as a localized web crawler. It automatically detects `/sitemap.xml` and utilizes multi-threading to concurrently scrape and freeze your dynamic backend into a flat `./syv_cache/` directory alongside a Time-To-Live (TTL) metadata manifest.

---

## 📂 Workspace Anatomy

When `syv` is initialized and running in your project, it manages your workspace efficiently without cluttering it. Here is how your project structure will look:

```text
.
├── syv                      # The core Zero-Dependency Python Daemon
├── syv.json                 # Daemon configuration (Generated by `syv init`)
├── installer/               
│   └── install.cmd          # Windows fast-installer & PATH injector
│   └── uninstall.cmd          # Windows fast-uninstaller & PATH uninjector
├── dist/                    # Target SPA Build Directory (Your frontend output)
│   ├── build_manifest.json  # Auto-generated MD5 version map
│   ├── index.html           # DOM-rewritten HTML (auto-injected by syv)
│   ├── js/
│   │   ├── app.js           # Raw JS asset
│   │   └── app.js.gz        # Multi-thread compressed gzip payload
│   └── css/
│       ├── style.css        # Raw CSS asset
│       └── style.css.gz     # Compressed payload
└── syv_cache/               # Local SSG Cache (Generated by `syv run update`)
    ├── manifest.json        # TTL metadata & generation stats
    ├── index.html           # Scraped root route
    └── dashboard/
        └── index.html       # Frozen dynamic endpoint
```

---

## 📦 Installation

Since `syv` is a standalone Python script, installation is simply making it executable and moving it to your system's PATH.

**For Linux / macOS / Termux:**
```bash
curl -O [https://raw.githubusercontent.com/kyrtstn/syv/main/syv](https://raw.githubusercontent.com/kyrtstn/syv/main/syv)
chmod +x syv
sudo mv syv /usr/local/bin/
```

**For Windows (CMD / PowerShell):**
`syv` is 100% Windows compatible (including native ANSI terminal aesthetics).

1. Clone the repo and run the installer:
   ```cmd
   installer\install.bat
   ```
2. Open a **new** terminal and verify:
   ```cmd
   syv help
   ```

---

## ⚙️ Configuration (`syv.json`)

`syv` respects a `syv.json` file placed in the project root. Generate a template using `syv init`.

```json
{
  "port": 3000,
  "ignore": ["node_modules", ".git", ".venv", "tests", "syv_cache"],
  "ttl": 3600,
  "silent_mode": false
}
```

---

## 🛠️ CLI Reference

### Global Utility
```bash
syv init                   # Generate default syv.json template
syv clean ./dist           # Purge .gz files, manifests, and local cache
syv build ./dist --dry-run # Simulate operations without disk I/O
```

### SPA Operations (Frontend Bundles)
```bash
syv build ./dist           # Multi-threaded build + automatic DOM injection
syv watch ./dist           # Initialize the live-reload daemon
syv build ./dist --debug   # Enable verbose, actionable execution logs
```

### SSG Operations (Backend Endpoints)
```bash
syv run update             # Scrapes default port (8080 or config port)
syv run update -p 5000     # Scrape specific port
syv force run update       # Bypass TTL checks and force hard rebuild
```

---

## 🤖 CI/CD & Strict Exit Codes

`syv` v5.1 features a highly structured exception hierarchy. It acts as a bulletproof CI/CD citizen by halting deployments on failure and returning granular POSIX exit codes to help automated runners diagnose the exact root cause.

| Exit Code | Classification | Description |
| :--- | :--- | :--- |
| `0` | **Success** | Execution completed flawlessly. |
| `1` | **Fatal Error** | General execution or unexpected thread failure. |
| `2` | **Config Error** | Invalid `syv.json` syntax or bad CLI parameters (e.g., invalid port). |
| `3` | **Network Error** | Connection timeouts, DNS failures, or completely dead routes. |
| `7` | **Security Error** | SSRF attempts, path traversals, or symlink violations detected. |
| `8` | **Resource Error** | System out of memory or thread explosion. |
| `13` | **File System Error** | Permission denied, disk full (`ENOSPC`), or missing directories. |

**Example GitHub Actions Pipeline:**
```yaml
name: syv Optimization Pipeline
on: [push]
jobs:
  build-and-optimize:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Compile Source Code
        run: npm run build
      - name: Optimize Payloads with syv
        run: |
          chmod +x ./syv
          ./syv build ./dist
      - name: Deploy to Production
        run: echo "Deploying highly optimized, secure payloads..."
```

---

## 📈 Star History

<a href="https://www.star-history.com/?repos=kyrtstn%2Fsyv&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=kyrtstn/syv&type=date&theme=dark&legend=bottom-right" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=kyrtstn/syv&type=date&legend=bottom-right" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=kyrtstn/syv&type=date&legend=bottom-right" />
 </picture>
</a>
