# Rm2Book - Redmine to NotebookLM Export Tool

## Projekt célja
Redmine projektből MINDEN adatot (beleértve historikus adatokat) kinyerni AI-barát markdown formátumban, ami NotebookLM-be vagy bármely AI eszközbe betölthető.

## Architektúra

```
Rm2Book/
├── run.py                    # CLI belépési pont
├── config.example.json       # Konfig sablon
├── requirements.txt          # Függőségek
└── redmine_export/
    ├── __init__.py
    ├── client.py             # Redmine API kliens (paginálás, retry)
    ├── exporter.py           # Orkesztrátor
    └── modules/
        ├── __init__.py
        ├── project.py        # Projekt info, tagok
        ├── issues.py         # Hibajegyek + teljes history
        ├── wiki.py           # Wiki + verzió history
        ├── news.py           # Hírek
        ├── versions.py       # Verziók/mérföldkövek
        ├── time_entries.py   # Időbejegyzések
        └── files.py          # Fájl metaadatok
```

## Konvenciók

### Modul interfész
Minden modul egyetlen `export(client, project_id, config)` függvényt exportál, ami `dict[filename, content]`-et ad vissza.

### Output formátum
- Minél kevesebb fájl (a felhasználó más forrásokat is tölt NotebookLM-be)
- Cél: 3-5 markdown fájl, max ~7 ha nagyon nagy a projekt
- AI-optimalizált: strukturált fejlécek, táblázatok, idővonal, kereshető
- Textile tartalom változatlanul marad (az AI ugyanúgy érti, konverzió felesleges overhead)
- Nagy issue-set darabolása csak ha szükséges (fájlméret limit miatt)

### Nyelv
- Kód: angol változónevek, docstringek
- Output markdown: angol mezőkódok/struktúra, a tartalom (leírás, kommentek) marad az eredeti nyelven
- Felhasználói kommunikáció: magyar

### Technológia
- Python 3.9+
- Egyetlen külső dependency: `requests`
- Nincs async, egyszerű szinkron megoldás

## Eldöntött kérdések
- [x] Wiki verzió-történet: **MINDEN verziót** lekérni, időbélyeggel
- [x] NotebookLM source limit: **Minél kevesebb fájl** (3-5 db), mert más források is kellenek
- [x] Textile→Markdown konverzió: **Nem**, felesleges — az AI ugyanúgy érti a Textile-t
- [x] Csatolmányok: **Csak metaadat** (fájlnév, méret, feltöltő, dátum)
- [x] Több projekt: **Nem**, egyetlen projekt exportálása

## Output fájl struktúra (tervezett)

| Fájl | Tartalom |
|------|----------|
| `01_project_and_meta.md` | Projekt info, tagok, verziók, kategóriák, fájlok metaadatai |
| `02_issues.md` | Minden hibajegy teljes történettel (darabolva ha >500KB) |
| `03_wiki.md` | Minden wiki oldal, minden verzió időbélyeggel |
| `04_activity.md` | Hírek, időbejegyzések |

## Kompakt output formátum specifikáció

### Alapelvek
- Minimális overhead, maximális információsűrűség
- Teljes angol mezőnevek (Priority, Status, Assigned...) — legenda nem kell, önmagyarázó
- Tartalom eredeti nyelven marad
- Nincs felesleges ismétlődés (táblázat fejlécek, szekció nevek)
- Konfigurálható tömörség: `compact_fields: false` (verbose, alapértelmezett) vagy `true` (1 betűs kódok + legenda)

### Dátum formátum
`YYMMDD HH:MM` — év 2 karakter, nincs kötőjel, nincs másodperc
- `2024-01-15 10:30:22` → `240115 10:30`
- Dátum-tartomány: `240115..240320`
- Csak dátum (idő nélkül): `240115`

### Issue formátum

Fájl fejléc (egyszer):
```markdown
# Issues (342)

---
```

