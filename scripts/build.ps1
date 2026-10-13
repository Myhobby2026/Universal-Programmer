$ErrorActionPreference = "Stop"
python -m PyInstaller --noconfirm --clean --name UniversalProgrammerStudio --windowed --paths . app/main.py
