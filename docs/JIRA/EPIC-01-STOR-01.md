# EPIC-01-STOR-01: Project Setup and Dependencies

**Epic**: [EPIC-01](EPIC-01.md) - Claude Usage Monitor v1.0  
**Status**: Not Started  
**Priority**: P0 (Blocker)  
**Estimated Effort**: 2 hours  
**Dependencies**: None  
**Assignee**: TBD

## Objective

Set up the Python development environment, install all required dependencies, and create the complete project directory structure for the Claude Usage Monitor tool.

## Requirements

### Functional Requirements
1. Python 3.8+ installation verified on Windows 11
2. Virtual environment created and activated
3. All core dependencies installed with pinned versions
4. Project directory structure created according to specifications
5. Git repository initialized (optional but recommended)

### Technical Requirements
1. **Python Version**: 3.8 or higher
2. **Package Manager**: pip (latest version)
3. **Virtual Environment**: venv or virtualenv
4. **Dependencies**:
   - `playwright==1.40.0`
   - `PyQt5==5.15.10`
   - `qdarktheme==2.1.0`
   - `atomicwrites==1.4.1`

## Acceptance Criteria

- [x] Python 3.8+ is installed and accessible via command line
- [x] Virtual environment created at project root
- [x] `requirements.txt` file created with all dependencies and pinned versions
- [x] All dependencies installed successfully in virtual environment
- [x] Playwright browsers installed (`playwright install chromium`)
- [x] Project directory structure created exactly as specified
- [x] Test imports work: `python -c "import playwright; import PyQt5; import qdarktheme; import atomicwrites"`
- [x] Git repository initialized with `.gitignore` for Python and virtual environment

## Implementation Steps

### Step 1: Verify Python Installation

```powershell
# Check Python version (must be 3.8+)
python --version

# If not installed or version too old, download from python.org
# Recommended: Python 3.11.x for Windows 11
```

### Step 2: Create Project Directory

```powershell
# Navigate to project root
cd d:\VSProj\ClaudeMonitor

# Verify you're in the correct directory
pwd
```

### Step 3: Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Upgrade pip to latest version
python -m pip install --upgrade pip
```

**Note**: If PowerShell execution policy blocks activation, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 4: Create requirements.txt

Create [`requirements.txt`](../../requirements.txt) with the following content:

```
# Web Scraping
playwright==1.40.0

# UI Framework
PyQt5==5.15.10
qdarktheme==2.1.0

# Data Storage
atomicwrites==1.4.1

# Development Dependencies (optional)
pytest==7.4.3
pytest-asyncio==0.21.1
```

### Step 5: Install Dependencies

```powershell
# Install all dependencies
pip install -r requirements.txt

# Install Playwright browsers (Chromium)
playwright install chromium

# Verify installations
python -c "import playwright; print('Playwright OK')"
python -c "import PyQt5; print('PyQt5 OK')"
python -c "import qdarktheme; print('qdarktheme OK')"
python -c "import atomicwrites; print('atomicwrites OK')"
```

### Step 6: Create Project Directory Structure

```powershell
# Create all directories
mkdir -p src/scraper
mkdir -p src/overlay
mkdir -p src/shared
mkdir -p data
mkdir -p browser-data
mkdir -p tests
mkdir -p docs/JIRA

# Create __init__.py files for Python packages
New-Item -ItemType File -Path "src/__init__.py"
New-Item -ItemType File -Path "src/scraper/__init__.py"
New-Item -ItemType File -Path "src/overlay/__init__.py"
New-Item -ItemType File -Path "src/shared/__init__.py"
New-Item -ItemType File -Path "tests/__init__.py"
```

**Expected Directory Structure**:
```
ClaudeMonitor/
├── venv/                      # Virtual environment (excluded from git)
├── src/
│   ├── __init__.py
│   ├── scraper/
│   │   └── __init__.py
│   ├── overlay/
│   │   └── __init__.py
│   ├── shared/
│   │   └── __init__.py
│   └── run_system.py          # To be created in STOR-07
├── data/                      # Runtime data directory
├── browser-data/              # Playwright persistent context
├── tests/
│   └── __init__.py
├── docs/
│   └── JIRA/
│       ├── EPIC-01.md
│       ├── EPIC-01-STOR-01.md (this file)
│       └── compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md
├── requirements.txt
├── .gitignore                 # To be created
└── README.md                  # To be created in STOR-11
```

### Step 7: Create .gitignore

Create [`.gitignore`](../../.gitignore) with the following content:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/
ENV/
.venv

# PyQt
*.qm

# Project specific
browser-data/
data/usage-data.json
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
desktop.ini

# Temporary files
*.tmp
*.bak
~*
```

