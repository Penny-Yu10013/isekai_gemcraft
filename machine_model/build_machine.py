# -*- coding: utf-8 -*-
# 異世界魔法石工坊 — 寶石切割機模型(實機骨架+魔法點綴)
# 用法: blender -b --factory-startup -P build_machine.py
# 產出: gem_faceting_machine.blend + render_34.png + render_head.png
import bpy, bmesh, math, os
from mathutils import Vector, Quaternion, Matrix

OUT = os.path.dirname(os.path.abspath(__file__))

# ---------- 清場 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

root_col = bpy.data.collections.new("GemMachine")
scene.collection.children.link(root_col)

def link(obj):
    root_col.objects.link(obj)
    return obj

# ---------- 材質 ----------
def mat(name, color, metallic=0.0, rough=0.5, emit=None, emit_str=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    def set_in(n, v):
        if n in bsdf.inputs: bsdf.inputs[n].default_value = v
    set_in("Base Color", (*color, 1.0))
    set_in("Metallic", metallic)
    set_in("Roughness", rough)
    if emit:
        set_in("Emission Color", (*emit, 1.0))
        set_in("Emission Strength", emit_str)
    return m

M_iron   = mat("iron_black",   (0.030,0.030,0.042),0.08,0.50)   # 深色烤漆鑄鐵
M_steel  = mat("steel_polish", (0.62,0.63,0.68),   0.95,0.22)
M_brass  = mat("brass",        (0.62,0.42,0.11),   0.95,0.35)
M_rubber = mat("rubber",       (0.02,0.02,0.02),   0.0, 0.9)
M_lap    = mat("lap_steel",    (0.30,0.32,0.38),   0.45,0.42)
M_dark   = mat("groove_dark",  (0.04,0.04,0.055),  0.0, 0.7)
M_cryst  = mat("crystal_purple",(0.42,0.25,0.92),  0.0, 0.25, emit=(0.45,0.30,0.95), emit_str=0.6)
M_rune   = mat("rune_gold",    (0.9,0.7,0.32),     0.6, 0.35, emit=(1.0,0.80,0.42), emit_str=0.9)
M_water  = mat("water_glow",   (0.25,0.85,0.9),    0.0, 0.1, emit=(0.3,0.9,0.95), emit_str=1.6)
M_glow   = mat("underglow",    (0.3,0.2,0.6),      0.0, 0.5, emit=(0.42,0.28,0.9), emit_str=0.8)

# ---------- 幾何工具 ----------
def cyl(name, r, depth, loc, mat_, verts=32, rot_quat=None, axis=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc)
    o = bpy.context.active_object; o.name = name
    o.data.materials.append(mat_)
    if rot_quat:
        o.rotation_mode='QUATERNION'; o.rotation_quaternion = rot_quat
    elif axis=='Y': o.rotation_euler=(math.pi/2,0,0)
    elif axis=='X': o.rotation_euler=(0,math.pi/2,0)
    for c in scene.collection.objects:
        if c==o: scene.collection.objects.unlink(o)
    return link(o)

def box(name, dims, loc, mat_, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object; o.name=name
    o.scale = (dims[0]/2, dims[1]/2, dims[2]/2)
    if rot: o.rotation_euler = rot
    o.data.materials.append(mat_)
    for c in scene.collection.objects:
        if c==o: scene.collection.objects.unlink(o)
    return link(o)

def torus(name, R, r, loc, mat_, rot=None, maj=48, minor=10):
    bpy.ops.mesh.primitive_torus_add(major_radius=R, minor_radius=r, location=loc,
                                     major_segments=maj, minor_segments=minor)
    o = bpy.context.active_object; o.name=name
    if rot: o.rotation_euler=rot
    o.data.materials.append(mat_)
    for c in scene.collection.objects:
        if c==o: scene.collection.objects.unlink(o)
    return link(o)

def ico(name, r, loc, mat_, subdiv=1):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdiv, radius=r, location=loc)
    o = bpy.context.active_object; o.name=name
    o.data.materials.append(mat_)
    for c in scene.collection.objects:
        if c==o: scene.collection.objects.unlink(o)
    return link(o)

def ring_of_boxes(name, count, ring_r, dims, center, normal_quat, mat_):
    """count 個小方塊繞環排列(齒/刻度),單一 mesh。normal_quat 把局部 Z 轉到環軸。"""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    for k in range(count):
        th = k/count*2*math.pi
        loc = Vector((math.cos(th)*ring_r, math.sin(th)*ring_r, 0))
        rot = Matrix.Rotation(th, 4, 'Z')
        sca = Matrix.Diagonal((dims[0], dims[1], dims[2], 1))
        bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation(loc) @ rot @ sca)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    o.data.materials.append(mat_)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=normal_quat
    o.location = center
    return link(o)

