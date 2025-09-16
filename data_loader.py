# data_loader.py (Kompakt-Version)
# Einfache Hilfsfunktionen zum Arbeiten mit CSV-Dateien.
# Ziel: maximal lesbarer, kurzer Code ohne komplexe Heuristiken.

import os
import pandas as pd


def is_csv_file(path):
    """True, wenn Pfad eine Datei mit Endung .csv ist."""
    return os.path.isfile(path) and path.lower().endswith(".csv")


def list_csv_files(folder):
    """Gibt alle CSV-Dateinamen im Ordner zurück (kein Rekurs)."""
    if not os.path.isdir(folder):
        return []
    return sorted([name for name in os.listdir(folder)
                   if is_csv_file(os.path.join(folder, name))])


def load_csv(path, sep=None):
    """
    Lädt eine CSV als DataFrame.
    Annahmen: UTF-8, Trennzeichen auto (sep=None).
    Rückgabe: (DataFrame, verwendetes_encoding)
    """
    df = pd.read_csv(path, encoding="utf-8", sep=sep, engine="python")
    return df, "utf-8"


def infer_columns(df):
    """
    Ermittelt einfache Spaltentypen:
    - 'numeric': numerische Spalten (int/float)
    - 'categorical': alle übrigen
    - 'datetime': hier bewusst leer (Datumserkennung erfolgt später beim Plotten)
    """
    numeric = df.select_dtypes(include=["number"]).columns.tolist()
    categorical = [c for c in df.columns if c not in numeric]
    return {"numeric": numeric, "datetime": [], "categorical": categorical}
