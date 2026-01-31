# CoolStuffInc TUI Development Plan

## Goals
- Design Textual screens for search, results selection, collections, and imports.
- Support:
  - Search single/multiple cards and add to a collection
  - Tabular search results with selection
  - Import from .txt or .ydk
  - Persist collections (“recipes”) per-user in SQLite
  - Export collection to Excel template (final milestone)

## Current Starting Point (Updated)
- Textual UI refactor underway:
  - Root app + status bar: `src/cli/app.py`
  - Screens split: `src/cli/search_screen.py`, `src/cli/import_screen.py`, `src/cli/collections_screen.py`
- Scraper service refactor: `src/services/scraper.py`
- Usecases: `src/usecases/search_cards.py`, `src/usecases/collections.py`
- Models updated: `src/models/cards.py` includes stock and collection item
- DB layer in place: `src/models/db_models.py`
- Database file created: `db/card_database.db`
- UI plan in `docs/tui_plan.md`

## Requirements
- Python 3.13
- Existing deps: `rich`, `textual`, `httpx`, `beautifulsoup4`, `aiofiles`
- New deps:
  - `aiosqlite` for async DB access (added)
  - `openpyxl` for Excel template export (added, still unused)

## Architecture Plan
- **UI Layer (Textual)**
  - Screens: Home, Search, Results, Import, Collections (split into files)
  - Status bar + modes implemented
- **Domain Models**
  - Card listing + collection item (implemented)
  - Collection / Recipe (DB model exists)
  - User profile (pending)
- **Services**
  - Scraper service (implemented)
  - Import parsers (.txt + .ydk) (pending)
  - Collection repository (SQLite via aiosqlite) (partial, not wired)
  - Excel exporter (last)

## Task List (Updated)
- [x] Define UI screen flow and navigation map
- [x] Create Textual screen skeletons and routing
- [x] Implement search workflow (input -> scrape -> results) for single query
- [x] Build results table with row selection and add‑to‑collection
- [x] Add working collection panel (display + add + undo)
- [x] Add DB dependency and basic repository layer
- [ ] Create DB usecases (collections CRUD + items CRUD)
- [ ] Persist working collection to DB (save/load)
- [ ] Wire DB models into collections screen (load list + details)
- [ ] Implement quantity adjustments (+/-), remove, rename in working collection
- [ ] Add stronger “added row” highlight in results (row style, not only prefix)
- [ ] Add card image popup from results table
- [ ] Implement import parser for .txt and .ydk
- [ ] Wire import flow into UI (file list, preview, add all)
- [ ] Add error handling/loading states/empty states to UI
- [ ] Add smoke tests (scraper + collection + import)
- [ ] Export to Excel template (final milestone)

## Milestones
1. UI foundation: screens + navigation (done)
2. Search and results selection (mostly done)
3. Collections with persistence (DB layer ready, wiring pending)
4. Import features (pending)
5. Reliability + UX polish (pending)
6. Excel export (last)