Z = Vector((0,0,1))
QID = Quaternion()

# ============================================================
# 底座
# ============================================================
base = box("Base", (0.46,0.36,0.07), (0,0,0.045), M_iron)
bev = base.modifiers.new("bev","BEVEL"); bev.width=0.012; bev.segments=3
for sx,sy in ((1,1),(1,-1),(-1,1),(-1,-1)):
    cyl(f"Foot_{sx}_{sy}", 0.014, 0.012, (sx*0.20, sy*0.15, 0.006), M_rubber, verts=16)
# 底部魔法微光
box("UnderGlow", (0.40,0.30,0.002), (0,0,0.004), M_glow)

# ============================================================
# 地面魔法陣(MC_* 獨立命名,遊戲端可整組做脈動微光)
# 8 芒星=兩正方形疊 45°,呼應遊戲的 8 折對稱
# ============================================================
M_mcP = mat("mc_purple",(0.35,0.22,0.80),0.0,0.4, emit=(0.50,0.32,1.0), emit_str=1.1)
M_mcG = mat("mc_gold",  (0.80,0.62,0.28),0.3,0.4, emit=(1.0,0.80,0.42), emit_str=0.9)
mc_z = 0.0035
torus("MC_RingOuter",  0.440,0.0028,(0,0,mc_z),M_mcP,maj=96,minor=6)
torus("MC_RingOuter2", 0.415,0.0016,(0,0,mc_z),M_mcP,maj=96,minor=6)
torus("MC_RingInner",  0.300,0.0020,(0,0,mc_z),M_mcG,maj=64,minor=6)
ring_of_boxes("MC_Runes",32,0.4275,(0.014,0.0035,0.0022),Vector((0,0,mc_z)),QID,M_mcG)
def square_edges(name, r_sq, rot0, mat_):
    pts=[Vector((math.cos(rot0+k*math.pi/2)*r_sq, math.sin(rot0+k*math.pi/2)*r_sq, mc_z)) for k in range(4)]
    for k in range(4):
        a,b=pts[k],pts[(k+1)%4]; m=(a+b)/2; e=b-a
        box(f"{name}_{k}",(e.length,0.0035,0.0022),m,mat_,rot=(0,0,math.atan2(e.y,e.x)))
square_edges("MC_StarA",0.30,0.0,M_mcP)
square_edges("MC_StarB",0.30,math.pi/4,M_mcP)
for k in range(8):
    th=k*math.pi/4+math.pi/8
    box(f"MC_Spoke_{k}",(0.115,0.0028,0.002),
        Vector((math.cos(th)*0.3575,math.sin(th)*0.3575,mc_z)),M_mcP,rot=(0,0,th))
# 微光閃爍:發光強度掛噪聲動畫(fr 1-250;GLB 不帶材質動畫,遊戲端用程式脈動)
try:
    for m_,base_,amp in ((M_mcP,1.1,0.45),(M_mcG,0.9,0.30)):
        inp=m_.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        inp.default_value=base_
        inp.keyframe_insert("default_value",frame=1)
        ad=m_.node_tree.animation_data; act=ad.action
        # Blender 5.x slotted actions:fcurve 在 layer→strip→channelbag 裡
        try:
            fcs=act.layers[0].strips[0].channelbag(ad.action_slot).fcurves
        except Exception:
            fcs=act.fcurves  # 舊版 fallback
        for fc in fcs:
            nm=fc.modifiers.new('NOISE'); nm.scale=30; nm.strength=amp; nm.phase=(hash(m_.name)%97)
    print("MC_FLICKER_OK")
