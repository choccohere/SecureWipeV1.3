# SecureWipe Industrialized

A robust, cross-platform data erasure utility for Windows and Linux.

## Features
- **Cross-Platform**: Native support for Windows (PowerShell/DiskPart) and Linux (dd/parted).
- **Dual Interface**: Modern GUI built with Tkinter and a robust Command Line Interface (CLI).
- **Industrialized Design**: Clean package structure, modular logic, and resource management.
- **Secure Erasure**: Support for multiple wipe patterns (Zeros, Ones).
- **Certificate Generation**: (In-progress) Automated erasure certificates in PDF format.

## Installation

1. Install Python 3.8+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### GUI Mode (Default)
```bash
python main.py
```

### CLI Mode
```bash
python main.py --cli
```

## Project Structure
- `src/secure_wipe/core`: Core wiping and disk detection logic.
- `src/secure_wipe/gui`: Tkinter GUI implementation.
- `src/secure_wipe/cli`: Interactive CLI implementation.
- `src/secure_wipe/assets`: Themes, icons, and logos.
- `src/secure_wipe/utils`: Shared utilities (authentication, PDF export).

## Security Note
This tool is designed to destroy data irreversibly. Use with extreme caution. Always double-check the target disk before confirming.
