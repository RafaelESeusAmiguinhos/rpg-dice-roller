import pygame
import random
import math
import sys

pygame.init()

# ── Janela ────────────────────────────────────────────────────────────────────
W, H = 1280, 720
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption('RPG Dice Roller')
clock = pygame.time.Clock()
FPS   = 60

# ── Cores ─────────────────────────────────────────────────────────────────────
BG       = (10,  10,  22)
PANEL    = (15,  21,  44)
PANEL2   = (22,  30,  60)
BORDER   = (38,  48,  85)
GOLD     = (245, 166, 35)
ACCENT   = (233, 69,  96)
ACC_DARK = (170, 40,  65)
TEXT     = (234, 234, 234)
SUBTEXT  = (128, 128, 155)
WHITE    = (255, 255, 255)
BLACK    = (0,   0,   0)

DICE_CLR = {
    'D4' : (155,  89, 182),
    'D6' : ( 52, 152, 219),
    'D8' : ( 46, 204, 113),
    'D12': (230, 126,  34),
    'D20': (231,  76,  60),
}
DICE_SIDES = {'D4': 4, 'D6': 6, 'D8': 8, 'D12': 12, 'D20': 20}
DICE_LIST  = ['D4', 'D6', 'D8', 'D12', 'D20']

# ── Fontes ────────────────────────────────────────────────────────────────────
def _f(size, bold=False):
    try:
        return pygame.font.SysFont('Courier New', size, bold=bold)
    except Exception:
        return pygame.font.Font(None, size + 6)

F_TITLE = _f(26, bold=True)
F_LABEL = _f(13, bold=True)
F_SMALL = _f(11)
F_BTN   = _f(15, bold=True)
F_QTY   = _f(38, bold=True)
F_DICE  = _f(46, bold=True)
F_TOTAL = _f(40, bold=True)
F_HIST  = _f(12)

# ── Utilitários ───────────────────────────────────────────────────────────────
def darker(c, f=0.55):
    return tuple(max(0, int(v * f)) for v in c)

def lighter(c, f=1.5):
    return tuple(min(255, int(v * f)) for v in c)

def txt_c(surf, text, font, color, cx, cy):
    s = font.render(text, True, color)
    surf.blit(s, s.get_rect(center=(cx, cy)))

def txt(surf, text, font, color, x, y):
    surf.blit(font.render(text, True, color), (x, y))

def poly_pts(cx, cy, rx, ry, n, off_deg=0):
    pts = []
    for i in range(n):
        a = math.radians(off_deg + 360 * i / n)
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts

# ── Desenho dos dados ─────────────────────────────────────────────────────────
DICE_SHAPE = {
    'D4' : (3,  -90),   # triângulo, vértice no topo
    'D6' : (4,   45),   # quadrado, lados retos
    'D8' : (4,    0),   # losango, vértice no topo
    'D12': (5,  -90),   # pentágono
    'D20': (6,    0),   # hexágono
}

def draw_die(surf, dtype, cx, cy, r, value, sx=1.0):
    """Desenha um dado com efeito 3-D usando highlight/sombra."""
    clr   = DICE_CLR[dtype]
    dark  = darker(clr, 0.45)
    light = lighter(clr, 1.55)
    n, off = DICE_SHAPE[dtype]
    rx = r * sx
    ry = r

    if rx < 2:
        return

    # ── sombra ──
    s_pts = [(int(x + 5), int(y + 6)) for x, y in poly_pts(cx, cy, rx, ry, n, off)]
    if len(s_pts) >= 3:
        pygame.draw.polygon(surf, darker(BG, 0.3), s_pts)

    # ── face inferior (mais escura) ──
    b_pts = [(int(x), int(y)) for x, y in poly_pts(cx + 3, cy + 4, rx * 0.96, ry * 0.96, n, off)]
    if len(b_pts) >= 3:
        pygame.draw.polygon(surf, dark, b_pts)

    # ── face principal ──
    m_pts = [(int(x), int(y)) for x, y in poly_pts(cx, cy, rx, ry, n, off)]
    if len(m_pts) >= 3:
        pygame.draw.polygon(surf, clr, m_pts)

    # ── highlight (canto superior-esquerdo) ──
    h_pts = [(int(x), int(y)) for x, y in
              poly_pts(cx - rx * 0.12, cy - ry * 0.14, rx * 0.65, ry * 0.65, n, off)]
    if len(h_pts) >= 3:
        pygame.draw.polygon(surf, light, h_pts)

    # ── núcleo (cor base para profundidade) ──
    k_pts = [(int(x), int(y)) for x, y in
              poly_pts(cx - rx * 0.05, cy - ry * 0.06, rx * 0.42, ry * 0.42, n, off)]
    if len(k_pts) >= 3:
        pygame.draw.polygon(surf, clr, k_pts)

    # ── contorno ──
    if len(m_pts) >= 3:
        pygame.draw.polygon(surf, light, m_pts, 2)

    # ── valor ──
    if value is not None and sx > 0.28:
        val_str = str(value)
        ts = F_DICE.render(val_str, True, WHITE)
        if sx < 0.92:
            nw = max(1, int(ts.get_width() * sx))
            ts = pygame.transform.scale(ts, (nw, ts.get_height()))
        surf.blit(ts, ts.get_rect(center=(int(cx), int(cy))))

