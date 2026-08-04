# Building Audio Fetch for Windows

This guide explains how to build the Audio Fetch desktop application as a standalone executable for Windows using PyInstaller.

## Prerequisites

### 1. Install Python 3.11+

Download and install Python from [python.org](https://www.python.org/downloads/windows/):

- **Recommended:** Python 3.11 or 3.12 (64-bit)
- **Important:** During installation, check "Add Python to PATH"
- Verify installation:
  ```cmd
  python --version
  python -m pip --version
  ```

### 2. Install Git (Optional)

Download from [git-scm.com](https://git-scm.com/download/win) if you plan to clone the repository.

### 3. Install Visual C++ Redistributables

Some dependencies require Visual C++ runtime libraries:

- Download from [Microsoft Support](https://support.microsoft.com/en-us/help/2977003/the-latest-supported-visual-c-downloads)
- Install both x64 versions (2015-2022)

## Setup Environment

### 1. Clone or Download the Repository

**Option A: Using Git**
```cmd
git clone https://github.com/yourusername/audio-fetch.git
cd audio-fetch
```

**Option B: Download ZIP**
- Download and extract the source code
- Open Command Prompt in the extracted folder

### 2. Create Virtual Environment

```cmd
python -m venv venv
venv\Scripts\activate
```

You should see `(venv)` in your command prompt.

### 3. Install Dependencies

```cmd
pip install --upgrade pip
pip install -r requirements-desktop.txt
```

This installs:
- FastAPI and Uvicorn (web server)
- PySide6 (Qt GUI framework)
- yt-dlp (YouTube downloader)
- PyInstaller (packaging tool)
- All other dependencies

**Note:** Installation may take 5-10 minutes due to PySide6's size (~500MB).

## Build the Executable

### 1. Clean Previous Builds (if any)

```cmd
rmdir /s /q build dist
```

### 2. Run PyInstaller

```cmd
pyinstaller audio-fetch.spec --clean
```

**Build time:** 2-5 minutes depending on your system.

**Expected output:**
```
Building Analysis...
Building PYZ...
Building PKG...
Building EXE...
Building EXE from EXE-00.toc completed successfully.
```

### 3. Locate the Executable

The built executable will be at:
```
dist\audio-fetch.exe
```

**Expected size:** ~250-300 MB (includes Python, Qt, and all dependencies)

## Test the Executable

### 1. Run from Command Line

```cmd
dist\audio-fetch.exe
```

**Expected behavior:**
- Console window appears (unless you set `console=False` in spec)
- Application window opens
- Server starts at `http://127.0.0.1:8000`

### 2. Test Download Functionality

1. Open the application
2. Paste a YouTube URL
3. Select audio quality and format
4. Click "Download"
5. Check the downloads folder for the output file

### 3. Test on Clean Windows System

**Important:** Test on a Windows machine WITHOUT Python installed to verify the executable is truly standalone.

Copy `dist\audio-fetch.exe` to another machine and run it.

## Troubleshooting

### Build Errors

**Error: `ModuleNotFoundError: No module named 'PyInstaller'`**
```cmd
pip install pyinstaller>=6.0.0
```

**Error: `Cannot find module 'PySide6'`**
```cmd
pip install PySide6>=6.6.0
```

**Error: Missing DLL files**
- Install Visual C++ Redistributables (see Prerequisites)
- Restart your terminal/IDE after installation

### Runtime Errors

**Error: `Qt platform plugin could not be initialized`**

This usually means Qt plugins are missing. Check the spec file includes:
```python
datas += collect_data_files('PySide6')
```

**Error: `Templates not found`**

Ensure `templates/` and `static/` directories are in the spec file:
```python
datas = [
    ('templates', 'templates'),
    ('static', 'static'),
]
```

**Error: `Server failed to start`**

Check Windows Firewall settings. The app needs to bind to localhost:8000.

### Performance Issues

**Build is slow:**
- Use an SSD if possible
- Close antivirus temporarily during build
- Expect 2-5 minutes build time

**Executable is large (>300MB):**
- This is normal for Qt-based applications
- PySide6 alone adds ~200MB
- Use UPX compression (enabled by default in spec)

## Distribution

### Create Installer (Optional)

Use [Inno Setup](https://jrsoftware.org/isinfo.php) to create a professional installer:

1. Download and install Inno Setup
2. Create an installer script (`.iss` file)
3. Include `dist\audio-fetch.exe`
4. Generate `Audio-Fetch-Setup.exe`

### Code Signing (Optional)

For production releases, consider code signing to avoid Windows SmartScreen warnings:

1. Obtain a code signing certificate
2. Sign the executable:
   ```cmd
   signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com dist\audio-fetch.exe
   ```

## Advanced Configuration

### Hide Console Window

Edit `audio-fetch.spec`, change:
```python
console=True,  # Change to False
```

**Note:** This hides debugging output. Use during final release only.

### Custom Icon

1. Create or obtain a `.ico` file (256x256 recommended)
2. Edit `audio-fetch.spec`:
   ```python
   icon='path/to/icon.ico',
   ```

### One-Folder Distribution

For faster startup, use folder distribution instead of single-file:

Edit `audio-fetch.spec`, uncomment the `COLLECT` section and comment out the single-file `EXE` configuration.

**Trade-off:**
- Faster startup time
- Larger distribution size (more files)
- Easier to debug

## Build Checklist

- [ ] Python 3.11+ installed and in PATH
- [ ] Visual C++ Redistributables installed
- [ ] Virtual environment activated
- [ ] Dependencies installed (`requirements-desktop.txt`)
- [ ] PyInstaller spec file present (`audio-fetch.spec`)
- [ ] Build completed without errors
- [ ] Executable created in `dist/`
- [ ] Tested on development machine
- [ ] Tested on clean Windows machine
- [ ] Downloads work correctly
- [ ] No missing DLL errors

## Support

For build issues:
- Check the PyInstaller documentation: https://pyinstaller.org/
- Review PySide6 documentation: https://doc.qt.io/qtforpython/
- Open an issue on the project repository

## Version History

- **v1.0** (2024): Initial Windows build support
