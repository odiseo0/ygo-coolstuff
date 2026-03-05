## coolstuffscrape

### Install and run

- **Install** (from repo): `pip install .`  
  Or from PyPI (when published): `pip install coolstuffscrape`
- **Run**: `coolstuffscrape`  
  On first run the app creates the database and app data directory automatically.
- **Optional setup**: `coolstuffscrape init` — creates the database and app data dir only (no TUI). Use for scripting or CI.

One-liner from repo: `pip install . && coolstuffscrape`

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
