import tkinter as tk
from tkinter import ttk
import random
import math

# ── Paleta de cores ──────────────────────────────────────────────────────────
BG        = "#1a1a2e"
PANEL     = "#16213e"
ACCENT    = "#e94560"
GOLD      = "#f5a623"
TEXT      = "#eaeaea"
SUBTEXT   = "#a0a0b0"
BTN_HOVER = "#c73652"
DICE_CLR  = {
    "D4":  "#9b59b6",
    "D6":  "#3498db",
    "D8":  "#2ecc71",
    "D12": "#e67e22",
    "D20": "#e74c3c",
}

DICE_SIDES = {"D4": 4, "D6": 6, "D8": 8, "D12": 12, "D20": 20}

# ── Faces ASCII dos dados ─────────────────────────────────────────────────────
DICE_ART = {
    "D4": [
        "    /\\    ",
        "   /  \\   ",
        "  / {v:2} \\  ",
        " /______\\ ",
    ],
    "D6": [
        " _______ ",
        "|       |",
        "|  {v:2}   |",
        "|_______|",
    ],
    "D8": [
        "   /\\   ",
        "  /{v:2} \\  ",
        "  \\    /  ",
        "   \\/   ",
    ],
    "D12": [
        "  /----\\  ",
        " / {v:3}  \\ ",
        " \\      / ",
        "  \\----/  ",
    ],
    "D20": [
        "  /\\  /\\  ",
        " /{v:3}\\/ \\",
        " \\  /\\  / ",
        "  \\/  \\/  ",
    ],
}


class DiceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RPG Dice Roller")
        self.configure(bg=BG)
        self.resizable(False, False)
        self.geometry("620x700")

        self._anim_job = None
        self._anim_step = 0
        self._final_results = []

        self._build_ui()
        self._center_window()

    # ── Layout ────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Título
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", pady=(18, 4))
        tk.Label(hdr, text="⚔  RPG DICE ROLLER  ⚔", font=("Courier New", 20, "bold"),
                 bg=BG, fg=GOLD).pack()
        tk.Label(hdr, text="Escolha o dado e a quantidade", font=("Courier New", 10),
                 bg=BG, fg=SUBTEXT).pack()

        # Separador
        tk.Frame(self, height=2, bg=ACCENT).pack(fill="x", padx=30, pady=8)

        # Painel de seleção
        sel = tk.Frame(self, bg=PANEL, bd=0, relief="flat")
        sel.pack(fill="x", padx=30, pady=6, ipady=14)

        # --- Tipo de dado ---
        tk.Label(sel, text="TIPO DE DADO", font=("Courier New", 9, "bold"),
                 bg=PANEL, fg=SUBTEXT).grid(row=0, column=0, padx=20, pady=(10, 2))

        self.dice_var = tk.StringVar(value="D20")
        dice_row = tk.Frame(sel, bg=PANEL)
        dice_row.grid(row=1, column=0, padx=20, pady=(0, 10))
        self._dice_btns = {}
        for i, d in enumerate(["D4", "D6", "D8", "D12", "D20"]):
            b = tk.Button(
                dice_row, text=d, width=5, font=("Courier New", 10, "bold"),
                bg=PANEL, fg=DICE_CLR[d], activebackground=DICE_CLR[d],
                activeforeground=BG, bd=1, relief="solid",
                cursor="hand2",
                command=lambda d=d: self._select_dice(d),
            )
            b.grid(row=0, column=i, padx=3)
            self._dice_btns[d] = b
        self._select_dice("D20")

        # --- Quantidade ---
        tk.Label(sel, text="QUANTIDADE", font=("Courier New", 9, "bold"),
                 bg=PANEL, fg=SUBTEXT).grid(row=0, column=1, padx=20, pady=(10, 2))

        qty_frame = tk.Frame(sel, bg=PANEL)
        qty_frame.grid(row=1, column=1, padx=20)

        self.qty_var = tk.IntVar(value=1)
        minus_btn = tk.Button(qty_frame, text="−", font=("Courier New", 14, "bold"),
                              bg=PANEL, fg=ACCENT, activebackground=ACCENT,
                              activeforeground=BG, bd=0, cursor="hand2",
                              command=self._dec_qty)
        minus_btn.grid(row=0, column=0, padx=4)

        self.qty_lbl = tk.Label(qty_frame, textvariable=self.qty_var,
                                width=3, font=("Courier New", 18, "bold"),
                                bg=PANEL, fg=TEXT)
        self.qty_lbl.grid(row=0, column=1)

        plus_btn = tk.Button(qty_frame, text="+", font=("Courier New", 14, "bold"),
                             bg=PANEL, fg=ACCENT, activebackground=ACCENT,
                             activeforeground=BG, bd=0, cursor="hand2",
                             command=self._inc_qty)
        plus_btn.grid(row=0, column=2, padx=4)

        sel.columnconfigure(0, weight=1)
        sel.columnconfigure(1, weight=1)

        # Botão Jogar
        self.roll_btn = tk.Button(
            self, text="🎲  JOGAR  🎲",
            font=("Courier New", 15, "bold"),
            bg=ACCENT, fg=TEXT,
            activebackground=BTN_HOVER, activeforeground=TEXT,
            relief="flat", bd=0, padx=20, pady=10,
            cursor="hand2",
            command=self._start_roll,
        )
        self.roll_btn.pack(pady=14)
        self.roll_btn.bind("<Enter>", lambda e: self.roll_btn.config(bg=BTN_HOVER))
        self.roll_btn.bind("<Leave>", lambda e: self.roll_btn.config(bg=ACCENT))

        # Área de animação / resultado do dado
        self.canvas = tk.Canvas(self, width=560, height=160,
                                bg=PANEL, highlightthickness=0)
        self.canvas.pack(padx=30, pady=(0, 6))

        # Totalizador
        tot_frame = tk.Frame(self, bg=BG)
        tot_frame.pack(pady=4)
        tk.Label(tot_frame, text="TOTAL:", font=("Courier New", 13, "bold"),
                 bg=BG, fg=SUBTEXT).pack(side="left", padx=6)
        self.total_var = tk.StringVar(value="—")
        tk.Label(tot_frame, textvariable=self.total_var,
                 font=("Courier New", 24, "bold"), bg=BG, fg=GOLD).pack(side="left")

        # Histórico
        tk.Frame(self, height=2, bg=ACCENT).pack(fill="x", padx=30, pady=6)
        tk.Label(self, text="HISTÓRICO", font=("Courier New", 9, "bold"),
                 bg=BG, fg=SUBTEXT).pack()

        hist_wrap = tk.Frame(self, bg=BG)
        hist_wrap.pack(fill="both", expand=True, padx=30, pady=(4, 14))

        scrollbar = tk.Scrollbar(hist_wrap)
        scrollbar.pack(side="right", fill="y")
        self.history = tk.Text(hist_wrap, height=8,
                               font=("Courier New", 9),
                               bg=PANEL, fg=TEXT, insertbackground=TEXT,
                               state="disabled", relief="flat",
                               yscrollcommand=scrollbar.set)
        self.history.pack(fill="both", expand=True)
        scrollbar.config(command=self.history.yview)

        self._draw_idle()

    # ── Controles ────────────────────────────────────────────────────────────
    def _select_dice(self, d):
        self.dice_var.set(d)
        for name, btn in self._dice_btns.items():
            if name == d:
                btn.config(bg=DICE_CLR[d], fg=BG, relief="sunken")
            else:
                btn.config(bg=PANEL, fg=DICE_CLR[name], relief="solid")

    def _inc_qty(self):
        if self.qty_var.get() < 20:
            self.qty_var.set(self.qty_var.get() + 1)

    def _dec_qty(self):
        if self.qty_var.get() > 1:
            self.qty_var.set(self.qty_var.get() - 1)

    # ── Animação ─────────────────────────────────────────────────────────────
    def _start_roll(self):
        if self._anim_job is not None:
            return  # já animando
        dtype = self.dice_var.get()
        qty   = self.qty_var.get()
        sides = DICE_SIDES[dtype]
        self._final_results = [random.randint(1, sides) for _ in range(qty)]
        self._anim_step = 0
        self.roll_btn.config(state="disabled")
        self._animate(dtype, qty, sides)

    def _animate(self, dtype, qty, sides):
        STEPS = 18  # número de frames de animação
        if self._anim_step < STEPS:
            fake = [random.randint(1, sides) for _ in range(qty)]
            self._draw_dice(dtype, fake, rolling=True)
            speed = max(40, 120 - self._anim_step * 5)  # acelera no início, desacelera
            self._anim_step += 1
            self._anim_job = self.after(speed, lambda: self._animate(dtype, qty, sides))
        else:
            self._anim_job = None
            self._show_result(dtype, self._final_results)
            self.roll_btn.config(state="normal")

    def _draw_dice(self, dtype, values, rolling=False):
        self.canvas.delete("all")
        qty   = len(values)
        color = DICE_CLR[dtype]
        w, h  = 560, 160
        slot  = min(w // qty, 120)
        start = (w - slot * qty) // 2

        for i, v in enumerate(values):
            cx = start + slot * i + slot // 2
            cy = h // 2
            r  = min(slot // 2 - 8, 46)
            self._draw_shape(dtype, cx, cy, r, color, v, rolling)

    def _draw_shape(self, dtype, cx, cy, r, color, value, rolling):
        c = self.canvas
        flash = color if not rolling else "#ffffff"
        lw = 2

        if dtype == "D4":
            pts = self._polygon_pts(cx, cy, r, 3, -90)
            c.create_polygon(pts, outline=flash, fill=BG, width=lw)
            c.create_text(cx, cy + r * 0.18, text=str(value),
                          font=("Courier New", 16, "bold"), fill=flash)

        elif dtype == "D6":
            c.create_rectangle(cx - r, cy - r, cx + r, cy + r,
                                outline=flash, fill=BG, width=lw)
            c.create_text(cx, cy, text=str(value),
                          font=("Courier New", 18, "bold"), fill=flash)

        elif dtype == "D8":
            pts = self._polygon_pts(cx, cy, r, 4, 0)
            c.create_polygon(pts, outline=flash, fill=BG, width=lw)
            pts2 = self._polygon_pts(cx, cy, r, 4, 45)
            c.create_polygon(pts2, outline=flash, fill=BG, width=lw)
            c.create_text(cx, cy, text=str(value),
                          font=("Courier New", 18, "bold"), fill=flash)

        elif dtype == "D12":
            pts = self._polygon_pts(cx, cy, r, 5, -90)
            c.create_polygon(pts, outline=flash, fill=BG, width=lw)
            c.create_text(cx, cy, text=str(value),
                          font=("Courier New", 16, "bold"), fill=flash)

        elif dtype == "D20":
            pts = self._polygon_pts(cx, cy, r, 6, 0)
            c.create_polygon(pts, outline=flash, fill=BG, width=lw)
            c.create_text(cx, cy, text=str(value),
                          font=("Courier New", 16, "bold"), fill=flash)

    def _polygon_pts(self, cx, cy, r, n, offset_deg):
        pts = []
        for i in range(n):
            a = math.radians(offset_deg + 360 * i / n)
            pts.append(cx + r * math.cos(a))
            pts.append(cy + r * math.sin(a))
        return pts

    def _draw_idle(self):
        self.canvas.delete("all")
        self.canvas.create_text(
            280, 80, text="Selecione o dado e pressione JOGAR",
            font=("Courier New", 11), fill=SUBTEXT,
        )

    # ── Resultado ────────────────────────────────────────────────────────────
    def _show_result(self, dtype, results):
        self._draw_dice(dtype, results, rolling=False)
        total = sum(results)
        self.total_var.set(str(total))
        self._add_history(dtype, results, total)

    def _add_history(self, dtype, results, total):
        color = DICE_CLR[dtype]
        qty   = len(results)
        rolls = ", ".join(str(r) for r in results)
        line  = f"  {qty}{dtype}  →  [{rolls}]  =  {total}\n"

        self.history.config(state="normal")
        tag = f"clr_{dtype}"
        self.history.tag_config(tag, foreground=color)
        self.history.insert("1.0", line, tag)
        self.history.config(state="disabled")

    # ── Utilitário ───────────────────────────────────────────────────────────
    def _center_window(self):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - self.winfo_width())  // 2
        y  = (sh - self.winfo_height()) // 2
        self.geometry(f"+{x}+{y}")


if __name__ == "__main__":
    app = DiceApp()
    app.mainloop()
