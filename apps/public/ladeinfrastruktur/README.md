# Standortplanung Schnellladeparks – Marimo-Notebook

Vorführ-Notebook für die Ringvorlesung „Einführung in die Wirtschaftswissenschaft“ (WS 2026/27), Block IT & Operations.
Zeigt, wie Wirtschaftsinformatik (Daten beschaffen, bereinigen, verknüpfen) und Operations (Versorgung messen, Optimierungsmodell) gemeinsam ein echtes Problem lösen.

## Starten

```bash
cd apps   # im Repo OM-lecture
uvx marimo run --sandbox ladeinfrastruktur_standortplanung.py     # Präsentationsmodus
uvx marimo edit --sandbox ladeinfrastruktur_standortplanung.py    # mit Code
```

Die Karten (folium) brauchen Internet für Kartenkacheln und Leaflet.

## Bedienung in der Vorlesung

- Folie 4: Schalter „Bereinigung anwenden“ – naiv 38.777 vs. bereinigt 40.320 Schnellladepunkte
- Folie 7: Gebiet (Umkreis Würzburg 60 km / Deutschland) und Entfernung R wählen
- Folie 9: Anzahl neuer Parks k; Würzburg rechnet sofort, Deutschland nach Klick auf „Optimieren“ (ca. 10 s)

## Daten (apps/public/ladeinfrastruktur/data)

- `ladesaeulenregister_2026-09-01.parquet` – Bundesnetzagentur, Ladesäulenregister, Stand 01.09.2026, relevante Spalten im Rohformat (Strings, inkl. Dezimalkomma und Mehrfachwerten)
  Quelle: https://www.bundesnetzagentur.de/DE/Fachthemen/ElektrizitaetundGas/E-Mobilitaet/DownloadundKontakt.html
- `ladesaeulenregister_kopf.txt` – die ersten 14 Zeilen der Original-CSV (für die Rohdaten-Folie)
- `zensus2022_bevoelkerung_1km.parquet` – Zensus 2022, Einwohner im 1-km-Gitter (EPSG:3035, plus lat/lon); Statistische Ämter des Bundes und der Länder, dl-de/by-2-0; aufbereitet über https://github.com/jslth/z22data

## Modell

Maximal Covering Location Problem auf 5-km-Gebieten mit unversorgter Bevölkerung, gelöst mit scipy.optimize.milp (HiGHS).
Abstände: Luftlinie. Vergleich mit Greedy-Heuristik auf Folie 10.

Für GitHub Pages (WASM) in OM-lecture: Ordner `public/ladeinfrastruktur` nach `apps/public/` kopieren und Datenpfade ggf. auf raw-GitHub-URLs umstellen (wie DataURLs in den OM-Notebooks).
