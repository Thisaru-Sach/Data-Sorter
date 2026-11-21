# Data Sorter

Sort a CSV or Excel file by one or more columns (ascending/descending, with proper date sorting).

## Use the app
1. **Open File…** (or drag a file into the window). Choose a sheet if the workbook has several.
2. Pick a column and Ascending/Descending. **+ Add Sort Rule** for more columns; the top rule is the main sort, the next ones break ties. Use ▲ ▼ to reorder.
3. Date columns are detected automatically (the **Date** box ticks itself). Untick/tick it to override. **Day first** controls whether 03/04/2024 means 3 April or March 4.
4. **Sort** to preview, **Save As…** to write a new file. The original file is never changed.

Empty cells always end up last. Column order is never changed. Excel colours/formulas are not kept; the sorted data, column order, bold header, column widths and date formats are.

## Run from source (venv)
Windows:
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    python main.py

macOS:
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    python main.py

Check the logic: `python test_sorter.py`

## Build a normal app
PyInstaller cannot cross-compile: build on Windows for Windows, on a Mac for Mac.

- **Windows:** double-click `build_windows.bat` -> `dist\DataSorter\DataSorter.exe`.
  Share the whole `dist\DataSorter` folder (zip it). Right-click DataSorter.exe -> Send to -> Desktop (create shortcut) or pin to taskbar.
- **macOS:** `bash build_mac.sh` -> `dist/DataSorter.app`. Drag to Applications.

## Build both without owning a Mac (GitHub Actions)
1. Create a GitHub repo and push this folder.
2. Repo -> **Actions** -> "Build Data Sorter" -> **Run workflow**.
3. When it finishes, download `DataSorter-windows` and `DataSorter-mac` from the run page.

`macos-latest` builds for Apple Silicon (M1/M2/M3/M4) Macs. For Intel Macs, add an Intel macOS runner label to the matrix in `build.yml` (check GitHub's current runner list).

## First launch warnings (unsigned app)
- **Windows SmartScreen:** More info -> Run anyway.
- **macOS:** right-click the app -> Open. On newer macOS, if it is still blocked: System Settings -> Privacy & Security -> "Open Anyway", or run `xattr -cr /Applications/DataSorter.app` once.
