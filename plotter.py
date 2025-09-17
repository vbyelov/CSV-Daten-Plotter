import matplotlib.pyplot as plt

# Jede Plot-Funktion zeichnet direkt auf der übergebenen Achse (ax).
# Wir benutzen einfache Matplotlib-Befehle, damit der Code lesbar bleibt.

def draw_line(ax, df, x_col, y_cols):
    """Liniendiagramm"""
    for y in y_cols:
        ax.plot(df[x_col], df[y], label=y)
    ax.set_title("Liniendiagramm")
    ax.set_xlabel(x_col)
    ax.set_ylabel("Wert")
    ax.legend()

def draw_pie(ax, df, x_col, y_cols):
    """Kreisdiagramm (eine Y-Spalte, gruppiert nach Kategorie)"""
    if not y_cols:
        return
    y = y_cols[0]
    grouped = df.groupby(x_col)[y].sum()
    ax.pie(grouped, labels=grouped.index, autopct="%1.1f%%")
    ax.set_title("Kreisdiagramm")

def draw_hist(ax, df, x_col, y_cols):
    """Histogramm für eine oder mehrere numerische Spalten"""
    for y in y_cols:
        ax.hist(df[y].dropna(), bins=20, alpha=0.5, label=y)
    ax.set_title("Histogramm")
    ax.set_xlabel("Wert")
    ax.set_ylabel("Häufigkeit")
    ax.legend()

def draw_stacked(ax, df, x_col, y_cols):
    """Gestapeltes Flächendiagramm"""
    ax.stackplot(df[x_col], [df[y] for y in y_cols], labels=y_cols)
    ax.set_title("Gestapeltes Flächendiagramm")
    ax.set_xlabel(x_col)
    ax.set_ylabel("Wert")
    ax.legend()

def draw_polar(ax, df, x_col, y_cols):
    """Polardiagramm (eine Y-Spalte, Summe pro Kategorie)"""
    if not y_cols:
        return
    y = y_cols[0]
    grouped = df.groupby(x_col)[y].sum()

    # Kategorien als Winkel verteilen
    categories = list(grouped.index)
    values = grouped.values
    angles = [n / float(len(categories)) * 2 * 3.14159 for n in range(len(categories))]

    values = list(values) + [values[0]]
    angles = list(angles) + [angles[0]]

    ax.plot(angles, values, "o-")
    ax.fill(angles, values, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title("Polardiagramm")

# Dispatcher für zentrale Steuerung
_DISPATCH = {
    "line": draw_line,
    "pie": draw_pie,
    "hist": draw_hist,
    "stacked": draw_stacked,
    "polar": draw_polar,
}

def draw(plot_type, ax, df, x_col, y_cols):
    """Allgemeine Funktion zum Zeichnen, wählt richtigen Plot"""
    if plot_type not in _DISPATCH:
        raise ValueError(f"Unbekannter Plot-Typ: {plot_type}")
    ax.clear()
    _DISPATCH[plot_type](ax, df, x_col, y_cols)
