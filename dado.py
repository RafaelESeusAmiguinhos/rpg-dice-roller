from ursina import *
import random, math

# ── App ───────────────────────────────────────────────────────────────────────
app = Ursina()
window.title      = 'RPG Dice Roller 3D'
window.borderless = False
window.color      = color.black
try:
    window.exit_button.visible  = False
    window.fps_counter.enabled  = False
    window.cog_button.enabled   = False
except Exception:
    pass

# ── Paleta ────────────────────────────────────────────────────────────────────
GOLD    = color.rgb(245, 166, 35)
ACCENT  = color.rgb(233,  69, 96)
PANEL   = color.rgb( 14,  20, 40)
SUBTEXT = color.rgb(160, 160, 176)
DICE_CLR = {
    'D4' : color.rgb(155,  89, 182),
    'D6' : color.rgb( 52, 152, 219),
    'D8' : color.rgb( 46, 204, 113),
    'D12': color.rgb(230, 126,  34),
    'D20': color.rgb(231,  76,  60),
}
DICE_SIDES = {'D4': 4, 'D6': 6, 'D8': 8, 'D12': 12, 'D20': 20}

# ── Meshes 3D ─────────────────────────────────────────────────────────────────
def _flat(verts, tris):
    return [verts[i] for tri in tris for i in tri]

def make_tetrahedron():
    v = [Vec3(0,1,0), Vec3(-.816,-.333,.471),
         Vec3(.816,-.333,.471), Vec3(0,-.333,-.943)]
    t = [(0,1,2),(0,2,3),(0,3,1),(1,3,2)]
    return Mesh(vertices=_flat(v,t), mode='triangle')

def make_octahedron():
    v = [Vec3(0,1,0), Vec3(0,-1,0), Vec3(1,0,0),
         Vec3(-1,0,0), Vec3(0,0,1), Vec3(0,0,-1)]
    t = [(0,2,4),(0,4,3),(0,3,5),(0,5,2),
         (1,4,2),(1,3,4),(1,5,3),(1,2,5)]
    return Mesh(vertices=_flat(v,t), mode='triangle')

def make_icosahedron():
    phi = (1 + math.sqrt(5)) / 2
    raw = [(-1,phi,0),(1,phi,0),(-1,-phi,0),(1,-phi,0),
           (0,-1,phi),(0,1,phi),(0,-1,-phi),(0,1,-phi),
           (phi,0,-1),(phi,0,1),(-phi,0,-1),(-phi,0,1)]
    n = math.sqrt(1 + phi**2)
    v = [Vec3(x/n, y/n, z/n) for x,y,z in raw]
    t = [(0,11,5),(0,5,1),(0,1,7),(0,7,10),(0,10,11),
         (1,5,9),(5,11,4),(11,10,2),(10,7,6),(7,1,8),
         (3,9,4),(3,4,2),(3,2,6),(3,6,8),(3,8,9),
         (4,9,5),(2,4,11),(6,2,10),(8,6,7),(9,8,1)]
    return Mesh(vertices=_flat(v,t), mode='triangle')

def make_diamond():
    """D8 visual alternativo: bipirâmide"""
    v = [Vec3(0,1.2,0), Vec3(1,0,0), Vec3(0,0,1),
         Vec3(-1,0,0), Vec3(0,0,-1), Vec3(0,-1.2,0)]
    t = [(0,1,2),(0,2,3),(0,3,4),(0,4,1),
         (5,2,1),(5,3,2),(5,4,3),(5,1,4)]
    return Mesh(vertices=_flat(v,t), mode='triangle')

MODEL_FN = {
    'D4' : make_tetrahedron,
    'D6' : None,           # usa 'cube' nativo
    'D8' : make_diamond,
    'D12': None,           # usa 'sphere' nativo
    'D20': make_icosahedron,
}

def get_model(dtype):
    fn = MODEL_FN[dtype]
    if fn is None:
        return 'cube' if dtype == 'D6' else 'sphere'
    return fn()

# ── Estado ────────────────────────────────────────────────────────────────────
sel_dice   = 'D20'
quantity   = 1
is_rolling = False
dice_ents  = []
val_texts  = []
hist_lines = []