Egy issue (verbose mód, `compact_fields: false` — alapértelmezett):
```markdown
## #42 [Bug] Login button not working (Closed)
Priority:High | Assigned:Kiss János | Version:v2.0 | Category:Backend | 240115..240320 | Done:70%

A login gomb nem reagál kattintásra...

[240116 10:30 Kiss J.] Status:New→InProgress
[240117 14:22 Nagy É.] "Komment szövege natúran, ahogy a Redmine-ban van"
  Assigned:Kiss J.→Nagy É. | Estimated:→4h
📎 screenshot.png (Kiss J. 240115 245KB)
~#124 ~blocked:#100
```

Ugyanez compact módban (`compact_fields: true` — legenda a fájl tetején):
```markdown
## #42 [Bug] Login button not working (Closed)
P:High | A:Kiss János | V:v2.0 | C:Backend | 240115..240320 | Done:70%

A login gomb nem reagál kattintásra...

[240116 10:30 Kiss J.] S:New→InProgress
[240117 14:22 Nagy É.] "Komment szövege natúran, ahogy a Redmine-ban van"
  A:Kiss J.→Nagy É. | Est:→4h
📎 screenshot.png (Kiss J. 240115 245KB)
~#124 ~blocked:#100
```

Szabályok:
- Fejléc: `## #ID [Tracker] Subject (Status)`
- Metaadatok: egyetlen sor, `|`-vel elválasztva, csak nem-üres mezők
- Leírás: közvetlenül a meta sor után, eredeti nyelven
- Journal: `[YYMMDD HH:MM Név] mezőváltozások` — komment idézőjelben
- Komment alatti mezőváltozások: behúzással, egy sorban
- Csatolmány: `📎 fájlnév (szerző dátum méret)`
- Kapcsolatok: `~#ID` (relates), `~blocks:#ID`, `~blocked:#ID`, `~dup:#ID`
- Egyéni mezők: `cf:Mezőnév:Érték` a meta sorban ha van
- Gyermek issue: `^#ID Subject` (rövid, egy sor)
- Személynevek: journal-ban rövidítve (Kiss J.), fejlécben/meta-ban teljes

### Wiki formátum

```markdown
# Wiki (12 pages)

## PageTitle
[v3 240320 Kiss J.] Current content here...
[v2 240215 Nagy É.] Previous version content...
[v1 231101 Kiss J.] Initial content...
```

Szabályok:
- Oldalanként `## PageTitle`
- Minden verzió: `[vN YYMMDD Author]` prefix, aztán tartalom
- Legfrissebb verzió elöl
- Tartalom nyers Textile marad (AI ugyanúgy érti)

### Projekt/meta formátum

```markdown
# Project: ProjectName
ID:project-id | Created:240115 | Public:yes

Description here...

## Members
| Name | Roles |
|------|-------|
| Kiss János | Manager, Developer |

## Versions
v2.0 | Open | Due:240601 | "Release description"
v1.0 | Closed | 231215 | "First release"

## Files
📎 spec.pdf (Kiss J. 240110 1.2MB) "Requirements document"
```

### Activity formátum (news + time entries)

```markdown
# News (5)
[240301 Kiss J.] "News title" Content here...

# Time entries (128)
T=Tracker A=Activity
[240301 Kiss J. #42 Dev 2.5h] "Implemented login fix"
[240228 Nagy É. #43 Test 1.0h] "Tested registration"
```

## Nyitott kérdések
- [ ] Fájlméret limit: mekkora markdown fájlt fogad el a NotebookLM? (500K szó a dokumentált limit)
  - Futásidejű szószám-ellenőrzés + automatikus darabolás ha közelít a limithez
  - Alapértelmezett értékek kihagyása (pl. P:Normal nem kerül be)
  - Journal tömörítés: komment nélküli mezőváltozások egy sorban

## Config referencia

```json
{
  "redmine_url": "https://redmine.example.com",  // Kötelező
  "api_key": "YOUR_API_KEY",                      // Kötelező
  "project_id": "project-id",                     // Kötelező
  "output_dir": "output",                         // Alapértelmezett: "output"
  "modules": ["project", "versions", "files",     // Alapértelmezett: mind
               "issues", "wiki", "news",
               "time_entries"],
  "compact_fields": false                          // true: 1 betűs kódok + legenda
}
```
