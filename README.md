# CSV Daten Plotter

Ein leichtgewichtiges Desktop-Tool zur Visualisierung von CSV-Dateien.  
Erstellt im Rahmen der Projektarbeit für den Python-Kurs.

## Kurzbeschreibung

Die Anwendung ermöglicht es, eine CSV-Datei zu laden, Spalten auszuwählen und verschiedene Diagrammtypen darzustellen.  
Zusätzlich werden Basis- und Plot-bezogene Statistiken berechnet und angezeigt.  
Visualisierung erfolgt mit `matplotlib`, GUI mit `tkinter`.

## Features

- Laden von CSV-Dateien (UTF-8, bis ~50 MB)  
- Auswahl von X- und Y-Spalten  
- Fünf Diagrammtypen: **Line, Pie, Histogram, Stacked Area, Polar**  
- Statistik-Panel mit:
  - Basisstatistik (Zeilen, Spalten, numerisch/kategorisch)
  - Plot-spezifische Kennzahlen (z. B. Mittelwert, Standardabweichung, Median)  
- Diagramm im Fenster anzeigen und als PNG speichern  
- Nutzerfreundliche Fehlermeldungen (kein Absturz, kein Traceback)  

## Installation

1. Python ≥ 3.10 installieren  
2. Benötigte Pakete installieren:
   ```bash
   pip install pandas matplotlib