# ── Funções de lógica ─────────────────────────────────────────────────────────
def select_dice(d):
    global sel_dice
    sel_dice = d
    for name, btn in dice_btns.items():
        dc = DICE_CLR[name]
        if name == d:
            btn.color = dc
            btn.text_entity.color = color.black
        else:
            btn.color = color.rgb(22, 33, 62)
            btn.text_entity.color = dc

def change_qty(delta):
    global quantity
    quantity = max(1, min(8, quantity + delta))
    qty_lbl.text = str(quantity)

def clear_scene():
    global dice_ents, val_texts
    for e in dice_ents:  destroy(e)
    for t in val_texts:  destroy(t)
    dice_ents = []
    val_texts = []

def roll_dice():
    global is_rolling
    if is_rolling:
        return
    is_rolling = True
    roll_btn.enabled = False
    clear_scene()

    dtype  = sel_dice
    qty    = quantity
    sides  = DICE_SIDES[dtype]
    vals   = [random.randint(1, sides) for _ in range(qty)]
    dc     = DICE_CLR[dtype]
    gap    = min(2.6, 9.0 / max(qty, 1))
    ox     = -(qty - 1) * gap / 2

    for i, v in enumerate(vals):
        e = Entity(
            model    = get_model(dtype),
            color    = dc,
            position = Vec3(ox + i * gap, 6, 3),
            scale    = 1.15,
        )
        dice_ents.append(e)
        dur = 0.65 + random.uniform(0, 0.3)
        e.animate_position(Vec3(ox + i * gap, -0.4, 3), duration=dur, curve=curve.out_bounce)
        e.animate_rotation(
            Vec3(random.uniform(360,1080), random.uniform(360,1080), random.uniform(360,1080)),
            duration=dur + 0.15, curve=curve.out_expo,
        )

    invoke(show_results, dtype, vals, delay=1.5)

def show_results(dtype, vals):
    global is_rolling, hist_lines
    is_rolling = False
    roll_btn.enabled = True

    total    = sum(vals)
    qty      = len(vals)
    gap      = min(2.6, 9.0 / max(qty, 1))
    ox       = -(qty - 1) * gap / 2
    dc       = DICE_CLR[dtype]

    total_lbl.text  = f'TOTAL:  {total}'
    total_lbl.color = GOLD

    for i, (e, v) in enumerate(zip(dice_ents, vals)):
        t = Text(
            str(v),
            parent    = scene,
            position  = Vec3(ox + i * gap, 1.2, 3),
            scale     = 8,
            color     = color.white,
            billboard = True,
        )
        val_texts.append(t)
        e.animate_scale(1.45, duration=0.12)
        e.animate_scale(1.15, duration=0.18, delay=0.12)

    rolls_str = ' + '.join(str(v) for v in vals)
    hist_lines.insert(0, f'{qty}{dtype}  [{rolls_str}] = {total}')
    hist_lines = hist_lines[:11]
    hist_txt.text = '\n'.join(hist_lines)

# ── Câmera e iluminação ───────────────────────────────────────────────────────
camera.position  = Vec3(0, 2, -13)
camera.rotation_x = -10

DirectionalLight(y=6, z=-4, rotation=Vec3(40, -30, 0), shadows=False)
AmbientLight(color=color.rgba(70, 70, 115, 255))

# ── Cenário: chão + grade neon ────────────────────────────────────────────────
Entity(model='plane', scale=Vec3(40, 1, 26), position=Vec3(0,-2.1,4),
       color=color.rgb(5, 5, 14))

for i in range(-10, 11):
    Entity(model='cube', scale=Vec3(.012,.004,26), position=Vec3(i*1.5,-2.09,4),
           color=color.rgb(20,20,55))
for j in range(-8, 9):
    Entity(model='cube', scale=Vec3(32,.004,.012), position=Vec3(0,-2.09,j*1.4),
           color=color.rgb(20,20,55))

# Borda luminosa do chão
for x in (-7.5, 7.5):
    Entity(model='cube', scale=Vec3(.06,.06,26), position=Vec3(x,-2.06,4),
           color=ACCENT)

# ── UI — painéis de fundo ─────────────────────────────────────────────────────
Entity(parent=camera.ui, model='quad', scale=Vec2(0.30, 0.92),
       position=Vec2(-0.565, 0), color=color.rgb(12,18,38,210))
