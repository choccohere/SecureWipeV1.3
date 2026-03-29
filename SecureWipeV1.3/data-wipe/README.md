# 🔐 SecureWipe Industrialized

## 📌 Overview

SecureWipe is a robust, cross-platform data erasure utility designed for secure and irreversible file deletion.

It supports both **Graphical User Interface (GUI)** and **Command Line Interface (CLI)**, making it suitable for beginners, developers, and system administrators.

Built with a modular and scalable architecture, SecureWipe ensures reliability, performance, and safe execution across environments.

---

## ✨ Features

* 🔐 **Secure Data Erasure** – Prevents recovery of deleted data
* 🖥️ **Dual Interface** – GUI (Tkinter) + CLI support
* 🌍 **Cross-Platform** – Works on Windows and Linux
* ⚡ **Industrial Design** – Clean, modular, and scalable codebase
* 🧠 **Smart Execution** – Handles GUI/CLI fallback automatically
* 🧾 **Certificate Generation (In Progress)** – PDF-based erasure reports
* 🧪 **Multiple Wipe Patterns** – Supports overwrite methods (Zeros, Ones)

---

## 🛠️ Tech Stack

* **Language:** Python
* **Libraries:** argparse, tkinter
* **System Tools:**

  * **Windows:** PowerShell, DiskPart
  * **Linux:** dd, parted

---

## 📂 Project Structure

```bash
DATA-WIPE/
│── src/
│   └── secure_wipe/
│       ├── core/        # Wiping & disk detection logic
│       ├── gui/         # Tkinter GUI
│       ├── cli/         # CLI interface
│       ├── assets/      # Themes, icons, logos
│       └── utils/       # Utilities (auth, PDF export)
│── main.py
│── README.md
│── requirements.txt
```

---

## ⚙️ Installation

### 1️⃣ Install Python

Make sure Python **3.8 or above** is installed.

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

### 🖥️ GUI Mode (Default)

```bash
python main.py
```

### 💻 CLI Mode

```bash
python main.py --cli
```

---

## 🎯 Use Cases

* Secure deletion of sensitive files
* Data sanitization before selling storage devices
* Privacy protection
* Enterprise-level disk wiping

---

## ⚠️ Security Warning

> This tool permanently destroys data and cannot be undone.
> Always verify the selected disk or file before proceeding.

---

## 🤝 Contributing

Contributions are welcome!
Feel free to fork the repository and submit a pull request.

---

## 📜 License

This project is licensed under the **MIT License**.

---

## 🙌 Author

**Satyam Panwar**
🔗 https://github.com/your-username