# ── Botão ─────────────────────────────────────────────────────────────────────
class Button:
    def __init__(self, rect, text, clr, hover, txt_clr, font=F_BTN, radius=8):
        self.rect    = pygame.Rect(rect)
        self.text    = text
        self.clr     = clr
        self.hover   = hover
        self.txt_clr = txt_clr
        self.font    = font
        self.radius  = radius
        self.hovered = False
        self.active  = False
        self.enabled = True

    def draw(self, surf):
        if not self.enabled:
            c  = darker(self.clr, 0.5)
            tc = SUBTEXT
        elif self.active:
            c  = self.hover
            tc = BLACK
        elif self.hovered:
            c  = self.hover
            tc = self.txt_clr
        else:
            c  = self.clr
            tc = self.txt_clr
        pygame.draw.rect(surf, c,              self.rect, border_radius=self.radius)
        pygame.draw.rect(surf, lighter(c, 1.3),self.rect, 1, border_radius=self.radius)
        s = self.font.render(self.text, True, tc)
        surf.blit(s, s.get_rect(center=self.rect.center))

    def update(self, mpos):
        self.hovered = self.rect.collidepoint(mpos) and self.enabled

    def clicked(self, ev):
        return (ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1
                and self.rect.collidepoint(ev.pos) and self.enabled)

# ── Layout ────────────────────────────────────────────────────────────────────
LP   = 18          # padding esquerdo interno
LW   = 215         # largura do painel esquerdo
RX   = W - 220     # x de início do painel direito
CX   = (LW + RX) // 2   # centro da área dos dados  (≈ 640)
CY   = H // 2 + 20      # centro vertical dos dados  (≈ 380)

# ── Botões dos dados ──────────────────────────────────────────────────────────
dice_btns: dict[str, Button] = {}
for i, d in enumerate(DICE_LIST):
    dc = DICE_CLR[d]
    b  = Button(
        rect=(LP, 88 + i * 66, LW - 2 * LP, 52),
        text=d, clr=PANEL2, hover=dc, txt_clr=dc,
    )
    dice_btns[d] = b

minus_btn = Button((LP,          472, 44, 44), '-', PANEL2, ACCENT, ACCENT, F_QTY)
plus_btn  = Button((LW - LP - 44, 472, 44, 44), '+', PANEL2, ACCENT, ACCENT, F_QTY)
roll_btn  = Button(
    rect=(LP, 578, LW - 2 * LP, 64),
    text='>> JOGAR <<', clr=ACCENT, hover=ACC_DARK,
    txt_clr=WHITE, radius=10,
)

all_btns = list(dice_btns.values()) + [minus_btn, plus_btn, roll_btn]

# ── Estado do jogo ────────────────────────────────────────────────────────────
sel_dice   = 'D20'
quantity   = 1
is_rolling = False
anim_t     = 0.0
ANIM_DUR   = 1.9

roll_vals: list[int] = []   # resultado final
disp_vals: list[int] = []   # exibido durante animação
hist_lines: list[str] = []
total_val  = None
result_t   = 0.0            # timer pós-resultado para bounce

