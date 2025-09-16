# app.py
# Einfache App-Logik für CSV Daten Plotter
# - Steuert GUI
# - Lädt CSV
# - Ruft Plot-Funktionen auf
# - Berechnet und zeigt Statistik (Basis + plotbezogen)

import tkinter as tk
from tkinter import messagebox

import pandas as pd

import data_loader
import plotter
from ui_main import MainUI


class App:
    def __init__(self, root: tk.Tk):
        # Hauptfenster und UI
        self.root = root
        self.root.title("CSV Daten Plotter")
        self.ui = MainUI(root,
                         on_select_folder=self.on_select_folder,
                         on_select_file=self.on_select_file,
                         on_plot=self.on_plot,
                         on_save_png=self.on_save_png)

        # Zustand
        self.current_folder = None
        self.current_file = None
        self.df: pd.DataFrame | None = None   # pandas ist erlaubt; Union vermeiden wir sonst

    # -----------------------------
    # 1) CSV laden und Basis-Statistik
    # -----------------------------
    def on_select_folder(self, folder_path: str):
        """Wird von der UI aufgerufen, wenn ein Ordner gewählt wurde."""
        self.current_folder = folder_path
        self.ui.list_csv_files(folder_path)  # UI zeigt CSV-Dateien an
        # Statistik-Panel leeren
        self.ui.update_stats_panel("")

    def on_select_file(self, file_path: str):
        """Wird aufgerufen, wenn eine CSV-Datei in der Liste angeklickt wurde."""
        try:
            self.current_file = file_path

            # --- Wichtig: load_csv kann entweder nur DataFrame zurückgeben
            # oder ein Tuple (df, sep). Deshalb hier Abfrage:
            res = data_loader.load_csv(file_path)
            if isinstance(res, tuple):
                df = res[0]  # erstes Element = DataFrame
            else:
                df = res

            # Einfache Sicherheitsprüfung
            if df is None:
                raise ValueError("Leerer DataFrame erhalten.")

            self.df = df

            # Spalten in der UI anzeigen (für X/Y-Auswahl)
            cols = list(self.df.columns)
            self.ui.set_columns(cols)

            # Basisstatistik berechnen und im Panel anzeigen
            basic = compute_basic_stats(self.df)
            basic_text = format_basic_stats(basic)
            self.ui.update_stats_panel(basic_text)

        except Exception as ex:
            # Fehlerdialog für den Nutzer
            from tkinter import messagebox
            messagebox.showerror("Fehler beim Laden", str(ex))
            self.df = None
            self.ui.set_columns([])
            self.ui.update_stats_panel("")

    # -----------------------------
    # 2) Plot zeichnen + plotbezogene Statistik
    # -----------------------------
    def on_plot(self, plot_type: str, x_col: str | None, y_cols: list[str] | None):
        """Wird aufgerufen, wenn der Plot-Button geklickt wurde."""
        if self.df is None:
            messagebox.showinfo("Hinweis", "Bitte zuerst eine CSV-Datei laden.")
            return

        try:
            # Eingaben prüfen (einfach und freundlich)
            if plot_type in ("Pie", "Polar"):
                # Für Pie/Polar: X = Kategorie, genau 1 Y-Spalte
                if not x_col or not y_cols or len(y_cols) != 1:
                    messagebox.showinfo(
                        "Eingabe prüfen",
                        "Für Pie/Polar bitte eine Kategorie-Spalte (X) und genau eine Y-Spalte wählen."
                    )
                    return
            else:
                # Für Line / Stacked Area / Histogram: mind. 1 Y-Spalte
                if not y_cols or len(y_cols) == 0:
                    messagebox.showinfo(
                        "Eingabe prüfen",
                        "Bitte mindestens eine Y-Spalte wählen."
                    )
                    return

            # Plot zeichnen
            ax = self.ui.get_plot_axes()
            ax.clear()

            if plot_type == "Line":
                plotter.plot_line(ax, self.df, x_col, y_cols)
            elif plot_type == "Histogram":
                plotter.plot_histogram(ax, self.df, y_cols)
            elif plot_type == "Stacked Area":
                plotter.plot_stacked_area(ax, self.df, x_col, y_cols)
            elif plot_type == "Pie":
                plotter.plot_pie(ax, self.df, x_col, y_cols[0])
            elif plot_type == "Polar":
                plotter.plot_polar(ax, self.df, x_col, y_cols[0])
            else:
                messagebox.showinfo("Hinweis", f"Unbekannter Plot-Typ: {plot_type}")
                return

            self.ui.draw_canvas()

            # Plot-bezogene Statistik berechnen und anzeigen
            plot_stats = compute_plot_stats(self.df, plot_type, x_col, y_cols)
            plot_text = format_plot_stats(plot_type, plot_stats)
            self.ui.update_stats_panel(plot_text)

        except Exception as ex:
            messagebox.showerror("Fehler beim Plotten", str(ex))

    # -----------------------------
    # 3) PNG speichern
    # -----------------------------
    def on_save_png(self):
        """PNG-Speicherung über UI auslösen."""
        try:
            self.ui.save_current_plot(self.current_file)
        except Exception as ex:
            messagebox.showerror("Fehler beim Speichern", str(ex))


