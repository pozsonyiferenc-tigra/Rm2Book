# Rm2Book

Redmine projekt teljes exportálása AI-barát markdown formátumba. NotebookLM-be, Claude-ba vagy bármely AI eszközbe betölthető output.

## Funkciók

- **Teljes adatkinyerés**: hibajegyek, wiki (alprojektekkel), DMSF dokumentumok, hírek, verziók, időbejegyzések, fájlok, projekt info
- **Teljes történet**: minden journal entry, minden wiki verzió, időbélyeggel
- **AI-optimalizált output**: kompakt, strukturált markdown, minimális token-overhead
- **Automatikus darabolás**: `split_limit_words` alapján, issue-határokon (egy issue soha nem szakad ketté)
- **Moduláris**: csak a szükséges modulok futtatása
- **Konfigurálható tömörség**: verbose (önmagyarázó) vagy compact (1 betűs kódok) mód

## Telepítés

```bash
git clone <repo-url> Rm2Book
cd Rm2Book
pip install -r requirements.txt
```

Egyetlen függőség: `requests`

### Követelmények

- Python 3.9+
- Redmine API hozzáférés (API kulcs)

## Konfiguráció

```bash
cp config.example.json config.json
```

Szerkeszd a `config.json` fájlt:

```json
{
  "redmine_url": "https://redmine.example.com",
  "api_key": "your-api-key-here",
  "project_id": "my-project",
  "output_dir": "output",
  "modules": ["project", "versions", "files", "dmsf", "issues", "wiki", "news", "time_entries"],
  "compact_fields": false,
  "split_limit_words": 450000
}
```

### Konfigurációs mezők

| Mező | Kötelező | Alapértelmezett | Leírás |
|------|----------|-----------------|--------|
| `redmine_url` | igen | — | Redmine alap URL (perjel nélkül) |
| `api_key` | igen | — | Redmine API kulcs |
| `project_id` | igen | — | Projekt azonosító (az URL-ből: `/projects/ez-az-id`) |
| `output_dir` | nem | `output` | Kimeneti könyvtár |
| `modules` | nem | mind | Futtatandó modulok listája |
| `compact_fields` | nem | `false` | `true`: tömör 1 betűs kódok (P:, S:, A:), `false`: teljes szavak (Priority:, Status:, Assigned:) |
| `split_limit_words` | nem | `450000` | Issue fájl darabolási limit szószámban. Issue-határokon vág, egy issue soha nem szakad ketté. |

### API kulcs megszerzése

Redmine-ben: **Saját fiók** (jobb felső sarok) → jobb oldalsáv → **API hozzáférési kulcs** → "Megjelenítés" link.

Ha nem látod az API kulcs szekciót, az adminisztrátor nem engedélyezte az API hozzáférést.

## Használat

### Alap futtatás

```bash
python run.py
```

### CLI opciók

```bash
python run.py --config my_config.json    # Egyedi config fájl
python run.py --output-dir export/       # Kimeneti könyvtár felülírása
python run.py --modules issues wiki      # Csak megadott modulok futtatása
```

### Példa kimenet

```
Rm2Book - Exporting project: my-project
Redmine: https://redmine.example.com
Output: output/

[project]
  Members...
  Statuses...
  Priorities...
  -> Project overview done (12 members)

[issues]
  Building lookups...
  Fetching issues (all statuses)...
  -> 342 issues fetched.

[wiki]
  Fetching wiki index...
  12 wiki pages found
    HomePage... v8
    Architecture... v3

--- Writing output ---
  01_project_and_meta.md (1,245 words, 8,923 chars)
  02_issues.md (45,678 words, 312,456 chars)
  03_wiki.md (12,345 words, 89,012 chars)
  04_activity.md (3,456 words, 23,456 chars)

--- Done ---
  Files: 4
  Total words: 62,724
  Time: 45.2s
  Output: /path/to/output/
```

## Output fájlok

| Fájl | Tartalom |
|------|----------|
| `01_project_and_meta.md` | Projekt info, tagok, verziók, kategóriák, fájl metaadatok, DMSF dokumentumfa |
| `02_issues.md` | Minden hibajegy teljes változás-történettel (darabolva: `02_issues_001.md`, `_002.md`, stb.) |
| `03_wiki.md` | Minden wiki oldal (alprojektekből is, rekurzívan), minden korábbi verzió időbélyeggel |
| `04_activity.md` | Hírek, időbejegyzések |

