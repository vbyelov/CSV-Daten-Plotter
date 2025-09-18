# plotter.py
# ---------------------------------------------------------
# Reine Zeichenfunktionen für Matplotlib.
#
# ---------------------------------------------------------

import numpy as np
import pandas as pd
from matplotlib.axes import Axes

# -----------------------------
# Hilfsfunktionen (intern)
# -----------------------------

def _as_xy(df: pd.DataFrame, x_col: str):
    """
    Wandelt X-Spalte in einen x-Vektor um.
    - Zahlen/Datum: direkte Werte (bei Datum sortiert der Aufrufer ggf. vorher)
    - Kategorie/Strings: Positionen 0..n-1 + Labels (für Ticks)
    Rückgabe: (x_positions, x_labels oder None)

    Prepare X axis
    """
    x = df[x_col]
    if np.issubdtype(x.dtype, np.number):
        # numerisch: direkt verwenden, keine Labels nötig
        return x.values, None
    # alles andere behandeln wir als Kategorie/Text
    positions = np.arange(len(x))
    labels = x.astype(str).values
    return positions, labels

def _apply_xtick_labels(ax: Axes, labels):
    """Setzt X-Tick-Labels (für kategoriale X).
    Apply Labels for X-Tick-Labels.
    """
    ax.set_xticks(np.arange(len(labels)))
    ax.set_xticklabels(labels, rotation=45, ha="right")

def _ensure_numeric(df: pd.DataFrame, ys: list[str]) -> pd.DataFrame:
    """Erzwingt numerische Typen für Y-Spalten (nicht konvertierbares -> NaN).
    Make sure Ys are numbers and no NAN are present.
    """
    out = df.copy()
    for c in ys:
        out[c] = pd.to_numeric(out[c], errors="coerce")
    return out

# -----------------------------
# Öffentliche Plot-Funktionen
# -----------------------------

def plot_line(ax: Axes, df: pd.DataFrame, x: str, ys: list[str]) -> None:
    """Line-Plot: X Kategorie/Datum/Zahl; Y >= 1 numerisch."""
    if not ys:
        raise ValueError("Mindestens eine Y-Spalte auswählen (Line).")
    df = _ensure_numeric(df, ys)
    x_vals, x_labels = _as_xy(df, x)
    for col in ys:
        ax.plot(x_vals, df[col].values, marker="o", label=col)
    if x_labels is not None:
        _apply_xtick_labels(ax, x_labels)
    ax.set_xlabel(x)
    ax.set_ylabel("Wert")
    ax.set_title("Line")
    ax.legend()
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

def plot_stacked_area(ax: Axes, df: pd.DataFrame, x: str, ys: list[str]) -> None:
    """Stacked Area: X Kategorie/Index/Datum; Y >= 1 (besser >=2) numerisch."""
    if len(ys) < 1:
        raise ValueError("Für Stacked Area bitte mindestens eine (besser zwei) Y-Spalten wählen.")
    df = _ensure_numeric(df, ys)
    x_vals, x_labels = _as_xy(df, x)
    y_arrays = [df[col].fillna(0).values for col in ys]
    ax.stackplot(x_vals, *y_arrays, labels=ys, step=None)
    if x_labels is not None:
        _apply_xtick_labels(ax, x_labels)
    ax.set_xlabel(x)
    ax.set_ylabel("Wert")
    ax.set_title("Stacked Area")
    ax.legend(loc="upper left")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

def plot_pie(ax: Axes, df: pd.DataFrame, label_col: str, value_col: str, top_n: int = 8) -> None:
    """
    Pie-Chart mit Cleaning/Aggregation:
      1) value numerisch
      2) <=0/NaN entfernen
      3) groupby(label).sum()
      4) Top-N + Rest ("Andere")
      5) axis('equal'), startangle=90
    """
    vals = pd.to_numeric(df[value_col], errors="coerce")
    lab = df[label_col].astype(str)
    mask = vals.notna() & (vals > 0)
    vals = vals[mask]
    lab = lab[mask]
    if vals.empty:
        raise ValueError("Pie: Keine positiven Werte nach Cleaning.")
    agg = vals.groupby(lab).sum().sort_values(ascending=False)
    if len(agg) > top_n:
        top = agg.iloc[:top_n]
        rest_sum = agg.iloc[top_n:].sum()
        agg = pd.concat([top, pd.Series([rest_sum], index=["Andere"])])
    labels = agg.index.tolist()
    values = agg.values
    ax.axis("equal")
    ax.pie(
        values,
        labels=labels,
        autopct="%1.1f%%",
        startangle=90,
        wedgeprops={"linewidth": 0.7, "edgecolor": "white"},
    )
    ax.set_title("Pie")

def plot_hist(ax: Axes, series: pd.Series, bins: int | str | None = "auto") -> None:
    """
    Histogramm (vereinfachte Variante):
    - genau 1 numerische Serie
    - 'bins' standardmäßig 'auto' (Matplotlib-Default-Strategie)
      -> Der Nutzer muss keinen Wert eingeben.
    """
    s = pd.to_numeric(series, errors="coerce").dropna()
    if s.empty:
        raise ValueError("Histogramm: keine numerischen Daten nach Cleaning.")
    # bins kann int oder 'auto' sein – hier 'auto' als Standard
    ax.hist(s.values, bins=bins, edgecolor="black", alpha=0.8)
    ax.set_xlabel(series.name if series.name else "Wert")
    ax.set_ylabel("Häufigkeit")
    ax.set_title("Histogram")
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6)

def plot_polar(ax: Axes, series: pd.Series) -> None:
    """Polar-Plot: eine numerische Serie, theta gleichmäßig 0..2π."""
    r = pd.to_numeric(series, errors="coerce").dropna().values
    if r.size == 0:
        raise ValueError("Polar: keine numerischen Daten nach Cleaning.")
    n = r.size
    theta = np.linspace(0, 2 * np.pi, num=n, endpoint=False)
    ax.plot(theta, r, marker="o")
    ax.fill(theta, r, alpha=0.25)
    ax.set_title("Polar")