# ── Lógica ────────────────────────────────────────────────────────────────────
def select_dice(d: str):
    global sel_dice
    sel_dice = d
    for name, b in dice_btns.items():
        b.active = (name == d)

def change_qty(delta: int):
    global quantity
    quantity = max(1, min(8, quantity + delta))

def start_roll():
    global is_rolling, anim_t, roll_vals, disp_vals, total_val, result_t
    if is_rolling:
        return
    is_rolling = True
    anim_t     = 0.0
    result_t   = 0.0
    total_val  = None
    sides      = DICE_SIDES[sel_dice]
    roll_vals  = [random.randint(1, sides) for _ in range(quantity)]
    disp_vals  = [random.randint(1, sides) for _ in range(quantity)]
    roll_btn.enabled = False

def finish_roll():
    global is_rolling, disp_vals, total_val, hist_lines
    is_rolling = False
    roll_btn.enabled = True
    disp_vals  = list(roll_vals)
    total_val  = sum(roll_vals)
    rolls_str  = ','.join(str(v) for v in roll_vals)
    line       = f'{quantity}{sel_dice}: [{rolls_str}]={total_val}'
    hist_lines.insert(0, line[:27])
    if len(hist_lines) > 13:
        hist_lines = hist_lines[:13]

# ── Grade de perspectiva ──────────────────────────────────────────────────────
def draw_grid(surf):
    horizon = H // 2 - 60
    vpx     = CX
    vpy     = horizon
    gcol    = (20, 20, 55)
    # horizontais
    for i in range(14):
        t = (i / 13) ** 1.4
        y = int(horizon + (H - horizon) * t)
        if LW < y < RX:
            pass
        pygame.draw.line(surf, gcol, (LW, y), (RX, y), 1)
    # verticais (ponto de fuga)
    for i in range(17):
        t  = i / 16
        x  = int(LW + (RX - LW) * t)
        pygame.draw.line(surf, gcol, (vpx, vpy), (x, H), 1)