### Step 8: Initialize Git Repository (Optional)

```powershell
# Initialize git
git init

# Add initial files
git add requirements.txt .gitignore docs/JIRA/*.md src/

# Initial commit
git commit -m "EPIC-01-STOR-01: Initial project setup with dependencies"
```

## Testing and Validation

### Validation Script

Create a temporary test script to verify the setup:

```python
# test_setup.py
"""Verify project setup is complete and all dependencies work."""

import sys
import importlib

def test_dependency(module_name):
    """Test if a module can be imported."""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} imported successfully")
        return True
    except ImportError as e:
        print(f"❌ {module_name} failed to import: {e}")
        return False

def main():
    print("Testing Project Setup...\n")
    
    # Test core dependencies
    dependencies = [
        "playwright",
        "PyQt5",
        "qdarktheme",
        "atomicwrites",
    ]
    
    results = [test_dependency(dep) for dep in dependencies]
    
    print(f"\nResults: {sum(results)}/{len(results)} dependencies OK")
    
    if all(results):
        print("\n✅ All dependencies installed correctly!")
        sys.exit(0)
    else:
        print("\n❌ Some dependencies failed. Check installation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

Run the validation:
```powershell
python test_setup.py
```

### Expected Output

```
Testing Project Setup...

✅ playwright imported successfully
✅ PyQt5 imported successfully
✅ qdarktheme imported successfully
✅ atomicwrites imported successfully

Results: 4/4 dependencies OK

✅ All dependencies installed correctly!
```

## Troubleshooting

### Issue: Python Version Too Old

**Symptom**: `python --version` shows < 3.8

**Solution**:
1. Download Python 3.11.x from https://www.python.org/downloads/
2. During installation, check "Add Python to PATH"
3. Restart PowerShell and verify: `python --version`

### Issue: Playwright Install Fails

**Symptom**: `playwright install chromium` fails with permission error

**Solution**:
```powershell
# Run PowerShell as Administrator
playwright install chromium

# Or install to user directory
playwright install --with-deps chromium
```

### Issue: PyQt5 Import Fails

**Symptom**: `ImportError: DLL load failed while importing QtCore`

**Solution**:
```powershell
# Install Visual C++ Redistributable
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe

# Or install PyQt5 binary wheel
pip install --force-reinstall PyQt5
```

### Issue: Virtual Environment Activation Blocked

**Symptom**: PowerShell script execution policy error

**Solution**:
```powershell
# Allow script execution for current user
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then retry activation
.\venv\Scripts\Activate.ps1
```

## File Locations

- **requirements.txt**: [`requirements.txt`](../../requirements.txt)
- **.gitignore**: [`.gitignore`](../../.gitignore)
- **Virtual Environment**: [`venv/`](../../venv/)
- **Source Directory**: [`src/`](../../src/)

## Dependencies for Subsequent Stories

This story **MUST** be completed before any other stories can begin, as it establishes:
1. Python environment
2. All required libraries
3. Project structure
4. Development workflow

**Blocks**: STOR-02, STOR-03, STOR-04, STOR-05, STOR-06, STOR-07, STOR-08, STOR-09, STOR-10, STOR-11

## Definition of Done

- [ ] Virtual environment created and activated
- [ ] All dependencies installed and verified
- [ ] Project directory structure matches specification
- [ ] Test script confirms all imports work
- [ ] `.gitignore` created
- [ ] Git repository initialized (optional)
- [ ] Documentation updated with any deviations or notes
- [ ] Story marked as DONE in EPIC-01.md

## References

- **Technical Specification**: Lines 1426-1436 in [`compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md`](compass_artifact_wf-218e8cf7-6f44-496a-b7bb-7af4c5f8be96_text_markdown.md:1426)
- **Playwright Installation**: https://playwright.dev/python/docs/intro
- **PyQt5 Installation**: https://www.riverbankcomputing.com/software/pyqt/download

---

**Created**: 2025-11-08  
**Last Updated**: 2025-11-08  
**Story Points**: 1  
**Actual Effort**: TBD