except Exception as e:
    print("MC_FLICKER_SKIP", e)
# 前面板(-Y 側,面對主視角):雙旋鈕 + 水晶動力窗
for i,x in enumerate((0.10,0.16)):
    cyl(f"Knob_{i}", 0.018, 0.022, (x, -0.181, 0.045), M_brass, verts=24, axis='Y')
    cyl(f"KnobCap_{i}", 0.006, 0.026, (x, -0.181, 0.045), M_dark, verts=12, axis='Y')
torus("CrystalPort", 0.030, 0.006, (-0.12, -0.180, 0.045), M_brass, rot=(math.pi/2,0,0), maj=32, minor=10)
cyl("CrystalWindow", 0.026, 0.008, (-0.12, -0.178, 0.045), M_cryst, verts=24, axis='Y')

# ============================================================
# 研磨盤(lap)+ 濺盤 + 符文環
# ============================================================
L = Vector((-0.10, 0.0, 0))
cyl("PanBottom", 0.150, 0.006, (L.x, L.y, 0.073), M_iron, verts=48)
cyl("PanWall",   0.150, 0.030, (L.x, L.y, 0.088), M_iron, verts=48)
torus("PanRim", 0.150, 0.005, (L.x, L.y, 0.103), M_iron, maj=48, minor=10)
cyl("LapDisk", 0.125, 0.008, (L.x, L.y, 0.099), M_lap, verts=64)
cyl("SpindleNut", 0.013, 0.014, (L.x, L.y, 0.109), M_brass, verts=6)
for i,rr in enumerate((0.05,0.08,0.105)):
    torus(f"Groove_{i}", rr, 0.0012, (L.x, L.y, 0.1035), M_dark, maj=48, minor=6)
torus("RuneRing", 0.118, 0.0018, (L.x, L.y, 0.1035), M_rune, maj=64, minor=6)

# ============================================================
# 滴水壺(魔法水滴)
# ============================================================
W = Vector((-0.185,-0.145,0))
cyl("DripRod", 0.005, 0.14, (W.x, W.y, 0.14), M_steel, verts=12)
cyl("DripTank", 0.028, 0.08, (W.x, W.y, 0.175), M_brass, verts=24)
cyl("DripLid", 0.030, 0.006, (W.x, W.y, 0.218), M_iron, verts=24)
# 出水臂:起點埋進壺壁,肘部/出水口加球接頭,管線連續不斷
A1 = Vector((-0.145,-0.055,0.185))
dir_h = Vector((A1.x-W.x, A1.y-W.y, 0)).normalized()
A0 = Vector((W.x, W.y, 0.205)) + dir_h*0.012
mid = (A0+A1)/2; dvec = A1-A0
qa = Vector((0,0,1)).rotation_difference(dvec.normalized())
cyl("DripArm", 0.004, dvec.length+0.010, mid, M_brass, verts=12, rot_quat=qa)
ico("DripElbow", 0.0056, A1, M_brass, subdiv=2)
cyl("DripTip", 0.004, 0.030, (A1.x, A1.y, A1.z-0.015), M_brass, verts=12)
ico("DripNozzle", 0.0052, (A1.x, A1.y, A1.z-0.030), M_brass, subdiv=2)
ico("WaterDrop", 0.005, (A1.x, A1.y, 0.140), M_water, subdiv=2)

