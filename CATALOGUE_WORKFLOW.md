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
| `id` | Accession number from original catalogue (e.g. 1, 2, 3 or 999, 1000...) |
| `class` | From WoRMS; title case |
| `subclass` | From WoRMS; title case |
| `order` | From WoRMS; title case. `Incertae sedis` if WoRMS assigns none; `Anomalodesmata` for Septibranchia |
| `family` | From WoRMS; title case |
| `genus_original` | Genus as recorded in catalogue |
| `genus_WoRMS` | WoRMS accepted genus |
| `species_original` | Species epithet as recorded in catalogue |
| `species_WoRMS` | WoRMS accepted species epithet |
| `describer_WoRMs` | Describer from WoRMS accepted record; no initials, no brackets |
| `description_date_WoRMs` | Year of description from WoRMS |
| `habitat` | Collection context (e.g. Beach, Live, dredged) |
| `location_specific` | Specific site (e.g. Jeffrey's Bay) |
| `location_region` | Region (e.g. Cape Province, British Columbia) |
| `location_country` | Country |
| `date_collected` | ISO format YYYY-MM-DD (`01` as placeholder for missing day/month) |
| `collector` | Collector name |
| `comments` | Free text notes |
| `WoRMs_note` | WoRMS status, mismatches, or match notes |

Missing values: `NA` throughout.

---

## Workflow for Adding New Pages

### 1. Photograph & OCR
- Photograph pages as HEIC; convert to JPEG with: `sips -s format jpeg file.HEIC --out file.jpg -Z 1200`
- Claude reads the images and transcribes into a staging CSV
- Uncertain readings are flagged in `WoRMs_note`

### 2. Accession Numbers
- Use the **ID numbers as written in the catalogue** (strip `id_` prefix and leading zeros if sourced from legacy CSV)

### 3. Dates
- Standardise to ISO `YYYY-MM-DD`
- Use `01` as placeholder for missing day or month (e.g. `Aug-84` → `1984-08-01`, `1975` → `1975-01-01`)
- **Do not open in Excel** — it reformats dates to DD/MM/YYYY

### 4. WoRMS Lookup (via REST API)
API base: `https://www.marinespecies.org/rest/`

**Species-level lookup:**
```
GET /AphiaRecordsByName/{genus species}?like=false&marine_only=false
```
- If status ≠ accepted, fetch valid record via `/AphiaRecordByAphiaID/{valid_AphiaID}`
- `genus_WoRMS` and `species_WoRMS` from valid record's `genus` and `species` fields (or parse from `scientificname`)
- `describer_WoRMs`: from `valid_authority`; strip all brackets (round and square), remove initials (single capital letter + period)
- `description_date_WoRMs`: year parsed from `valid_authority`

**Higher taxonomy:**
```
GET /AphiaClassificationByAphiaID/{AphiaID}
```
- Walk classification tree for `class`, `subclass`, `order`, `family`
- Apply title case to all four fields; use `NA` if not found

**If name-search fails** (e.g. recently added or fossil taxa), look up by AphiaID directly:
```
GET /AphiaRecordByAphiaID/{AphiaID}
```

**Known taxonomy notes:**
- Cypraeidae genera split: *Cypraea* → *Naria*, *Cypraeovula*, *Erronea*, *Talostolida*, *Siphocypraea* etc.
- Triviidae: *Trivia* → *Triviella*, *Trivellona*
- Pyramidellidae (*Odostomia*, *Turbonilla*): WoRMS assigns no Order → use `Incertae sedis`
- *Tachyrhynchus*, *Opalia*, *Mesalia*: WoRMS `Caenogastropoda incertae sedis` → use `Incertae sedis`
- *Cuspidaria*: use `Anomalodesmata` (strictly a superorder; WoRMS assigns no formal Order)
- *Siphocypraea*, *Akleistostoma*, *Venericor*, *Stazzania*: extinct taxa not found by name search — use AphiaID
- Describer `Sowerby I / II / III` retained to distinguish the three authors

### 5. Push to GitHub
```bash
cd /tmp/Shell-collection
git pull          # always pull first to avoid conflicts
# ... make edits ...
git add shell_collection_catalogue.csv
git commit -m "Add catalogue entries [accession range]"
git push
```

---

## Current Data

| Range | Description |
|-------|-------------|
| 1–12 | Cypraeidae + Triviidae, South Africa & Philippines, 1975–1977 |
| 13–300 | Mixed gastropods + bivalves, South Africa, Portugal, Philippines, and worldwide |
| 999–1038 | Marine gastropods, bivalves, scaphopods — Trevor Channel / Barkley Sound, British Columbia, Canada, A.M. Leroi, 1983–1986 |
| 1092, 1130, 1132, 1134 | Additional Barkley Sound specimens |
| 1135–1256 | Mixed worldwide; includes fossil taxa (*Venericor*, *Akleistostoma*, *Stazzania*) |

**Total: 466 entries** as of March 2026. All entries have WoRMS-validated taxonomy.
