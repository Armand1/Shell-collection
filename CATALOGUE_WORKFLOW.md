# Shell Collection Catalogue — Workflow Notes

## Overview
The catalogue is a typed ring-binder. Each page contains 4 entries with fields:
Class, Family, Genus, Species, Describer, Locality, Date, Collector, Comments, Reference.

Pages are photographed as HEIC images and OCR'd into a staging CSV (`shell_catalogue.csv`),
then merged into the master file (`shell_collection_catalogue.csv`).

---

## Column Structure (master CSV)

| Column | Notes |
|--------|-------|
| Accession No | Sequential ID from original catalogue (e.g. 1, 2, 3 or 999, 1000...) |
| Class | As recorded in catalogue |
| Subclass | From WoRMS |
| Order | From WoRMS (formal order; blank if WoRMS assigns none) |
| Clade 2 | Original catalogue field — not yet updated to WoRMS |
| Family | Updated to WoRMS family name |
| Subfamily | As recorded |
| Genus | As recorded in catalogue |
| genus_WoRMs | WoRMS accepted genus |
| species | As recorded in catalogue |
| species_WoRMs | WoRMS accepted species epithet |
| describer_WoRMs | Authority from WoRMS accepted record |
| description_date_WoRMs | Year from WoRMS accepted record |
| Habitat | Collection context (e.g. Beach, Live, dredged) |
| Specific locality | Specific site (e.g. Jeffrey's Bay) |
| General locality | Region (e.g. Cape Province, British Columbia) |
| Country | Country |
| date_collected | ISO format YYYY-MM-DD (01 used as placeholder for missing day/month) |
| Collector | Collector name |
| Comments | Free text notes |
| Checked? | `ok` if user has verified uncertain OCR readings |
| WoRMs_note | WoRMS status or match notes |

---

## Workflow for Adding New Pages

### 1. Photograph & OCR
- Photograph pages as HEIC; convert to JPEG with: `sips -s format jpeg file.HEIC --out file.jpg -Z 1200`
- Claude reads the images and transcribes into a staging CSV
- Uncertain readings are flagged with notes in the `Notes` column
- User checks and corrects uncertain entries, marks them `ok` in `checked` column

### 2. Accession Numbers
- Use the **ID numbers as written in the catalogue** (not auto-generated sequential numbers)

### 3. Merge into Master CSV
- Map staging columns to master columns:
  - `Locality` → split into `Specific locality` / `General locality` / `Country`
  - `Comments` (Beach/Live) → `Habitat`
  - `Notes` → `WoRMs_note`
  - `checked` → `Checked?`
- `Clade 2`, `Subfamily` left blank unless present in catalogue

### 4. Dates
- Standardise to ISO `YYYY-MM-DD`
- Use `01` as placeholder for missing day or month (e.g. `Aug-84` → `1984-08-01`, `1975` → `1975-01-01`)

### 5. WoRMS Lookup (via REST API)
API base: `https://www.marinespecies.org/rest/`

For each Genus + species pair:
```
GET /AphiaRecordsByName/{name}?like=false&marine_only=false
```
- Use `valid_name` field for `genus_WoRMs` + `species_WoRMs`
- If status ≠ accepted, fetch valid record via `/AphiaRecordByAphiaID/{valid_AphiaID}`
- Parse `authority` field: split on last comma → describer + year
- Use `/AphiaClassificationByAphiaID/{AphiaID}` to extract `Subclass` and `Order` ranks

**Known taxonomy notes:**
- Cypraeidae genera are now split: *Cypraea* → *Naria*, *Cypraeovula*, *Erronea*, *Talostolida* etc.
- Triviidae: *Trivia* → *Triviella*, *Trivellona*
- Pyramidellidae (*Odostomia*, *Turbonilla*): WoRMS assigns no Order (leave blank)
- *Tachyrhynchus*: WoRMS order is `Caenogastropoda incertae sedis` — leave Order blank
- Family `Turridae` split: check against WoRMS (e.g. *Kurtzia* → Mangeliidae)
- Family `Marginellidae` split: check against WoRMS (e.g. *Granulina* → Granulinidae)

### 6. Push to GitHub
```bash
cd /tmp/Shell-collection
git pull          # always pull first to avoid conflicts
# ... make edits ...
git add shell_collection_catalogue.csv
git commit -m "Add catalogue entries [accession range]"
git push
```

---

## Existing Data Sources
- **Pages 1–3** (Accessions 1–12): Cypraeidae + Triviidae, South Africa & Philippines, collector M. Mullan / Carfel, 1975–1977
- **Accessions 999–1134**: Marine gastropods & bivalves, Trevor Channel / Barkley Sound, British Columbia, Canada, collector A.M. Leroi, 1983–1986