# ============================================================
# 桅杆(mast)+ 滑座
# ============================================================
MX = Vector((0.18,-0.02,0))
box("MastPlatform", (0.11,0.11,0.022), (MX.x, MX.y, 0.081), M_iron)
cyl("HeightWheel", 0.030, 0.014, (MX.x+0.048, MX.y, 0.079), M_brass, verts=24, axis='X')
cyl("Mast", 0.015, 0.36, (MX.x, MX.y, 0.272), M_steel, verts=24)
ico("MastCap", 0.017, (MX.x, MX.y, 0.455), M_brass, subdiv=2)
carr_z = 0.27
cyl("Carriage", 0.026, 0.055, (MX.x, MX.y, carr_z), M_brass, verts=24)
torus("CarriageRune", 0.027, 0.0022, (MX.x, MX.y, carr_z+0.012), M_rune, maj=32, minor=6)
cyl("ClampLever", 0.005, 0.05, (MX.x, MX.y+0.035, carr_z), M_dark, verts=10, axis='Y')

# ============================================================
# 切割頭:量角器盤 + quill 臂 + 96齒分度輪 + dop + 原石
# ============================================================
P = Vector((0.15,-0.02, carr_z))            # 量角器/quill 樞紐
T = Vector((-0.02, 0.0, 0.095))             # 石頭接觸點(lap 面上)
d = (T-P).normalized(); Ltot = (T-P).length
q = Vector((0,0,-1)).rotation_difference(d) # 局部 -Z 對準切割方向
def at(t): return P + d*t

# 樞紐臂(滑座→樞紐)
arm_mid = (Vector((MX.x,MX.y,carr_z))+P)/2
cyl("HeadArm", 0.010, (P-Vector((MX.x,MX.y,carr_z))).length+0.02, arm_mid, M_steel, verts=16, axis='X')
# 量角器圓盤:法線=傾斜平面法線(d × Z),翻到面對相機(-Y)側
n_dial = d.cross(Z).normalized()
if n_dial.y > 0: n_dial = -n_dial
q_dial = Vector((0,0,1)).rotation_difference(n_dial)
cyl("DialAxle", 0.006, 0.030, P + n_dial*0.008, M_steel, verts=12, rot_quat=q_dial)
cyl("ProtractorDial", 0.050, 0.008, P + n_dial*0.014, M_iron, verts=48, rot_quat=q_dial)
torus("DialRim", 0.050, 0.0028, P + n_dial*0.014, M_brass, rot=q_dial.to_euler(), maj=48, minor=8)
ring_of_boxes("DialTicks", 24, 0.042, (0.009,0.0016,0.0022), P + n_dial*0.019, q_dial, M_rune)
# quill 主臂
qlen = 0.15
cyl("Quill", 0.011, qlen, at(qlen/2 - 0.02), M_steel, verts=20, rot_quat=q)
# 96 齒分度輪(quill 後端,離量角器盤遠一點)
gear_t = -0.075
cyl("IndexGear", 0.034, 0.012, at(gear_t), M_brass, verts=48, rot_quat=q)
ring_of_boxes("GearTeeth", 96, 0.0355, (0.0032,0.0016,0.010), at(gear_t), q, M_brass)
cyl("GearHub", 0.008, 0.020, at(gear_t), M_dark, verts=12, rot_quat=q)
# 棘爪(pawl):貼在齒輪頂,沿切線方向
pq = q @ Quaternion(Vector((0,1,0)), math.radians(90))
cyl("Pawl", 0.004, 0.026, at(gear_t) + (q @ Vector((0,0.0405,0))), M_steel, verts=10, rot_quat=pq)
cyl("Cheater", 0.009, 0.016, at(-0.012) + (q @ Vector((0.028,0,0))), M_brass, verts=16,
    rot_quat=q @ Quaternion(Vector((0,1,0)), math.radians(90)))
# dop 夾頭 → dop 桿 → 封蠟 → 原石(紫水晶粗胚)
t_stone = Ltot - 0.008
cyl("DopChuck", 0.009, 0.028, at(qlen-0.02+0.014), M_brass, verts=16, rot_quat=q)
rod_a = qlen-0.02+0.028; rod_b = t_stone-0.024
cyl("DopRod", 0.0035, rod_b-rod_a, at((rod_a+rod_b)/2), M_steel, verts=12, rot_quat=q)
bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=0.0075, radius2=0.003,
    depth=0.018, location=at(t_stone-0.015))