# ============================================================
# Statistik-Funktionen (einfach, gut lesbar)
# ============================================================

def compute_basic_stats(df: pd.DataFrame) -> dict:
    """
    Einfache Basisstatistik nach dem Laden:
    - Zeilen / Spalten
    - Anzahl numerischer / kategorischer Spalten
    """
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = [c for c in df.columns if c not in numeric_cols]

    return {
        "rows": int(df.shape[0]),
        "cols": int(df.shape[1]),
        "numeric_count": len(numeric_cols),
        "categorical_count": len(categorical_cols),
    }


def compute_plot_stats(df: pd.DataFrame,
                       plot_type: str,
                       x_col: str | None,
                       y_cols: list[str] | None) -> dict:
    """
    Plot-bezogene Statistik gemäß TZ:
    - Line / Stacked Area / Histogram: count, mean, std, min, max je Y; Histogram zusätzlich median
    - Pie / Polar: Summe pro Kategorie (Top-5), Gesamt, Anzahl Kategorien
    Rückgabe als einfaches dict für die UI.
    """
    result = {"type": plot_type}

    if plot_type in ("Line", "Stacked Area", "Histogram"):
        if not y_cols:
            return result

        stats_per_y = {}
        for y in y_cols:
            s = pd.to_numeric(df[y], errors="coerce").dropna()
            if s.empty:
                stats_per_y[y] = {"count": 0}
                continue

            entry = {
                "count": int(s.count()),
                "mean": float(s.mean()),
                "std": float(s.std(ddof=1)) if s.count() > 1 else 0.0,
                "min": float(s.min()),
                "max": float(s.max()),
            }
            if plot_type == "Histogram":
                entry["median"] = float(s.median())
            stats_per_y[y] = entry

        result["per_y"] = stats_per_y
        return result

    if plot_type in ("Pie", "Polar"):
        # Aggregation pro Kategorie (Summe)
        if not x_col or not y_cols:
            return result
        y = y_cols[0]
        # Nur numerische Werte summieren
        s = pd.to_numeric(df[y], errors="coerce")
        tmp = df.copy()
        tmp[y] = s
        grouped = tmp.groupby(x_col, dropna=True, as_index=False)[y].sum()
        grouped = grouped.sort_values(by=y, ascending=False)

        total = float(grouped[y].sum()) if not grouped.empty else 0.0
        n_cat = int(grouped.shape[0])
        top5 = grouped.head(5)

        # In einfache Struktur bringen
        top5_list = []
        for _, row in top5.iterrows():
            top5_list.append({"category": str(row[x_col]), "sum": float(row[y])})

        result["total_sum"] = total
        result["n_categories"] = n_cat
        result["top5"] = top5_list
        return result

    return result


# ============================================================
# Hilfsfunktionen für UI-Text
# ============================================================

def format_basic_stats(basic: dict) -> str:
    """Erzeugt einen klaren Textblock für die Basisstatistik."""
    lines = [
        "=== Basisstatistik (nach dem Laden) ===",
        f"Zeilen: {basic.get('rows', 0)}",
        f"Spalten: {basic.get('cols', 0)}",
        f"Numerische Spalten: {basic.get('numeric_count', 0)}",
        f"Kategorische Spalten: {basic.get('categorical_count', 0)}",
    ]
    return "\n".join(lines)


def format_plot_stats(plot_type: str, data: dict) -> str:
    """Erzeugt einen klaren Textblock für die plotbezogene Statistik."""
    if plot_type in ("Line", "Stacked Area", "Histogram"):
        lines = [f"=== Plot-Statistik: {plot_type} ==="]
        per_y = data.get("per_y", {})
        if not per_y:
            lines.append("Keine numerischen Werte gefunden.")
            return "\n".join(lines)

        for y, s in per_y.items():
            lines.append(f"[{y}] count={s.get('count', 0)}, "
                         f"mean={round(s.get('mean', 0.0), 3)}, "
                         f"std={round(s.get('std', 0.0), 3)}, "
                         f"min={round(s.get('min', 0.0), 3)}, "
                         f"max={round(s.get('max', 0.0), 3)}")
            if plot_type == "Histogram" and "median" in s:
                lines[-1] += f", median={round(s['median'], 3)}"
        return "\n".join(lines)

    if plot_type in ("Pie", "Polar"):
        lines = [f"=== Plot-Statistik: {plot_type} ==="]
        total = data.get("total_sum", 0.0)
        n_cat = data.get("n_categories", 0)
        lines.append(f"Gesamtsumme: {round(total, 3)}")
        lines.append(f"Anzahl Kategorien: {n_cat}")
        lines.append("Top-5 Kategorien (Summe):")
        for item in data.get("top5", []):
            lines.append(f"- {item['category']}: {round(item['sum'], 3)}")
        return "\n".join(lines)

    return f"=== Plot-Statistik: {plot_type} ===\nKeine Daten."


# ============================================================
# Start
# ============================================================

def main():
    root = tk.Tk()
    app = App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
