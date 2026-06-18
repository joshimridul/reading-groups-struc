#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_ROOT="${1:-/Users/mriduljoshi/Github/reading-groups-struc}"
ARCHIVE_DIR="$TARGET_ROOT/archive/legacy_root_entrypoints_2026-06-07_ability_migration"
STALE_INPUT_ARCHIVE="$TARGET_ROOT/archive/stale_paper_inputs"

if [[ ! -d "$TARGET_ROOT/.git" ]]; then
  echo "Target is not a git repository: $TARGET_ROOT" >&2
  exit 2
fi

mkdir -p "$ARCHIVE_DIR"
mkdir -p "$STALE_INPUT_ARCHIVE"

archive_if_present() {
  local rel="$1"
  local src="$TARGET_ROOT/$rel"
  if [[ -e "$src" ]]; then
    local base
    base="$(basename "$rel")"
    local dst="$ARCHIVE_DIR/$base"
    if [[ -e "$dst" ]]; then
      dst="$ARCHIVE_DIR/${base}.pre_migration"
    fi
    mv "$src" "$dst"
  fi
}

# Keep the root focused on the active three-country paper.
archive_if_present "main2.tex"
archive_if_present "main2.pdf"
archive_if_present "main_nigeria.tex"
archive_if_present "main_nigeria.pdf"
archive_if_present "main_3country_new.before_structural_framing_20260607.tex"

# Active paper source and bibliography.
rsync -a "$SOURCE_ROOT/main_3country_new.structural_edit.tex" \
  "$TARGET_ROOT/main_3country_new.tex"
rsync -a "$SOURCE_ROOT/bib.bib" "$TARGET_ROOT/bib.bib"
rsync -a "$SOURCE_ROOT/README.md" "$TARGET_ROOT/README.md"
rsync -a "$SOURCE_ROOT/.gitignore" "$TARGET_ROOT/.gitignore"
if [[ -e "$SOURCE_ROOT/build_paper.sh" ]]; then
  rsync -a "$SOURCE_ROOT/build_paper.sh" "$TARGET_ROOT/build_paper.sh"
fi
if [[ -e "$SOURCE_ROOT/run_all.sh" ]]; then
  rsync -a "$SOURCE_ROOT/run_all.sh" "$TARGET_ROOT/run_all.sh"
fi

# Active paper inputs and audit trail. Stale files are archived, not deleted.
rsync -a --delete --backup --backup-dir "$STALE_INPUT_ARCHIVE/stata_output" \
  --exclude '.DS_Store' "$SOURCE_ROOT/stata_output/" "$TARGET_ROOT/stata_output/"
rsync -a --delete --backup --backup-dir "$STALE_INPUT_ARCHIVE/structural_output" \
  --exclude '.DS_Store' "$SOURCE_ROOT/structural_output/" "$TARGET_ROOT/structural_output/"
rsync -a --exclude '.DS_Store' "$SOURCE_ROOT/paper_pipeline/" "$TARGET_ROOT/paper_pipeline/"
rsync -a --exclude '.DS_Store' "$SOURCE_ROOT/replication_audit/" "$TARGET_ROOT/replication_audit/"

# Analysis code and local data. Data are copied for local self-containment; the
# copied .gitignore keeps raw/clean data from being accidentally committed.
rsync -a --exclude '.DS_Store' "$SOURCE_ROOT/1_Do/" "$TARGET_ROOT/1_Do/"
rsync -a --exclude '.DS_Store' "$SOURCE_ROOT/2_Data/" "$TARGET_ROOT/2_Data/"
rsync -a --exclude '.DS_Store' "$SOURCE_ROOT/3_Python/" "$TARGET_ROOT/3_Python/"
rsync -a --exclude '.DS_Store' "$SOURCE_ROOT/4_Stata2/" "$TARGET_ROOT/4_Stata2/"

# Project notes and literature/data anchors used in the current paper work.
mkdir -p "$TARGET_ROOT/docs/notes" "$TARGET_ROOT/literature" "$TARGET_ROOT/data"
for rel in "HANDOVER_NIGERIA.md" "STRUCTURAL_RESULTS_NOTE.md"; do
  if [[ -e "$SOURCE_ROOT/$rel" ]]; then
    rsync -a "$SOURCE_ROOT/$rel" "$TARGET_ROOT/docs/notes/$rel"
  fi
done

for rel in \
  "ai23-802.pdf" \
  "VSC (Current WP).pdf" \
  "2011-peer-effects-teacher-incentives-and-the-impact-of-tracking-evidence-from-a-randomized-evaluation-in-kenya (1).pdf"
do
  if [[ -e "$SOURCE_ROOT/$rel" ]]; then
    rsync -a "$SOURCE_ROOT/$rel" "$TARGET_ROOT/literature/$rel"
  fi
done

if [[ -d "$SOURCE_ROOT/ddk data" ]]; then
  rsync -a --exclude '.DS_Store' "$SOURCE_ROOT/ddk data/" "$TARGET_ROOT/data/ddk/"
fi

if [[ -d "$SOURCE_ROOT/archive/main2_release_notes_2026-06-07" ]]; then
  mkdir -p "$TARGET_ROOT/archive"
  rsync -a --exclude '.DS_Store' \
    "$SOURCE_ROOT/archive/main2_release_notes_2026-06-07/" \
    "$TARGET_ROOT/archive/main2_release_notes_2026-06-07/"
fi

cat > "$ARCHIVE_DIR/MANIFEST.md" <<'MANIFEST'
# Legacy Root Entrypoints

Archived on 2026-06-07 during migration into the
Overleaf-linked `reading-groups-struc` repository.

The active root manuscript is now:

```text
main_3country_new.tex
```

Old root entrypoints/PDFs were moved here so the repository root is focused on
the three-country paper.
MANIFEST

find "$TARGET_ROOT" -name .DS_Store -type f -delete

echo "Migration complete: $TARGET_ROOT"
echo "Archived old root entrypoints in: $ARCHIVE_DIR"