wax = bpy.context.active_object; wax.name="DopWax"
wax.rotation_mode='QUATERNION'; wax.rotation_quaternion=q @ Quaternion(Vector((1,0,0)), math.pi)
wax.data.materials.append(mat("wax_brown",(0.09,0.045,0.018),0.0,0.85))
scene.collection.objects.unlink(wax); link(wax)
ico("RoughStone", 0.015, at(t_stone), M_cryst, subdiv=1)

# ============================================================
# 燈光 / 相機 / 世界
# ============================================================
world = bpy.data.worlds.new("W"); scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
bg.inputs[0].default_value = (0.030,0.020,0.062,1); bg.inputs[1].default_value = 1.0  # 紫色背景

def area(name, loc, energy, color, size):
    ld = bpy.data.lights.new(name,'AREA'); ld.energy=energy; ld.color=color; ld.size=size
    lo = bpy.data.objects.new(name, ld); lo.location=loc
    c = bpy.data.objects.new(name+"_t", None); c.location=(0,0,0.15)
    tr = lo.constraints.new('TRACK_TO'); tr.target=c
    root_col.objects.link(lo); root_col.objects.link(c)
    return lo
area("Key",  (0.55,-0.70,0.80), 13, (1.0,0.95,0.87), 0.45)
area("RimP", (-0.75,0.55,0.55),  8, (0.55,0.40,1.0), 0.55)
area("Fill", (-0.35,-0.75,0.25), 3.5,(0.8,0.88,1.0), 0.4)
# 地板:接影子與底部紫暈
bpy.ops.mesh.primitive_plane_add(size=4, location=(0,0,-0.001))
floor_o = bpy.context.active_object; floor_o.name="Floor"
floor_o.data.materials.append(mat("floor_dark",(0.022,0.016,0.050),0.0,0.85))
scene.collection.objects.unlink(floor_o); link(floor_o)

cam_d = bpy.data.cameras.new("Cam"); cam_d.lens=55
cam = bpy.data.objects.new("Cam", cam_d); root_col.objects.link(cam)
scene.camera = cam
target = bpy.data.objects.new("CamTarget", None); root_col.objects.link(target)
tr = cam.constraints.new('TRACK_TO'); tr.target = target

scene.render.engine = 'CYCLES'
scene.cycles.samples = 48
scene.cycles.use_denoising = True
scene.render.resolution_x = 960; scene.render.resolution_y = 720
# 色彩轉換:接近 Three.js/遊戲觀感,顏色不被 AgX 沖淡
try: scene.view_settings.view_transform = 'Khronos PBR Neutral'
except Exception:
    try: scene.view_settings.view_transform = 'Standard'
    except Exception: pass

# ---------- 存檔 ----------
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "gem_faceting_machine.blend"))

# ---------- 渲染兩個視角 ----------
def shoot(name, cam_loc, tgt):
    cam.location = cam_loc; target.location = tgt
    bpy.context.view_layer.update()
    scene.render.filepath = os.path.join(OUT, name)
    bpy.ops.render.render(write_still=True)

scene.frame_set(120)  # 取閃爍中段的發光值
shoot("render_34.png",   (0.66,-0.76,0.52), (0.0,-0.01,0.12))
shoot("render_head.png", (0.30,-0.28,0.34), (0.11,-0.02,0.23))
shoot("render_front.png",(-0.06,-0.80,0.26),(0.0,0.0,0.12))

# ---------- GLB 輸出(未來進 Three.js 用) ----------
floor_o.hide_render = True
for o in root_col.objects:
    o.select_set(o.type=='MESH' and o.name not in ('Floor',))
try:
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,"gem_faceting_machine.glb"),
        use_selection=True, export_apply=True)
    print("GLB_OK")
except Exception as e:
    print("GLB_FAIL", e)

tris = sum(len(o.data.polygons) for o in root_col.objects if o.type=='MESH')
print("BUILD_OK faces=%d objects=%d" % (tris, len(root_col.objects)))
