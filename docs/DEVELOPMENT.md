# syv ⚡ Development & Debugging Guide (v5.1 Ultimate)

This guide is for developers who want to modify the `syv` source code, add new features, or test changes locally before pushing to production. Since we do not rely on heavy testing frameworks like `pytest`, we utilize a manual, highly effective sandbox testing strategy.

## 🛠️ Local Environment Setup

Since `syv` relies entirely on Python's standard library, the setup is extremely simple and cross-platform.

1. **Prerequisites:** Ensure you have Python 3.6 or higher installed.
2. **Clone the repo:**
   ```bash
   git clone [https://github.com/kyrtstn/syv.git](https://github.com/kyrtstn/syv.git)
   cd syv
   ```
3. **Make it executable (POSIX - Linux/macOS/Termux):**
   ```bash
   chmod +x syv
   ```
4. **Windows Setup:**
   If developing on Windows CMD/PowerShell, run the installer (`installer\install.bat`) to inject `syv` into your local PATH.
   
5. **Run it locally:** Instead of installing it globally, run it directly from the folder during development using `./syv` (or just `syv` if using the `.bat` wrapper on Windows).
   ```bash
   ./syv help
   ```

---

## 🧪 Testing Your Changes (The Sandbox)

You don't need a complex React app or a live database to test `syv`. You can simulate the full SSG, SPA, and Security environments using basic terminal commands.

### 1. Testing SPA Mode & DOM Rewriter
1. Create a dummy frontend directory with heavy text files and a dummy HTML file:
   ```bash
   mkdir -p test_dist/js test_dist/css
   head -c 5000000 /dev/urandom | base64 > test_dist/js/app.js
   echo '<script src="js/app.js"></script>' > test_dist/index.html
   ```
2. Run the build command with the debug flag:
   ```bash
   ./syv build ./test_dist --debug
   ```
3. **Verify:** Check that `app.js.gz` was created, `build_manifest.json` contains the hash, and most importantly, `test_dist/index.html` was automatically rewritten to include the hash (e.g., `<script src="js/app.js?v=e3b0c442"></script>`).

### 2. Testing Security & Hardening (v5.1+)
We rely on strict pre-flight validation. Test the security layers manually:
1. **Test SSRF Protection:** Modify your `syv.json` or attempt to scrape an external site.
   ```bash
   # Create a sitemap with a malicious external link
   echo '<loc>[http://example.com/admin](http://example.com/admin)</loc>' > sitemap.xml
   ./syv run update
   ```
   *Expected:* The daemon should reject the URL, log a `SYVSSRFRiskError`, and gracefully fail.
2. **Test Symlink/Traversal Blocking:**
   Create a symbolic link pointing to a root directory or use `../` in a manifest, then run `syv clean`. The daemon must throw a `SecurityError` and refuse to follow the symlink.

### 3. Testing SSG Mode (HTML Scraper)
1. Open a new terminal tab and start a dummy Python web server:
   ```bash
   mkdir dummy_backend && cd dummy_backend
   echo "<h1>Hello from the simulated backend</h1>" > index.html
   python3 -m http.server 8080
   ```
2. Go back to your main `syv` terminal and run the scraper:
   ```bash
   ./syv run update -p 8080
   ```
3. **Verify:** Ensure `./syv_cache/index.html` and `./syv_cache/manifest.json` were created successfully.

### 4. Testing Multi-Page SSG (Sitemap Discovery)
1. In your `dummy_backend`, create a dummy `sitemap.xml`:
   ```bash
   echo '<urlset><url><loc>[http://127.0.0.1:8080/about.html](http://127.0.0.1:8080/about.html)</loc></url></urlset>' > sitemap.xml
   echo "<h1>About Page</h1>" > about.html
   ```
2. Run the update command (`./syv run update -p 8080`) and verify `syv_cache/about.html` is generated.

---

## 🧩 Extending the Router

If you are adding a new core command, you must integrate it using our structured error hierarchy.

1. **Write your core function:** Add your logic above the `# --- Router Logic ---` section.
2. **Implement Pre-flight Checks:** Always use `validate_directory_readable()` or `validate_config()` before performing operations.
3. **Update the `main()` block:**
   ```python
   elif command == "analyze":
       target_dir = args[1] if len(args) > 1 else "./dist"
       log_sys(f"Initializing deep analysis on {target_dir}...")
       # Call your new function here
       # analyze_payloads(target_dir)
   ```

---

## 📜 Coding Style & Engineering Guidelines

* **The Zero-Dependency Oath:** NEVER add external libraries via `pip`. Use standard library equivalents (`re` instead of `BeautifulSoup`).
* **Structured Exception Handling (v5.1+):** NEVER use generic `except Exception:` blocks to hide errors. Inherit from the `SYVException` base class. 
  * If a file cannot be read, raise `FileSystemError`.
  * If a network request fails, raise `NetworkError` or `SYVNetworkTimeoutError`.
  * Always provide a `recovery` string to help the user fix the issue (e.g., `recovery="chmod +w ./dist"`).
* **CI/CD Reliability (Exit Codes):** Do not use `sys.exit(1)` arbitrarily. The `SYVException` class handles exit codes automatically (e.g., Exit 2 for Config, Exit 7 for Security, Exit 13 for Filesystem). The router will catch the exception and exit with the correct POSIX code.
* **Thread Safety:** When modifying `compress_payloads` or `scrape_localhost`, ensure all heavy I/O operations remain inside the `ThreadPoolExecutor`. Handle `MemoryError` gracefully by falling back to sequential processing.

## 🎨 Terminal Aesthetic Standards

`syv` is designed for terminal hackers. Maintain the established color-coding structure.

* **`C_GREEN`** (`log_info`): Successful operations, completions, and positive states.
* **`C_CYAN`** (`log_sys`): System initialization, directory scanning, and neutral daemon states.
* **`C_ORANGE`** (`log_warn`): Non-fatal warnings or soft thread exceptions.
* **`C_MAGENTA`** (`log_debug`): Deep system telemetry (visible only with `--debug`).

### 🚨 The `log_error()` Function
For fatal crashes or caught `SYVException`s, always use `log_error`. It generates a structured, actionable tree output:
```python
log_error(
    category="CONFIG",
    message="Invalid port value",
    context={"port": raw_port_str},
    recovery="Specify a valid integer port (e.g., --port 8080)",
    exit_code=2
)
```
