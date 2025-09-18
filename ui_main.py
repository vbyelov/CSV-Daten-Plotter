# ui_main.py
# -----------------------------------------------
# Linke Pane fest 400 px, rechte Pane füllt Rest++
# -----------------------------------------------

import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


class MainUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("CSV Daten Plotter")
        self.root.geometry("1000x700")

        # PanedWindow
        self.paned = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        self.paned.pack(fill=tk.BOTH, expand=True)

        # Frames
        left_frame = ttk.Frame(self.paned, width=400)
        right_frame = ttk.Frame(self.paned)

        self.paned.add(left_frame)
        self.paned.add(right_frame)

        # --- Fix sash bei 400 px ---
        self.root.after(0, lambda: self._fix_left_width(400))
        self.root.bind("<Configure>", lambda _e: self._fix_left_width(400))
        self.paned.bind("<B1-Motion>", lambda _e: self._fix_left_width(400))

        # Datei-Button
        self.btn_open = ttk.Button(left_frame, text="CSV öffnen")
        self.btn_open.pack(padx=5, pady=5, anchor="w")

        # Diagrammtyp
        self.plot_type = tk.StringVar(value="")
        rb_frame = ttk.LabelFrame(left_frame, text="Diagrammtyp")
        rb_frame.pack(fill="x", padx=5, pady=5)
        for pt in ["Line", "Pie", "Histogram", "Stacked Area", "Polar"]:
            rb = ttk.Radiobutton(rb_frame, text=pt, value=pt, variable=self.plot_type)
            rb.pack(side="left", padx=3, pady=3)

        # Auswahl X
        x_frame = ttk.Frame(left_frame)
        x_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(x_frame, text="X-Spalte:").pack(side="left")
        self.cmb_x = ttk.Combobox(x_frame, state="readonly")
        self.cmb_x.pack(side="left", fill="x", expand=True)

        # Auswahl Y
        y_frame = ttk.Frame(left_frame)
        y_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(y_frame, text="Y-Spalten:").pack(anchor="w")
        self.lst_y = tk.Listbox(y_frame, selectmode=tk.MULTIPLE, exportselection=False, height=5)
        self.lst_y.pack(fill="x", expand=True)

        # Buttons
        btns = ttk.Frame(left_frame)
        btns.pack(fill="x", padx=5, pady=8)
        self.btn_plot = ttk.Button(btns, text="Plot erzeugen", state="disabled")
        self.btn_plot.pack(side="left")
        self.btn_save = ttk.Button(btns, text="Als PNG speichern", state="normal")
        self.btn_save.pack(side="left", padx=8)

        # Details
        details_frame = ttk.LabelFrame(left_frame, text="Details / Statistik")
        details_frame.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        self.txt_details = tk.Text(details_frame, wrap="word")
        self.txt_details.pack(fill="both", expand=True, padx=5, pady=5)

        # Plot rechts
        self.fig = Figure(figsize=(6, 4))
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Statuszeile
        self.status = tk.StringVar(value="Bereit")
        lbl_status = ttk.Label(self.root, textvariable=self.status, anchor="w")
        lbl_status.pack(fill="x", side="bottom")

    # Hilfsmethoden
    def clear_plot(self):
        self.fig.clf()
        self.ax = self.fig.add_subplot(111)
        self.canvas.draw()

    def update_status(self, text: str):
        self.status.set(text)

    def update_details(self, text: str):
        self.txt_details.delete("1.0", tk.END)
        self.txt_details.insert(tk.END, text)

    def _fix_left_width(self, width_px: int):
        try:
            self.paned.sashpos(0, width_px)
        except Exception:
            pass