Ha az issue-k össz szószáma meghaladja a `split_limit_words` értéket (alapért. 450K), automatikusan darabolódik: `02_issues_001.md`, `02_issues_002.md`, stb. A darabolás mindig issue-határokon történik — egy issue soha nem szakad ketté.

## Output formátum

### Issue (verbose mód, alapértelmezett)

```markdown
## ID:42 [Bug] Login button not working (Closed)
Priority:High | Assigned:Kiss János | Version:v2.0 | Category:Backend | 240115..240320 | Done:70%

A login gomb nem reagál kattintásra...

[240116 10:30 Kiss J.] Status:New→InProgress
[240117 14:22 Nagy É.] "Javítottam a click handler-t"
  Assigned:Kiss J.→Nagy É. | Estimated:→4h
📎 screenshot.png (Kiss J. 240115 245KB)
~ID:124 ~blocked:ID:100

---
```

### Issue (compact mód, `compact_fields: true`)

```markdown
## ID:42 [Bug] Login button not working (Closed)
P:High | A:Kiss János | V:v2.0 | C:Backend | 240115..240320 | Done:70%

A login gomb nem reagál kattintásra...

[240116 10:30 Kiss J.] S:New→InProgress
[240117 14:22 Nagy É.] "Javítottam a click handler-t"
  A:Kiss J.→Nagy É. | Est:→4h

---
```

Compact módban a fájl tetejére legenda kerül:
```
S=Status P=Priority A=Assigned V=Version C=Category T=Tracker
```

### Wiki (alprojektekkel)

```markdown
# Wiki (42 pages, 5 projects)

## PageTitle [my-project]
[v3 240320 Kiss J.] Aktuális tartalom...
[v2 240215 Nagy É.] Korábbi verzió tartalma...
[v1 231101 Kiss J.] Eredeti tartalom...

## OtherPage [sub-project-1]
[v1 240101 Kiss J.] Alprojekt wiki tartalom...
```

Minden verzió megjelenik, legfrissebb elöl, időbélyeggel és szerzővel. A projekt-azonosító szögletes zárójelben jelenik meg minden oldal fejlécében. Az alprojektek rekurzívan bejárásra kerülnek (teljes fa).

### DMSF dokumentumok

```markdown
## DMSF Documents

📁 Requirements/
  📎 spec.pdf v3 (Kiss J. 240315 1.2MB) "Updated requirements"
  📁 Archive/
    📎 old_spec.pdf (2 revisions)
      [v2 240201 Kiss J. 980KB] "Updated"
      [v1 231101 Kiss J. 900KB] "Initial"
```

Mappa struktúra behúzással, fájlok metaadatokkal és revízió-történettel. Ha a DMSF plugin nincs telepítve, a modul automatikusan kimarad.

### Projekt meta

```markdown
# Project: ProjectName
ID:project-id | Created:240115 | Public:yes

## Members
| Name | Roles |
|------|-------|
| Kiss János | Manager, Developer |

## Versions
v2.0 | Open | Due:240601 | "Release description"
```

### Activity (hírek + időbejegyzések)

```markdown
# News (5)
[240301 Kiss J.] "News title" Content here...

# Time entries (128)
[240301 Kiss J. ID:42 Dev 2.5h] "Implemented login fix"
```

## Formátum konvenciók

| Elem | Formátum | Példa |
|------|----------|-------|
| Dátum+idő | `YYMMDD HH:MM` | `240115 10:30` |
| Csak dátum | `YYMMDD` | `240115` |
| Időtartomány | `YYMMDD..YYMMDD` | `240115..240320` |
| Személynév (journal) | Rövidítve | `Kiss J.` |
| Személynév (meta/fejléc) | Teljes | `Kiss János` |
| Csatolmány | `📎 fájl (szerző dátum méret)` | `📎 spec.pdf (Kiss J. 240110 1.2MB)` |
| Kapcsolat | `~prefix:ID:szám` | `~blocked:ID:100` |
| Gyermek issue | `^ID:szám Subject` | `^ID:55 Fix login CSS` |
| Issue elválasztó | `---` | Vízszintes vonal minden issue után |
| Egyéni mező | `cf:Név:Érték` | `cf:Client:ACME` |
| Wiki oldal | `## Title [project-id]` | `## HomePage [BGA]` |
| DMSF mappa | `📁 Név/` | `📁 Requirements/` |
| DMSF fájl | `📎 fájl vN (szerző dátum méret) "leírás"` | `📎 spec.pdf v3 (Kiss J. 240315 1.2MB)` |

