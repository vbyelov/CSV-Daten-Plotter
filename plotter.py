# plotter.py
# Einfache Plot-Funktionen für das Projekt "CSV Daten Plotter".
# Ziel: Sehr gut lesbarer Code, wenige Abhängigkeiten, deutsche Kommentare.
# Matplotlib erstellt jeweils eine Figure, die an die GUI übergeben werden kann.

from __future__ import annotations
from typing import List, Optional

import numpy as np
import pandas as pd
from matplotlib.figure import Figure


# -------------------------------------------------------------
# Hilfsfunktionen
# -------------------------------------------------------------

def _new_figure(figsize=(8, 5)) -> Figure:
    """Erzeugt eine neue Matplotlib-Figure in einheitlicher Größe."""
    fig = Figure(figsize=figsize)
    return fig


def _require_columns(df: pd.DataFrame, cols: List[str]):
    """Prüft, ob alle Spalten im DataFrame vorhanden sind."""
    missing = [c for c in cols if c not in df.columns]
    if missing:
        raise ValueError(f"Spalte(n) fehlen: {', '.join(missing)}")


def _ensure_numeric(df: pd.DataFrame, cols: List[str]) -> pd.DataFrame:
    """Konvertiert die genannten Spalten (kopiert) in numerische Werte (errors='coerce')."""
    cpy = df.copy()
    for c in cols:
        cpy[c] = pd.to_numeric(cpy[c], errors="coerce")
    return cpy


# -------------------------------------------------------------
# Linien-Plot (Line)
# -------------------------------------------------------------

def plot_line(df: pd.DataFrame, x_col: str, y_cols: List[str], title: Optional[str] = None) -> Figure:
    """
    Einfacher Linien-Plot.
    - x_col: X-Achse (kann Datum, Kategorie oder numerisch sein)
    - y_cols: eine oder mehrere numerische Spalten
    """
    _require_columns(df, [x_col] + y_cols)

    # numerische Y-Spalten sicherstellen
    df_num = _ensure_numeric(df[[x_col] + y_cols], y_cols)

    fig = _new_figure()
    ax = fig.add_subplot(111)

    # Datum automatisch erkennen und hübsch formatieren
    x = df_num[x_col]
    try:
        x_parsed = pd.to_datetime(x, errors="raise")
        x = x_parsed
    except Exception:
        pass  # wenn nicht als Datum interpretierbar, einfach so lassen

    for y in y_cols:
        ax.plot(x, df_num[y], label=y)

    ax.set_xlabel(x_col)
    ax.set_ylabel("Wert")
    if title:
        ax.set_title(title)
    if len(y_cols) > 1:
        ax.legend(loc="best")
    ax.grid(True, linestyle=":", linewidth=0.5)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------
# Histogramm
# -------------------------------------------------------------

def plot_histogram(df: pd.DataFrame, cols: List[str], bins: int = 20, title: Optional[str] = None) -> Figure:
    """
    Histogramm für eine oder mehrere numerische Spalten.
    - cols: Liste numerischer Spalten
    - bins: Anzahl Klassen
    """
    _require_columns(df, cols)
    df_num = _ensure_numeric(df[cols], cols)

    fig = _new_figure()
    ax = fig.add_subplot(111)

    # NaN-Werte entfernen, sonst meckert matplotlib
    data = [df_num[c].dropna().values for c in cols]

    # mehrere Datensätze werden übereinander transparent angezeigt
    ax.hist(data, bins=bins, alpha=0.7, label=cols)

    ax.set_xlabel("Wert")
    ax.set_ylabel("Häufigkeit")
    if title:
        ax.set_title(title)
    if len(cols) > 1:
        ax.legend(loc="best")
    ax.grid(True, linestyle=":", linewidth=0.5)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------
# Kreisdiagramm (Pie)
# -------------------------------------------------------------

