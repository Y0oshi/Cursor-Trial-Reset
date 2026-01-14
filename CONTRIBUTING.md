# Contributing to Cursor Trial Reset

First off, thanks for taking the time to contribute! 🎉

We welcome contributions from everyone. By participating in this project, you help make it better for the entire community.

## 📋 How to Contribute

### Reporting Bugs
If you find a bug or an issue where the reset doesn't work:
1. Check the [Issues](../../issues) tab to see if it has already been reported.
2. Open a new Issue with a descriptive title.
3. Include your **OS version** (Windows 10/11, macOS Sequoia, Ubuntu, etc.).
4. Include your **Cursor version**.
5. Describe exactly what happened (e.g., "Script ran successfully but trial still active").

### Suggesting Enhancements
- Have an idea for a new feature?
- Discovered a new fingerprinting method used by Cursor?
- Want to improve the CLI interface?

Open an issue and tag it as an **Enhancement**.

### Pull Requests
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/AmazingFeature`).
3. Make your changes.
4. Commit your changes (`git commit -m 'Add some AmazingFeature'`).
5. Push to the branch (`git push origin feature/AmazingFeature`).
6. Open a Pull Request.

## 💻 Coding Guidelines

- **Language**: Python 3.8+
- **Style**: Try to follow PEP 8 guidelines.
- **Imports**: Keep imports organized (standard library first, then third-party).
- **Cross-Platform**: Ensure your changes work on macOS, Windows, and Linux if possible. If a feature is OS-specific (like Registry edits), wrap it in a platform check.
- **No External Dependencies**: We aim to keep this tool dependency-free so users don't need `pip install`. Use standard libraries (`os`, `sys`, `json`, `shutil`, `ctypes`, etc.) whenever possible.

## ⚠️ Important Note

This tool is created for **educational purposes only**.
When contributing, please ensure you do not include any malicious code, telemetry, or data exfiltration mechanisms. All code must be transparent and open source.

---

Thanks!
**Y0oshi**
