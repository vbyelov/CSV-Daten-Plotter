# 📊 CSV Daten Plotter

## Kurzbeschreibung

CSV laden und mit MatPlotLib visualisieren

## Projektbeschreibung

Das Projekt **„CSV Daten Plotter"** ist ein Desktop-Tool zur schnellen
Visualisierung von CSV-Dateien.\
Mit einer einfachen grafischen Oberfläche (Tkinter) kann der Benutzer:

-   einen Ordner wählen und eine CSV-Datei laden,\
-   Spalten für die Darstellung auswählen,\
-   einen von fünf Diagrammtypen anzeigen (**Line, Pie, Histogram,
    Stacked Area, Polar**).

Die Daten werden mit **pandas** eingelesen und mit **matplotlib**
dargestellt.\
Der erzeugte Plot erscheint direkt im Fenster und kann zusätzlich als
**PNG** gespeichert werden.

Das Tool ist bewusst schlank und robust gehalten, um Daten schnell und
übersichtlich darzustellen.

------------------------------------------------------------------------

## Installation

``` bash
pip install pandas matplotlib
```

*(tkinter ist in Python Standard enthalten)*

------------------------------------------------------------------------

## Benutzung

1.  Programm starten:

    ``` bash
    python app.py
    ```

2.  Ordner mit CSV-Dateien auswählen.\

3.  Eine Datei aus der Liste laden.\

4.  Plot-Typ wählen (Line, Pie, Histogram, Stacked Area, Polar).\

5.  Spalten X/Y (bzw. numerische Spalten) auswählen.\

6.  Diagramm anzeigen lassen.\

7.  Optional: Diagramm als PNG speichern.

------------------------------------------------------------------------

## Bekannte Einschränkungen

-   Nur CSV-Dateien mit UTF-8 Kodierung werden unterstützt.\
-   Dateigröße sollte ≤ 50 MB sein.\
-   Für Stacked Area sind mindestens zwei numerische Spalten
    erforderlich.\
-   Für Polar-Plot müssen Kategorie- und Werte-Spalten verfügbar sein.\
-   Heatmap ist nur optional und nicht im Standardumfang enthalten.
