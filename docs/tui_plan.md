# CoolStuffInc UI Plan (TUI Screens + Navigation)

## Visual Baseline
- Black background, white text
- Minimal accents (gray borders, dim text)
- No color scheme exploration yet

## Global Layout
- Top title bar: app title + runtime context (local/user)
- Main content area: screen-specific layout
- Bottom status bar (mode line): Vim/Emacs style

## Modes
- `NAV`: default, navigation between widgets/panels
- `INSERT`: text entry (search, rename, filters)
- `SELECT`: table/list selection (multi-select)

## Global Keybindings (Draft)
- `q` quit
- `Esc` back / exit modal / exit select
- `?` help overlay
- `/` focus search input (enter INSERT)
- `Tab` / `Shift+Tab` cycle focus
- `u` undo last collection change

## Status Bar Content (Always Visible)
- Left: mode (`NAV`, `INSERT`, `SELECT`)
- Center: breadcrumb (e.g., `Home > Search > Results`)
- Right: contextual hints (`Enter: open`, `a: add`, `u: undo`)

---

## Screen Map

### 1) Home / Welcome
- Purpose: entry point
- Content:
  - ASCII art (simple logo)
  - Quick actions: Search, Import, Collections
  - Recent collections (optional)
- Navigation:
  - `s` → Search
  - `i` → Import
  - `c` → Collections

### 2) Search (Input + Results)
- Layout:
  - Search input (top)
  - Filters (optional)
  - Results table (main)
  - Inline Working Collection panel (right)
- Behavior:
  - `Enter` in input triggers search
  - Results appear in table
- Status bar hints: `/` search, `Space` select, `a` add, `u` undo

### 3) Search Results Table
- Columns:
  - `Card Name`, `Code`, `Price`, `Rarity`, `Condition`, `Qty`
- Selection:
  - `Space` toggles row selection (enter SELECT)
  - `a` adds selected rows to collection
  - `+/-` adjust quantity
- Visual feedback:
  - Added rows get a highlight
  - Selected row gets focus highlight

### 4) Inline Working Collection (Panel)
- Shows current working collection while searching
- Actions:
  - `d` remove item
  - `e` rename collection
  - `Ctrl+s` save
- Total count shown at bottom

### 5) Collections (Saved)
- Layout:
  - Left list of collections
  - Right detail (items + quantities)
- Actions:
  - `Enter` load into working collection
  - `n` new
  - `r` rename
  - `d` delete

### 6) Import
- Purpose: load `.txt` or `.ydk`
- Layout:
  - File list (left)
  - Preview of parsed cards (right)
- Actions:
  - `Enter` import and go to results
  - `a` add all to collection

### 7) Collection (Dedicated View)
- Purpose: full-screen view for active collection
- Content:
  - Collection name
  - Items table (name/code/qty)
  - Summary line (count, estimated value later)
- Actions:
  - `d` remove
  - `e` rename
  - `Ctrl+s` save

### 8) Help Overlay
- Shortcuts + mode explanation
- Toggle with `?`

---

## Navigation Flow
- Home → Search → Results → Add to Collection → Save
- Home → Import → Results → Add to Collection → Save
- Home → Collections → Load → Edit → Save

---

## UI Feedback Rules
- When a card is added:
  - Row gets a visible highlight in results
  - Status bar shows `Added: <card name>`
- Undo:
  - `u` rolls back last add/remove
  - Status bar confirms `Undo: <card name>`

---

## Implementation Notes (For Later)
- Use Textual screens and widgets
- Keep status bar in root layout (not per screen)
- Inline collection panel should be togglable (`c`)

