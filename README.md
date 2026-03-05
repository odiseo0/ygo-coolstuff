## coolstuffscrape

### Install and run

- **Install** (from PyPI when published): `pip install coolstuffscrape`
- **Install from source**: see [Install from source](#install-from-source) below.
- **Run**: `coolstuffscrape`  
  On first run the app creates the database and app data directory automatically.
- **Optional setup**: `coolstuffscrape init` — creates the database and app data dir only (no TUI). Use for scripting or CI.

### Install from source

Requires **Python 3.13 or newer**.

1. Clone the repo and go into the project directory:
   ```bash
   git clone https://github.com/your-username/scripting.git
   cd scripting
   ```
2. Install the package in editable mode using Python 3.13:
   ```bash
   pip install -e .
   ```
   If you have multiple Python versions (e.g. 3.11 and 3.13) and get an error like *"Package requires a different Python: 3.11.x not in '>=3.13'"*, use the 3.13 interpreter explicitly:
   - **Windows** (Python launcher): `py -3.13 -m pip install -e .`
   - **Windows** (full path): `"C:\Path\To\Python313\python.exe" -m pip install -e .`
   - **macOS/Linux**: `python3.13 -m pip install -e .` or `pip3.13 install -e .`
3. Run the app (with the same Python you used to install):
   - **Windows**: `py -3.13 -m coolstuffscrape` or just `coolstuffscrape` if that environment is active.
   - **macOS/Linux**: `coolstuffscrape` or `python3.13 -m coolstuffscrape`.

One-liner from repo (Windows, Python 3.13): `py -3.13 -m pip install -e . && py -3.13 -m coolstuffscrape`

### Overview
**coolstuffscrape** is a terminal user interface for managing card collections without constantly switching between browser tabs. Instead of searching on a website and juggling multiple pages, you stay inside this app, search for cards, and build collections that can later be exported into a template.

### flow
- **Search**: Press `s` to enter Search then press `/` to focus the search, then search for the card you want.
- **Browse results**: Use the arrow keys to move through the results table.
- **Add cards**: Press `space` to select a row and then press `a` to add that card to the current collection.
- **Adjust quantities**: Use `-` to decrease the quantity for the selected card, and use `Shift` + `+` to increase the quantity.

### Collections
- **Save collection**: Press `Ctrl+S` to save the current collection.
- **Rename or delete**: After saving, you can rename or delete collections from within the app.
- **Export**: Press `x` to export the collection.


### Imports
- **Import .ydk files**: Press `i` to import a `.ydk` file and turn it into a collection you can review and edit.

---

### Publishing (maintainers)

- **CI**: On push/PR to `main` or `master`, GitHub Actions builds the package and runs `coolstuffscrape init` to verify the install.
- **PyPI**: Creating a **GitHub Release** (tag + “Publish release”) triggers a workflow that builds and publishes to PyPI.

**Setup for PyPI:**

1. Create an API token at [pypi.org/manage/account/token/](https://pypi.org/manage/account/token/) (scope: entire account or just this project).
2. In the repo: **Settings → Secrets and variables → Actions** → **New repository secret** → name `PYPI_API_TOKEN`, value = the token.
3. To release: create a new **Release** (e.g. tag `v0.1.0`), publish it. The “Publish to PyPI” workflow will run and upload the package.

Optional: [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) lets you drop the token; remove the `password` input from the workflow and add the publisher on PyPI.
