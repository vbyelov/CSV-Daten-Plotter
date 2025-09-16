# plotter.py
# Plot-Funktionen für fünf Diagrammtypen:
# Line, Histogram, Stacked Area, Pie, Polar (einfach als "radiale" Darstellung)
#
# Hinweise:
# - Fokus auf einfache, gut lesbare Implementierung.
# - Für "Polar" nutzen wir eine leichte radiale Darstellung auf Kartesisch,
#   damit die UI-Achse (ax) nicht in eine echte Polar-Achse umgebaut werden muss.
#   Kategorien werden gleichmäßig als Winkel verteilt, der Wert ist der Radius.

import math
import numpy as np
import pandas as pd


# --------------------------------------------------------
# 1) LINE
# --------------------------------------------------------
def plot_line(ax, df, x_col, y_cols):
    """Einfache Liniengrafik. X kann Kategorie/Datum sein, Y sind numerische Spalten."""
    ax.grid(True, linestyle="--", alpha=0.3)

    # X-Achse
    if x_col and x_col in df.columns:
        x = df[x_col]
    else:
        x = df.index  # Fallback

    # Y-Serien plotten (nur numerische)
    plotted_any = False
    for y in (y_cols or []):
        if y not in df.columns:
            continue
        s = pd.to_numeric(df[y], errors="coerce")
        if s.notna().sum() == 0:
            continue
        ax.plot(x, s, label=y)
        plotted_any = True

    ax.set_title("Linien-Diagramm")
    ax.set_xlabel(x_col if x_col else "Index")
    ax.set_ylabel("Wert")
    if plotted_any:
        ax.legend(loc="best")
    _rotate_xticks_if_needed(ax)


# --------------------------------------------------------
# 2) HISTOGRAM
# --------------------------------------------------------
def plot_histogram(ax, df, y_cols, bins=30):
    """Histogramme mehrerer numerischer Spalten (gemeinsame X-Achse für Bins)."""
    ax.grid(True, linestyle="--", alpha=0.3)

    # Daten sammeln (nur numerische Spalten)
    plotted_any = False
    for y in (y_cols or []):
        if y not in df.columns:
            continue
        s = pd.to_numeric(df[y], errors="coerce").dropna()
        if s.empty:
            continue
        ax.hist(s, bins=bins, alpha=0.6, label=y)
        plotted_any = True

    ax.set_title("Histogramm")
    ax.set_xlabel("Wert")
    ax.set_ylabel("Häufigkeit")
    if plotted_any:
        ax.legend(loc="best")


# --------------------------------------------------------
# 3) STACKED AREA
# --------------------------------------------------------
def plot_stacked_area(ax, df, x_col, y_cols):
    """Gestapeltes Flächendiagramm (mind. 2 numerische Spalten)."""
    ax.grid(True, linestyle="--", alpha=0.3)

    # X-Achse
    if x_col and x_col in df.columns:
        x_raw = df[x_col]
    else:
        x_raw = df.index

    # Y-Matrix vorbereiten (nur numerisch)
    series_list = []
    labels = []
    for y in (y_cols or []):
        if y not in df.columns:
            continue
        s = pd.to_numeric(df[y], errors="coerce")
        series_list.append(s)
        labels.append(y)

    if len(series_list) == 0:
        ax.text(0.5, 0.5, "Keine numerischen Y-Spalten.", ha="center", va="center", transform=ax.transAxes)
        return

    # Fehlende Werte als 0 interpretieren (einfach und robust)
    Y = pd.concat(series_list, axis=1)
    Y.columns = labels
    Y = Y.fillna(0.0)

    # X als Positionen (0..n-1) + Ticks mit Labels
    x_pos = np.arange(len(x_raw))
    ax.stackplot(x_pos, Y.values.T, labels=labels)
    ax.set_title("Gestapeltes Flächendiagramm")
    ax.set_xlabel(x_col if x_col else "Index")
    ax.set_ylabel("Wert")
    ax.legend(loc="best")

    # Schöne X-Beschriftung
    ax.set_xticks(_sparse_ticks(x_pos))
    ax.set_xticklabels(_sparse_ticklabels(x_raw, x_pos))
    _rotate_xticks_if_needed(ax)


