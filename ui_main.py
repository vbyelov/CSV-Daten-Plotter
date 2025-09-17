# ui_main.py
# ------------------------------------------------------
# Aufbau der Benutzeroberfläche (Tkinter).
# Vereinfachte rechte Seite: nur "Details" ohne Mini-Tabelle.
# Kein separates Bins-Feld mehr (Histogramm verwendet Default im Code).
# ------------------------------------------------------

import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class MainUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CSV Daten Plotter")
        self.root.geometry("1000x700")  # Startgröße (kann angepasst werden)

        # Haupt-Container: PanedWindow (Plot links, Statistik rechts)
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # --------- Linke Seite: Plot-Bereich + Steuerung ---------
        left_frame = ttk.Frame(self.paned)
        self.paned.add(left_frame, weight=3)  # Start: 60 % links

        # Datei-Button
        self.btn_open = ttk.Button(left_frame, text="CSV öffnen")
        self.btn_open.pack(padx=5, pady=5, anchor="w")

        # Diagrammtyp (Radiobuttons)
        self.plot_type = tk.StringVar(value="")
        plot_types = ["Line", "Pie", "Histogram", "Stacked Area", "Polar"]
        rb_frame = ttk.LabelFrame(left_frame, text="Diagrammtyp")
        rb_frame.pack(fill="x", padx=5, pady=5)
        for pt in plot_types:
            rb = ttk.Radiobutton(rb_frame, text=pt, value=pt, variable=self.plot_type)
            rb.pack(side="left", padx=3, pady=3)

        # Auswahl X
        x_frame = ttk.Frame(left_frame)
        x_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(x_frame, text="X-Spalte:").pack(side="left")
        self.cmb_x = ttk.Combobox(x_frame, state="readonly")
        self.cmb_x.pack(side="left", fill="x", expand=True)

        # Auswahl Y (Mehrfachauswahl möglich)
        y_frame = ttk.Frame(left_frame)
        y_frame.pack(fill="both", padx=5, pady=2, expand=False)
        ttk.Label(y_frame, text="Y-Spalten:").pack(anchor="w")
        self.lst_y = tk.Listbox(y_frame, selectmode=tk.MULTIPLE, exportselection=False, height=5)
        self.lst_y.pack(fill="x", expand=True)

        # Plot-Button
        self.btn_plot = ttk.Button(left_frame, text="Plot erzeugen", state="disabled")
        self.btn_plot.pack(padx=5, pady=5)

        # Canvas für Matplotlib-Figur
        self.fig = Figure(figsize=(5, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=left_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True)

        # --------- Rechte Seite: NUR Details ---------
        right_frame = ttk.Frame(self.paned)
        self.paned.add(right_frame, weight=2)  # Start: 40 % rechts

        ttk.Label(right_frame, text="Details / Statistik:").pack(anchor="w", padx=5, pady=5)
        self.txt_details = tk.Text(right_frame, wrap="word", height=20)
        self.txt_details.pack(fill="both", expand=True, padx=5, pady=5)

        # --------- Statuszeile ---------
        self.status = tk.StringVar(value="Bereit")
        lbl_status = ttk.Label(self.root, textvariable=self.status, anchor="w")
        lbl_status.pack(fill="x", side="bottom")

    # --------------------------------------------------
    # Hilfs-Methoden zum Zugriff von außen
    # --------------------------------------------------
    def clear_plot(self):
        """Löscht aktuelle Zeichnung."""
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.canvas.draw()

    def update_status(self, text: str):
        """Aktualisiert die Statuszeile."""
        self.status.set(text)

    def update_details(self, text: str):
        """Zeigt Details als mehrzeiligen Text."""
        self.txt_details.delete("1.0", tk.END)
        self.txt_details.insert(tk.END, text)