### Kapcsolat típusok

| Redmine | Output |
|---------|--------|
| relates | `~ID:szám` |
| blocks | `~blocks:ID:szám` |
| blocked by | `~blocked:ID:szám` |
| duplicates | `~dup:ID:szám` |
| precedes | `~precedes:ID:szám` |
| follows | `~follows:ID:szám` |

## Modulok

Minden modul külön ki-/bekapcsolható a `modules` config mezőben:

| Modul | Leírás | Output fájl |
|-------|--------|-------------|
| `project` | Projekt info, tagok, kategóriák, státuszok, prioritások | `01_project_and_meta.md` |
| `versions` | Verziók / mérföldkövek | `01_project_and_meta.md` |
| `files` | Feltöltött fájlok metaadatai | `01_project_and_meta.md` |
| `dmsf` | DMSF dokumentumfa + fájl metaadatok + revíziók | `01_project_and_meta.md` |
| `issues` | Hibajegyek + teljes változás-történet | `02_issues.md` |
| `wiki` | Wiki oldalak + minden korábbi verzió (alprojektekkel, rekurzív) | `03_wiki.md` |
| `news` | Projekt hírek | `04_activity.md` |
| `time_entries` | Időbejegyzések | `04_activity.md` |

## Projekt struktúra

```
Rm2Book/
├── run.py                        # CLI belépési pont
├── config.example.json           # Konfig sablon
├── requirements.txt              # Függőségek
├── CLAUDE.md                     # AI fejlesztési specifikáció
└── redmine_export/
    ├── __init__.py               # Segédfüggvények (fmt_date, short_name, stb.)
    ├── client.py                 # Redmine API kliens (paginálás, retry)
    ├── exporter.py               # Orkesztrátor (modulok futtatása, merge, darabolás)
    └── modules/
        ├── project.py            # Projekt info, tagok
        ├── versions.py           # Verziók
        ├── files.py              # Fájl metaadatok
        ├── issues.py             # Hibajegyek + history
        ├── wiki.py               # Wiki + verzió history (alprojektekkel)
        ├── dmsf.py               # DMSF dokumentumkezelő metaadatok
        ├── news.py               # Hírek
        └── time_entries.py       # Időbejegyzések
```

## Automatizált futtatás

A script egyetlen `python run.py` paranccsal indítható, ami bármilyen ütemezővel használható:

### Cron (Linux/macOS)

```bash
# Minden nap éjjel 2:00-kor
0 2 * * * cd /path/to/Rm2Book && python3 run.py >> /var/log/rm2book.log 2>&1
```

### Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["python", "run.py"]
```

```bash
docker build -t rm2book .
docker run -v $(pwd)/config.json:/app/config.json -v $(pwd)/output:/app/output rm2book
```

## NotebookLM limitek

- **Max 50 forrás** per notebook → a `split_limit_words`-szel szabályozható, hogy hány fájl keletkezzen
- **Max 500K szó** per forrás → alapértelmezett darabolás 450K szónál (biztonsági margó)
- Nagy projektnél (pl. 16K+ issue) akár 14+ issue fájl is keletkezhet — ilyenkor érdemes a limitet magasan tartani (450K)
- A verbose mód (~45KB extra 500 issue-nál) elhanyagolható overhead a limithez képest

## Hibaelhárítás

| Probléma | Megoldás |
|----------|---------|
| `Config file not found` | `cp config.example.json config.json` és töltsd ki |
| `Missing or placeholder value` | Írd be a valós Redmine URL-t, API kulcsot, projekt ID-t |
| `404` hiba modulnál | A projekt nem tartalmazza az adott modult (pl. wiki nincs engedélyezve) — a script átugorja |
| `403 Forbidden` | Az API kulcs nem rendelkezik elég jogosultsággal |
| Üres output | Ellenőrizd, hogy a `project_id` helyes-e (URL-ből: `/projects/ez-az-id`) |
| Túl nagy output fájl | Az automatikus darabolás kezeli, de csökkentheted a modulok számát |

## Licensz

MIT