Entity(parent=camera.ui, model='quad', scale=Vec2(0.30, 0.92),
       position=Vec2( 0.565, 0), color=color.rgb(12,18,38,210))
Entity(parent=camera.ui, model='quad', scale=Vec2(1.14, 0.08),
       position=Vec2(0, 0.455), color=color.rgb(20,30,58,220))
Entity(parent=camera.ui, model='quad', scale=Vec2(0.44, 0.074),
       position=Vec2(0, -0.435), color=color.rgb(20,30,58,220))

# ── UI — título ───────────────────────────────────────────────────────────────
Text('⚔   RPG DICE ROLLER   ⚔', parent=camera.ui,
     scale=1.35, position=Vec2(0, 0.455), origin=(0,0), color=GOLD)

# ── UI — tipo de dado ─────────────────────────────────────────────────────────
Text('TIPO DE DADO', parent=camera.ui, scale=0.65,
     position=Vec2(-0.565, 0.365), origin=(0,0), color=SUBTEXT)

dice_btns = {}
for idx, d in enumerate(['D4','D6','D8','D12','D20']):
    btn = Button(
        text=d, parent=camera.ui,
        scale=Vec2(0.20, 0.068),
        position=Vec2(-0.565, 0.27 - idx * 0.096),
        color=color.rgb(22, 33, 62),
        highlight_color=DICE_CLR[d],
        pressed_color=DICE_CLR[d],
        text_color=DICE_CLR[d],
    )
    btn.on_click = (lambda d=d: select_dice(d))
    dice_btns[d] = btn

# ── UI — quantidade ───────────────────────────────────────────────────────────
Text('QUANTIDADE', parent=camera.ui, scale=0.65,
     position=Vec2(-0.565, -0.215), origin=(0,0), color=SUBTEXT)

minus_btn = Button(text='−', parent=camera.ui,
    scale=Vec2(0.068,0.068), position=Vec2(-0.655,-0.30),
    color=color.rgb(40,15,22), highlight_color=ACCENT, text_color=ACCENT)
minus_btn.on_click = lambda: change_qty(-1)

qty_lbl = Text('1', parent=camera.ui, scale=2.4,
               position=Vec2(-0.565,-0.30), origin=(0,0), color=color.white)

plus_btn = Button(text='+', parent=camera.ui,
    scale=Vec2(0.068,0.068), position=Vec2(-0.475,-0.30),
    color=color.rgb(40,15,22), highlight_color=ACCENT, text_color=ACCENT)
plus_btn.on_click = lambda: change_qty(1)

# ── UI — botão jogar ──────────────────────────────────────────────────────────
roll_btn = Button(
    text='🎲   JOGAR', parent=camera.ui,
    scale=Vec2(0.22, 0.085), position=Vec2(-0.565, -0.41),
    color=ACCENT,
    highlight_color=color.rgb(199, 54, 82),
    pressed_color=color.rgb(140, 30, 50),
    text_color=color.white,
)
roll_btn.on_click = roll_dice

# ── UI — histórico ────────────────────────────────────────────────────────────
Text('HISTÓRICO', parent=camera.ui, scale=0.65,
     position=Vec2(0.565, 0.365), origin=(0,0), color=SUBTEXT)
hist_txt = Text('', parent=camera.ui, scale=0.58,
                position=Vec2(0.425, 0.300), origin=(0,1),
                color=color.rgb(200,200,220), wordwrap=26)

# ── UI — total ────────────────────────────────────────────────────────────────
total_lbl = Text('TOTAL:  —', parent=camera.ui, scale=1.35,
                 position=Vec2(0, -0.435), origin=(0,0), color=GOLD)

# ── Dica SPACE ────────────────────────────────────────────────────────────────
Text('[SPACE] para jogar  •  [ESC] para sair', parent=camera.ui,
     scale=0.55, position=Vec2(0, -0.47), origin=(0,1),
     color=color.rgb(100,100,130))

# ── Seleção inicial ───────────────────────────────────────────────────────────
select_dice('D20')

# ── Loop de atualização ───────────────────────────────────────────────────────
def update():
    if not is_rolling:
        for e in dice_ents:
            e.rotation_y += time.dt * 28

def input(key):
    if key == 'escape':
        application.quit()
    elif key == 'space' and not is_rolling:
        roll_dice()

app.run()
