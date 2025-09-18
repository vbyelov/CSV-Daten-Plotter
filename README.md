# CSV Daten Plotter

Ein schlankes Desktop-Tool (Tkinter + Matplotlib + Pandas) zur **Visualisierung von CSV-Dateien**.  
Nutzer können eine CSV-Datei laden, Spalten auswählen, den Diagrammtyp bestimmen, Basis- und Plot-Statistiken einsehen und die erzeugten Diagramme als PNG speichern.

---

## Funktionen

- 📂 CSV-Import (UTF-8, automatische Trennzeichenerkennung).  
- 📊 Fünf Diagrammtypen:
  - Line
  - Pie
  - Histogramm
  - Stacked Area
  - Polar  
- 🧮 Statistik-Panel:
  - Nach dem Laden: Zeilen, Spalten, Anzahl numerischer/kategorischer Spalten.  
  - Nach dem Plotten: Typ-spezifische Kennzahlen (z. B. Mittelwert, Standardabweichung, Top-Kategorien).  
- 💾 Export des aktuellen Plots als PNG.  
- ❌ Verständliche Fehlermeldungen anstelle von Abstürzen.  

---

## Projektstruktur

- `app.py` – Hauptlogik: Dateiauswahl, Validierung, Plot-Erzeugung, Statistik, PNG-Speichern.  
- `ui_main.py` – Benutzeroberfläche (Tkinter-Layout, Buttons, Auswahllisten, Plot-Bereich, Statistik-Panel).  
- `data_loader.py` – CSV-Einlesen, Trennzeichenerkennung, Spaltentyp-Erkennung, numerische Konvertierung.  
- `plotter.py` – Reine Plot-Funktionen (Line, Pie, Histogramm, Stacked Area, Polar).  

---

## Voraussetzungen

- Python **≥ 3.10**  
- Bibliotheken:  
  - `pandas`  
  - `matplotlib`  
  - `tkinter` (in der Standardinstallation von Python enthalten; unter Linux ggf. separat installieren)  

Installation fehlender Pakete:

```bash
pip install pandas matplotlib
