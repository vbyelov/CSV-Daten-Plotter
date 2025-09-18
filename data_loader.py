# data_loader.py
# ---------------------------------------------
# Einfache Lade- und Hilfsfunktionen für CSV-Dateien.
# Fokus: Lesbarkeit und Robustheit (für das Abschlussprojekt).
# ---------------------------------------------

import pandas as pd

def _detect_sep(sample):
    """
    Ermittelt ein wahrscheinliches Trennzeichen aus einer Textprobe.
    Sehr einfache Heuristik: prüft gängige Kandidaten.
    """
    candidates = [",", ";", "\t", "|", ":"]
    counts = {c: sample.count(c) for c in candidates}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","

def load_csv(path):
    """
    Liest eine CSV-Datei als DataFrame.
    - UTF-8
    - einfacher Separator-Check (Heuristik)
    - engine='python' um flexible Trennzeichen zu erlauben
    Wirft eine Exception mit verständlicher Nachricht, falls etwas schiefgeht.
    """
    try:
        # Kleine Probe lesen, um das Trennzeichen zu schätzen
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            sample = "".join([next(f, "") for _ in range(20)])

        sep = _detect_sep(sample)

        df = pd.read_csv(
            path,
            encoding="utf-8",
            sep=sep,
            engine="python"
        )

        # Optional: Whitespace in Spaltennamen entfernen
        df.columns = [c.strip() for c in df.columns]
        return df

    except FileNotFoundError:
        raise RuntimeError("Datei wurde nicht gefunden. Bitte Pfad prüfen.")
    except pd.errors.EmptyDataError:
        raise RuntimeError("Die Datei scheint leer zu sein oder hat kein gültiges CSV-Format.")
    except Exception as ex:
        raise RuntimeError(f"CSV konnte nicht geladen werden: {ex}")

def infer_columns(df):
    """
    Ermittelt einfache Spaltentypen:
    - 'numeric': numerische Spalten (int/float)
    - 'categorical': alle übrigen
    """
    numeric = df.select_dtypes(include=["number"]).columns.tolist()
    categorical = [c for c in df.columns if c not in numeric]
    return {"numeric": numeric, "categorical": categorical}

def coerce_numeric(series):
    """
    Versucht, eine Serie numerisch zu interpretieren.
    Nicht konvertierbare Werte werden zu NaN.
    Gut für Pie/Histogramm.
    """
    return pd.to_numeric(series, errors="coerce")
