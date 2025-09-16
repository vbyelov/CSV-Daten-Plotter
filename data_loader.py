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


def load_csv(path):
    """
    CSV-Datei laden und als DataFrame zurückgeben.
    - Automatische Erkennung des Trennzeichens
    - Entfernt leere / 'Unnamed' Spalten
    """
    # CSV laden (engine='python' für flexible Trennung)
    df = pd.read_csv(path, sep=None, engine="python", encoding="utf-8")

    # Spalten, die komplett leer sind, entfernen
    df = df.dropna(axis=1, how="all")

    # Spaltennamen 'Unnamed: ...' entfernen (z. B. leere Index-Spalte)
    df = df.loc[:, ~df.columns.str.contains("^Unnamed")]

    return df


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
