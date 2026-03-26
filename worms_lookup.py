#!/usr/bin/env python3
"""
WoRMS lookup for shell_collection_catalogue_merged.csv
Fills: genus_WoRMs, species_WoRMs, describer_WoRMs, description_date_WoRMs,
       Subclass, Order, WoRMs_note
Skips rows that already have genus_WoRMs populated.
"""

import csv, time, re, json, urllib.request, urllib.parse, sys

BASE = "https://www.marinespecies.org/rest"

def get(url):
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return None

def search_name(name):
    enc = urllib.parse.quote(name)
    return get(f"{BASE}/AphiaRecordsByName/{enc}?like=false&marine_only=false")

def get_by_id(aphia_id):
    return get(f"{BASE}/AphiaRecordByAphiaID/{aphia_id}")

def get_classification(aphia_id):
    return get(f"{BASE}/AphiaClassificationByAphiaID/{aphia_id}")

def parse_authority(authority):
    """Split 'Author, year' → (author, year). Returns ('','') if unparseable."""
    if not authority:
        return '', ''
    # Try last comma as separator
    m = re.match(r'^(.*),\s*(\d{4})\s*$', authority.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    # Try just a year at end
    m2 = re.match(r'^(.*)\s+(\d{4})\s*$', authority.strip())
    if m2:
        return m2.group(1).strip(), m2.group(2).strip()
    return authority.strip(), ''

def get_rank(classification, rank_name):
    """Walk classification tree to find a rank."""
    if not classification:
        return ''
    node = classification
    while node:
        if node.get('rank', '').lower() == rank_name.lower():
            return node.get('scientificname', '')
        node = node.get('child')
    return ''

def lookup(genus, species):
    """
    Returns dict with keys: genus_WoRMs, species_WoRMs, describer_WoRMs,
    description_date_WoRMs, Subclass, Order, WoRMs_note
    """
    result = {
        'genus_WoRMs': '', 'species_WoRMs': '', 'describer_WoRMs': '',
        'description_date_WoRMs': '', 'Subclass': '', 'Order': '', 'WoRMs_note': ''
    }

    if not genus or genus.strip() in ('', 'AVAILABLE'):
        result['WoRMs_note'] = 'no genus'
        return result

    # Build search name
    search = genus.strip()
    has_species = species and species.strip() not in ('', 'NA', 'sp', 'sp.')
    if has_species:
        search = f"{genus.strip()} {species.strip()}"

    records = search_name(search)
    time.sleep(0.3)

    if not records:
        # Try genus-only fallback if species search failed
        if has_species:
            records = search_name(genus.strip())
            time.sleep(0.3)
            if not records:
                result['WoRMs_note'] = 'no WoRMS match'
                return result
            result['WoRMs_note'] = f'species "{species}" not found; genus-only match'
            has_species = False
        else:
            result['WoRMs_note'] = 'no WoRMS match'
            return result

    # Pick best record: prefer status=accepted, else first
    rec = next((r for r in records if r.get('status') == 'accepted'), records[0])

    # If not accepted, follow valid_AphiaID
    status = rec.get('status', '')
    valid_id = rec.get('valid_AphiaID')
    aphia_id = rec.get('AphiaID')

    if status != 'accepted' and valid_id and valid_id != aphia_id:
        valid_rec = get_by_id(valid_id)
        time.sleep(0.3)
        if valid_rec:
            note_parts = [f"original status: {status}"]
            rec_genus = rec.get('genus', genus)
            rec_species = rec.get('species', species) if has_species else ''
            valid_genus = valid_rec.get('genus', '')
            valid_species = valid_rec.get('species', '')

            mismatches = []
            if rec_genus and valid_genus and rec_genus.lower() != valid_genus.lower():
                mismatches.append(f"genus: {rec_genus} → {valid_genus}")
            if has_species and rec_species and valid_species and rec_species.lower() != valid_species.lower():
                mismatches.append(f"species: {rec_species} → {valid_species}")
            if mismatches:
                note_parts.append('mismatch: ' + '; '.join(mismatches))

            result['WoRMs_note'] = '; '.join(note_parts)
            rec = valid_rec
        else:
            result['WoRMs_note'] = f'status: {status}; could not fetch valid record'
    else:
        if status != 'accepted':
            result['WoRMs_note'] = f'status: {status}'

    # Fill WoRMS name fields
    result['genus_WoRMs'] = rec.get('genus', '')
    if has_species:
        result['species_WoRMs'] = rec.get('species', '')

    authority = rec.get('authority', '')
    describer, year = parse_authority(authority)
    result['describer_WoRMs'] = describer
    result['description_date_WoRMs'] = year

    # Classification
    use_id = rec.get('AphiaID', aphia_id)
    if use_id:
        classif = get_classification(use_id)
        time.sleep(0.3)
        if classif:
            result['Subclass'] = get_rank(classif, 'Subclass')
            order = get_rank(classif, 'Order')
            # Handle incertae sedis
            if not order:
                order = get_rank(classif, 'Infraclass')
            result['Order'] = order

    return result

# ── Main ──────────────────────────────────────────────────────────────────────

in_path  = '/Users/armandleroi/Desktop/shell_collection_catalogue_merged.csv'
out_path = '/Users/armandleroi/Desktop/shell_collection_catalogue_merged.csv'

with open(in_path, encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

fieldnames = list(rows[0].keys())

to_process = [r for r in rows if not r.get('genus_WoRMs', '').strip()]
print(f"Rows needing WoRMS lookup: {len(to_process)}", flush=True)

for i, row in enumerate(rows):
    if row.get('genus_WoRMs', '').strip():
        continue  # already done

    genus   = row.get('Genus', '').strip()
    species = row.get('species', '').strip()

    idx = rows.index(row)
    print(f"[{i+1}/{len(to_process)}] {row['Accession No']:>6}  {genus} {species}", end='  ', flush=True)

    result = lookup(genus, species)

    # Only overwrite blank fields (don't clobber existing data)
    for col in ('genus_WoRMs', 'species_WoRMs', 'describer_WoRMs',
                'description_date_WoRMs', 'WoRMs_note'):
        if not row.get(col, '').strip():
            row[col] = result[col]

    # Subclass and Order: fill if blank
    if not row.get('Subclass', '').strip():
        row['Subclass'] = result['Subclass']
    if not row.get('Order', '').strip():
        row['Order'] = result['Order']

    print(f"→ {result['genus_WoRMs']} {result['species_WoRMs']}  [{result['WoRMs_note'] or 'ok'}]", flush=True)

    # Save progress every 25 rows
    if (i + 1) % 25 == 0:
        with open(out_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        print(f"  ── checkpoint saved ──", flush=True)

# Final save
with open(out_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nDone. Written to {out_path}")