# --------------------------------------------------------
# 4) PIE
# --------------------------------------------------------
def plot_pie(ax, df, x_col, y_col):
    """Kreisdiagramm: Summe pro Kategorie."""
    ax.grid(False)

    if x_col not in df.columns or y_col not in df.columns:
        ax.text(0.5, 0.5, "Spalten nicht gefunden.", ha="center", va="center", transform=ax.transAxes)
        return

    s = pd.to_numeric(df[y_col], errors="coerce")
    tmp = df.copy()
    tmp[y_col] = s

    grouped = tmp.groupby(x_col, dropna=True, as_index=False)[y_col].sum()
    if grouped.empty:
        ax.text(0.5, 0.5, "Keine Daten.", ha="center", va="center", transform=ax.transAxes)
        return

    # Optional: zu viele Kategorien -> Top 10 + Rest (für bessere Lesbarkeit)
    grouped = grouped.sort_values(by=y_col, ascending=False)
    if len(grouped) > 10:
        top = grouped.head(9)
        rest_sum = grouped.iloc[9:][y_col].sum()
        grouped = pd.concat([top, pd.DataFrame({x_col: ["Andere"], y_col: [rest_sum]})], ignore_index=True)

    ax.pie(grouped[y_col].values,
           labels=[str(v) for v in grouped[x_col].values],
           autopct="%1.1f%%",
           startangle=90)
    ax.axis("equal")  # Kreis
    ax.set_title(f"Kreisdiagramm (Summe von '{y_col}' pro '{x_col}')")


# --------------------------------------------------------
# 5) POLAR (radiale, einfache Darstellung auf Kartesisch)
# --------------------------------------------------------
def plot_polar(ax, df, x_col, y_col):
    """
    Polar (einfach): Kategorien werden gleichmäßig auf 0..2π verteilt.
    Der Wert ist der Radius. Wir zeichnen Strahlen vom Ursprung.
    """
    ax.grid(True, linestyle="--", alpha=0.3)

    if x_col not in df.columns or y_col not in df.columns:
        ax.text(0.5, 0.5, "Spalten nicht gefunden.", ha="center", va="center", transform=ax.transAxes)
        return

    s = pd.to_numeric(df[y_col], errors="coerce")
    tmp = df.copy()
    tmp[y_col] = s

    grouped = tmp.groupby(x_col, dropna=True, as_index=False)[y_col].sum()
    grouped = grouped.sort_values(by=y_col, ascending=False)
    if grouped.empty:
        ax.text(0.5, 0.5, "Keine Daten.", ha="center", va="center", transform=ax.transAxes)
        return

    # Winkel und Radien
    n = len(grouped)
    angles = [2 * math.pi * i / n for i in range(n)]
    radii = grouped[y_col].values.astype(float)
    labels = [str(v) for v in grouped[x_col].values]

    # Skala bestimmen
    r_max = float(max(radii))
    pad = r_max * 0.1 if r_max > 0 else 1.0
    r_lim = r_max + pad

    # Strahlen zeichnen
    for theta, r, lab in zip(angles, radii, labels):
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        ax.plot([0, x], [0, y], linewidth=2)
        # Marker am Ende
        ax.scatter([x], [y], s=30)

    # Hilfskreise (nur als optische Führung)
    _draw_circle(ax, radius=r_lim, segments=200, alpha=0.15)
    _draw_circle(ax, radius=r_lim * 0.5, segments=160, alpha=0.08)

    # Labels am Rand
    label_radius = r_lim * 1.06
    for theta, lab in zip(angles, labels):
        lx = label_radius * math.cos(theta)
        ly = label_radius * math.sin(theta)
        ax.text(lx, ly, lab, ha="center", va="center")

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlim(-label_radius * 1.15, label_radius * 1.15)
    ax.set_ylim(-label_radius * 1.15, label_radius * 1.15)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title(f"Polar (einfach) – Radius = Summe von '{y_col}' pro '{x_col}'")


# ========================================================
# Hilfsfunktionen
# ========================================================
def _rotate_xticks_if_needed(ax, angle=30):
    """Dreht X-Beschriftung leicht, falls viele Werte vorhanden sind."""
    try:
        ticks = ax.get_xticks()
        if len(ticks) > 8:
            for label in ax.get_xticklabels():
                label.set_rotation(angle)
                label.set_ha("right")
    except Exception:
        pass


def _sparse_ticks(x_positions, max_ticks=12):
    """Reduziert die Anzahl der Ticks auf max_ticks (gleichmäßig verteilt)."""
    n = len(x_positions)
    if n <= max_ticks:
        return x_positions
    step = max(1, int(round(n / max_ticks)))
    return x_positions[::step]


def _sparse_ticklabels(x_labels, x_positions):
    """Gibt zu den sparse Ticks die passenden Labels zurück."""
    labels = []
    pos_set = set(x_positions)
    for i, v in enumerate(x_labels):
        if i in pos_set:
            labels.append(str(v))
    return labels


def _draw_circle(ax, radius=1.0, segments=200, alpha=0.1):
    """Zeichnet einen leichten Kreis zur Orientierung."""
    t = np.linspace(0, 2 * math.pi, segments)
    x = radius * np.cos(t)
    y = radius * np.sin(t)
    ax.plot(x, y, linestyle="-", linewidth=1, alpha=alpha)
