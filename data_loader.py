# data_loader.py
# ---------------------------------------------
# Einfache Lade- und Hilfsfunktionen für CSV-Dateien.
# Fokus: Lesbarkeit und Robustheit (für das Abschlussprojekt).
# ---------------------------------------------

from __future__ import annotations  # nur für Zukunftssicherheit, schadet nicht
import pandas as pd
from typing import Dict, List  # nur Basis-Typen für Klarheit

def _detect_sep(sample: str) -> str:
    """
    Ermittelt ein wahrscheinliches Trennzeichen aus einer Textprobe.
    Sehr einfache Heuristik: prüft gängige Kandidaten.
    """
    candidates = [",", ";", "\t", "|", ":"]
    counts = {c: sample.count(c) for c in candidates}
    # Wähle das Zeichen mit den meisten Treffern
    best = max(counts, key=counts.get)
    # Falls wirklich keine Treffer, nimm Komma als Standard
    return best if counts[best] > 0 else ","

def load_csv(path: str) -> pd.DataFrame:
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
        # Allgemeine, aber freundliche Fehlermeldung
        raise RuntimeError(f"CSV konnte nicht geladen werden: {ex}")

def infer_columns(df: pd.DataFrame) -> Dict[str, List[str]]:
    """
    Ermittelt einfache Spaltentypen:
    - 'numeric': numerische Spalten (int/float)
    - 'categorical': alle übrigen
    Hinweis: Datumserkennung erfolgt nicht automatisch (bewusst einfach gehalten).
    """
    numeric = df.select_dtypes(include=["number"]).columns.tolist()
    categorical = [c for c in df.columns if c not in numeric]
    return {"numeric": numeric, "categorical": categorical}

def coerce_numeric(series: pd.Series) -> pd.Series:
    """
    Versucht, eine Serie numerisch zu interpretieren.
    Nicht konvertierbare Werte werden zu NaN.
    Gut für Pie/Histogramm, bevor man filtert/aggregiert.
    """
    return pd.to_numeric(series, errors="coerce")