# ── Renderização principal ────────────────────────────────────────────────────
def draw(surf):
    surf.fill(BG)

    # Área central
    draw_grid(surf)

    # Painel esquerdo
    pygame.draw.rect(surf, PANEL,  (0, 0, LW, H))
    pygame.draw.rect(surf, BORDER, (0, 0, LW, H), 1)

    # Painel direito
    pygame.draw.rect(surf, PANEL,  (RX, 0, W - RX, H))
    pygame.draw.rect(surf, BORDER, (RX, 0, W - RX, H), 1)

    # Barra de título
    pygame.draw.rect(surf, PANEL2, (0, 0, W, 52))
    pygame.draw.line(surf, ACCENT, (0, 52), (W, 52), 2)
    txt_c(surf, 'ooo   RPG DICE ROLLER   ooo', F_TITLE, GOLD, W // 2, 26)

    # ── Painel esquerdo ───────────────────────────────────────────────────────
    txt_c(surf, 'TIPO DE DADO', F_LABEL, SUBTEXT, LW // 2, 70)

    for d, b in dice_btns.items():
        b.draw(surf)
        dc = DICE_CLR[d]
        pygame.draw.rect(surf, dc, (LP, b.rect.y, 4, 52), border_radius=2)

    txt_c(surf, 'QUANTIDADE', F_LABEL, SUBTEXT, LW // 2, 450)
    minus_btn.draw(surf)
    plus_btn.draw(surf)
    txt_c(surf, str(quantity), F_QTY, WHITE, LW // 2, 494)

    roll_btn.draw(surf)

    txt_c(surf, '[SPACE] rolar', F_SMALL, SUBTEXT, LW // 2, 660)
    txt_c(surf, '[ESC]   sair',  F_SMALL, SUBTEXT, LW // 2, 676)

    # ── Área dos dados ────────────────────────────────────────────────────────
    n = max(len(disp_vals), 1)
    gap = min(155, (RX - LW - 40) // n)
    r   = min(72,  gap // 2 - 6)
    ox  = CX - (n - 1) * gap // 2

    if disp_vals:
        for i, v in enumerate(disp_vals):
            dx = ox + i * gap
            if is_rolling:
                phase = (anim_t * 7.5 + i * 1.3) % (2 * math.pi)
                sx    = max(0.06, abs(math.cos(phase)))
            else:
                # bounce de entrada
                bounce = math.sin(min(result_t * 4, math.pi)) * 0.25
                sx     = 1.0 + bounce * max(0, 1 - result_t * 2)
            draw_die(surf, sel_dice, dx, CY, r, v, sx=sx)
    else:
        txt_c(surf, f'Selecione {sel_dice} e pressione JOGAR',
              F_LABEL, SUBTEXT, CX, CY)

    # ── Total ─────────────────────────────────────────────────────────────────
    if total_val is not None and not is_rolling:
        bw, bh = 420, 54
        bx, by = CX - bw // 2, H - 70
        pygame.draw.rect(surf, PANEL2, (bx, by, bw, bh), border_radius=10)
        pygame.draw.rect(surf, GOLD,   (bx, by, bw, bh), 1, border_radius=10)
        txt_c(surf, f'TOTAL:  {total_val}', F_TOTAL, GOLD, CX, by + bh // 2)
        if len(roll_vals) > 1:
            subs = '  +  '.join(str(v) for v in roll_vals)
            txt_c(surf, subs, F_SMALL, SUBTEXT, CX, H - 10)

    # ── Painel direito ────────────────────────────────────────────────────────
    txt_c(surf, 'HISTORICO', F_LABEL, SUBTEXT, RX + 110, 70)
    pygame.draw.line(surf, BORDER, (RX + 10, 85), (W - 10, 85), 1)

    for i, line in enumerate(hist_lines):
        y = 92 + i * 46
        if y + 42 > H - 10:
            break
        dtype = next((d for d in DICE_LIST if d in line), 'D20')
        dc    = DICE_CLR[dtype]
        pygame.draw.rect(surf, PANEL2, (RX + 8, y, 200, 38), border_radius=5)
        pygame.draw.rect(surf, dc,     (RX + 8, y,   3, 38), border_radius=2)

        # linha superior: tipo + resultado
        label_part = line.split('=')[0] if '=' in line else line
        total_part = line.split('=')[1] if '=' in line else ''
        txt(surf, label_part[:18], F_HIST, SUBTEXT, RX + 16, y + 4)
        if total_part:
            ts = F_LABEL.render('= ' + total_part, True, dc)
            surf.blit(ts, (RX + 16, y + 20))

    # ── Linha de rodapé ───────────────────────────────────────────────────────
    pygame.draw.line(surf, ACCENT, (0, H - 3), (W, H - 3), 3)

    pygame.display.flip()

# ── Selecção inicial ──────────────────────────────────────────────────────────
select_dice('D20')

# ── Loop principal ────────────────────────────────────────────────────────────
running = True
while running:
    dt      = clock.tick(FPS) / 1000.0
    mpos    = pygame.mouse.get_pos()
    sides   = DICE_SIDES[sel_dice]

    for b in all_btns:
        b.update(mpos)

    for ev in pygame.event.get():
        if ev.type == pygame.QUIT:
            running = False

        elif ev.type == pygame.KEYDOWN:
            if ev.key == pygame.K_ESCAPE:
                running = False
            elif ev.key == pygame.K_SPACE and not is_rolling:
                start_roll()

        # Cliques
        for d, b in dice_btns.items():
            if b.clicked(ev):
                select_dice(d)
        if minus_btn.clicked(ev):
            change_qty(-1)
        if plus_btn.clicked(ev):
            change_qty(1)
        if roll_btn.clicked(ev):
            start_roll()

    # Animação de rolagem
    if is_rolling:
        anim_t += dt
        # números piscam cada vez mais devagar
        flash_speed = max(4, 22 - int(anim_t * 13))
        ticks_now  = int(anim_t * flash_speed * 3)
        ticks_prev = int((anim_t - dt) * flash_speed * 3)
        if ticks_now != ticks_prev:
            disp_vals = [random.randint(1, sides) for _ in range(quantity)]
        if anim_t >= ANIM_DUR:
            finish_roll()

    if not is_rolling and total_val is not None:
        result_t = min(2.0, result_t + dt)

    draw(screen)

pygame.quit()
sys.exit()