def plot_pie(df: pd.DataFrame, category_col: str, value_col: str, title: Optional[str] = None) -> Figure:
    """
    Kreisdiagramm aus Kategorien + Werten.
    Falls mehrere Zeilen pro Kategorie existieren, werden die Werte summiert.
    """
    _require_columns(df, [category_col, value_col])

    # gruppieren, damit jede Kategorie einmal vorkommt
    grouped = df.groupby(category_col, dropna=False)[value_col].sum().sort_values(ascending=False)

    # nur numerische Werte
    grouped = pd.to_numeric(grouped, errors="coerce").dropna()
    if grouped.empty:
        raise ValueError("Keine numerischen Werte für das Kreisdiagramm gefunden.")

    labels = grouped.index.astype(str).tolist()
    sizes = grouped.values

    fig = _new_figure()
    ax = fig.add_subplot(111)
    ax.pie(sizes, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.axis("equal")  # kreisrund
    if title:
        ax.set_title(title)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------
# Gestapeltes Flächendiagramm (Stacked Area)
# -------------------------------------------------------------

def plot_stacked_area(df: pd.DataFrame, x_col: str, y_cols: List[str], title: Optional[str] = None) -> Figure:
    """
    Gestapeltes Flächendiagramm über eine X-Achse (Zeit, Kategorie oder numerisch).
    - y_cols: mindestens zwei numerische Spalten sind sinnvoll
    """
    if len(y_cols) < 2:
        raise ValueError("Für Stacked Area bitte mindestens zwei numerische Spalten wählen.")

    _require_columns(df, [x_col] + y_cols)

    df_num = _ensure_numeric(df[[x_col] + y_cols], y_cols)

    # X ggf. in Datum umwandeln (für schönere Achse)
    x = df_num[x_col]
    try:
        x_parsed = pd.to_datetime(x, errors="raise")
        x = x_parsed
    except Exception:
        pass

    fig = _new_figure()
    ax = fig.add_subplot(111)

    y_data = [df_num[c].fillna(0.0).values for c in y_cols]
    ax.stackplot(x, *y_data, labels=y_cols)

    ax.set_xlabel(x_col)
    ax.set_ylabel("Wert")
    if title:
        ax.set_title(title)
    ax.legend(loc="upper left")
    ax.grid(True, linestyle=":", linewidth=0.5)
    fig.tight_layout()
    return fig


# -------------------------------------------------------------
# Polar-Plot (kategorisch -> Winkel, Werte -> Radius)
# -------------------------------------------------------------

def plot_polar(df: pd.DataFrame, category_col: str, value_col: str, title: Optional[str] = None) -> Figure:
    """
    Polar-Plot für Kategorien.
    Idee: Jede Kategorie erhält einen Winkel (gleichmäßig verteilt), der Wert ist der Radius.
    """
    _require_columns(df, [category_col, value_col])

    # ggf. aggregieren, damit jede Kategorie einmal vorkommt
    grouped = df.groupby(category_col, dropna=False)[value_col].sum()
    grouped = pd.to_numeric(grouped, errors="coerce").dropna()
    if grouped.empty:
        raise ValueError("Keine numerischen Werte für den Polar-Plot gefunden.")

    labels = grouped.index.astype(str).tolist()
    r = grouped.values.astype(float)

    # Winkel gleichmäßig über 0..2π verteilen und zum Schließen den ersten Punkt anhängen
    n = len(r)
    if n == 0:
        raise ValueError("Es wurden keine Kategorien gefunden.")

    theta = np.linspace(0.0, 2.0 * np.pi, num=n, endpoint=False)
    theta = np.append(theta, theta[0])
    r = np.append(r, r[0])

    fig = _new_figure()
    ax = fig.add_subplot(111, projection="polar")

    ax.plot(theta, r)
    ax.fill(theta, r, alpha=0.25)

    # Ticks mit Kategorien beschriften (ohne den duplizierten letzten Punkt)
    ax.set_xticks(np.linspace(0.0, 2.0 * np.pi, num=n, endpoint=False))
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticklabels([])  # optional: radialen Text ausblenden

    if title:
        ax.set_title(title, va="bottom")

    fig.tight_layout()
    return fig


# -------------------------------------------------------------
# Dispatcher (optional): einheitlicher Einstiegspunkt
# -------------------------------------------------------------

def make_plot(
    plot_type: str,
    df: pd.DataFrame,
    x_col: Optional[str] = None,
    y_cols: Optional[List[str]] = None,
    category_col: Optional[str] = None,
    value_col: Optional[str] = None,
    **kwargs,
) -> Figure:
    """
    Zentraler Einstieg: wählt anhand von plot_type die passende Funktion.
    Erwartete Werte:
      - "Line": x_col + y_cols
      - "Histogram": cols = y_cols
      - "Pie": category_col + value_col
      - "Stacked Area": x_col + y_cols
      - "Polar": category_col + value_col
    """
    pt = (plot_type or "").strip().lower()

    if pt == "line":
        if not x_col or not y_cols:
            raise ValueError("Für Line bitte X-Spalte und mindestens eine Y-Spalte wählen.")
        return plot_line(df, x_col, y_cols, title=kwargs.get("title"))

    elif pt == "histogram":
        if not y_cols:
            raise ValueError("Für Histogramm bitte mindestens eine numerische Spalte wählen.")
        return plot_histogram(df, y_cols, bins=kwargs.get("bins", 20), title=kwargs.get("title"))

    elif pt == "pie":
        if not category_col or not value_col:
            raise ValueError("Für Pie bitte Kategorie- und Werte-Spalte wählen.")
        return plot_pie(df, category_col, value_col, title=kwargs.get("title"))

    elif pt == "stacked area":
        if not x_col or not y_cols:
            raise ValueError("Für Stacked Area bitte X-Spalte und mindestens zwei Y-Spalten wählen.")
        return plot_stacked_area(df, x_col, y_cols, title=kwargs.get("title"))

    elif pt == "polar":
        if not category_col or not value_col:
            raise ValueError("Für Polar bitte Kategorie- und Werte-Spalte wählen.")
        return plot_polar(df, category_col, value_col, title=kwargs.get("title"))

    else:
        raise ValueError(f"Unbekannter Plot-Typ: {plot_type}")



#other plots