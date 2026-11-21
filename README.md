# Data Sorter

A simple desktop app for sorting Excel and CSV files by one or more columns. Pick the columns, choose ascending or descending, and save the result. Dates are sorted as real dates, numbers as real numbers, and your column order never changes. Runs on **Windows** and **macOS**.

<!-- Add a screenshot: save it as docs/screenshot.png and uncomment the next line -->
<!-- ![Data Sorter screenshot](docs/screenshot.png) -->

## Features

- Opens `.xlsx`, `.xlsm`, `.xls` and `.csv` files (CSV with comma, semicolon, tab or pipe separators). Drag and drop works too.
- Multi-sheet workbooks: choose which sheet to sort.
- Sort by **one or many columns**, each **ascending or descending**. The top rule is the main sort, and the following rules break ties. Reorder rules with the arrow buttons.
- **Smart date sorting:** date columns are detected automatically and sorted chronologically, not alphabetically. A **Day first** option handles `03/04/2024` (3 April vs March 4).
- **Smart number sorting:** 10 comes after 9, including numbers stored as text in CSV files.
- Text sorts case-insensitively. Empty cells always go last.
- Preview the result before saving. Your original file is never modified.
- Original **column order is preserved**.

## Download (no Python needed)

Go to the [**Releases**](../../releases) page and download:

| Your computer | File |
|---|---|
| Windows | `DataSorter-windows.zip` |
| Mac (Apple Silicon: M1/M2/M3/M4) | `DataSorter-mac.zip` |

**Windows:** unzip the folder, open it and run `DataSorter.exe`. Keep the files together. Right-click `DataSorter.exe` → *Send to → Desktop (create shortcut)* for easy access.
**Mac:** unzip, then drag `DataSorter.app` to your Applications folder.

### First launch warnings (the app is unsigned)

- **Windows SmartScreen:** click **More info → Run anyway**.
- **macOS:** right-click the app → **Open**. If it is still blocked, go to *System Settings → Privacy & Security → Open Anyway*, or run this once in Terminal:
  ```bash
  xattr -cr /Applications/DataSorter.app
  ```

## How to use

1. Click **Open File…** (or drag a file into the window). Pick the sheet if the workbook has several.
2. Choose a column and **Ascending** or **Descending**.
3. Click **+ Add Sort Rule** to sort by more columns. Use ▲ ▼ to change priority and ✕ to remove a rule.
4. Check the **Date** box if a column holds dates (it ticks itself when it detects them). Tick **Day first** if your dates are `dd/mm/yyyy`.
5. Click **Sort** to preview the result. **Show Original** returns to the original order.
6. Click **Save As…** to write the sorted file as `.xlsx` or `.csv`.

> **Note:** when saving to Excel, colours, formulas and other cell formatting are not kept. The sorted data, column order, bold header, column widths and date formats are.

## Run from source

Requires **Python 3.10 or newer**.

```bash
git clone https://github.com/Thisaru-Sach/data-sorter.git
cd data-sorter
```

**Windows**
```bat
python -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
python main.py
```

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

You can also open a file directly: `python main.py path/to/file.xlsx`

Run the tests of the sorting logic with `python test_sorter.py`.

## Build the app yourself

PyInstaller cannot cross-compile, so build on the system you want the app for.

- **Windows:** double-click `build_windows.bat`. The app appears in `dist\DataSorter\DataSorter.exe`.
- **macOS:** run `bash build_mac.sh`. The app appears at `dist/DataSorter.app`.

### Automatic builds with GitHub Actions

The workflow in `.github/workflows/build.yml` builds both versions on GitHub's servers:

- **Run workflow** manually from the *Actions* tab, then download the results from the run page.
- **Publish a release:** push a version tag and the zips are attached to a new release automatically.
  ```bash
  git tag v1.0.0
  git push origin v1.0.0
  ```

The Mac build targets Apple Silicon. For Intel Macs, add an Intel macOS runner to the matrix in `build.yml`.

## Project structure

```
main.py                 App entry point
ui.py                   Window and widgets (PySide6)
sorter.py               Loading, date detection, sorting, saving (no GUI code)
test_sorter.py          Tests for the sorting logic
requirements.txt        Runtime dependencies
requirements-build.txt  Adds PyInstaller for building the app
build_windows.bat       One-click Windows build
build_mac.sh            macOS build
.github/workflows/      GitHub Actions build
```

Built with [PySide6](https://doc.qt.io/qtforpython/), [pandas](https://pandas.pydata.org/), [openpyxl](https://openpyxl.readthedocs.io/) and [PyInstaller](https://pyinstaller.org/).

## Troubleshooting

- **`pip.exe` was blocked by Device Guard / policy (Windows):** use `python -m pip install -r requirements.txt` instead of `pip install ...`.
- **Dates sort in the wrong order:** toggle the **Day first** box for that rule.
- **"Cannot save" error:** the target file is open in Excel. Close it and save again.
- **Old `.xls` file will not open:** make sure `xlrd` is installed (it is in `requirements.txt`), or re-save the file as `.xlsx`.

## License

Released under the [MIT License](LICENSE).