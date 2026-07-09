# -*- coding: utf-8 -*-
"""
intro_flythrough.py — 預告片開場運鏡(一次性),疊加在 gem_faceting_machine.blend 上。
不修改 build_machine.py / 原 blend;所有新增物件掛 Intro* 前綴,結果另存 intro_flythrough.blend。

用法(在 machine_model/ 目錄):
  blender -b gem_faceting_machine.blend --factory-startup -P intro_flythrough.py -- build
  blender -b gem_faceting_machine.blend --factory-startup -P intro_flythrough.py -- still 1 75 150
  blender -b gem_faceting_machine.blend --factory-startup -P intro_flythrough.py -- anim

內容:
  * 攝影機 Bezier 螺旋收近路徑(Follow Path + 領先 Empty TRACK_TO),150fr@30fps,
    末端 15 幀定格在 3/4 俯角 hero 構圖(方位對齊 Key 燈方向)
  * 魔法粒子螺旋:紫→金漸層發光細管,bevel 生長動畫與運鏡同步收尾,
    路徑刻意壓低經過 地面魔法陣 / RuneRing(z=0.1035,θ=180°) / CarriageRune(z=0.282,θ≈354°)
  * 螺旋上撒發光粒子(尾焰塵粒)
  * EEVEE + Compositor Glare(Bloom),1920x1080 PNG 序列 → intro_frames/
  * 附帶動態:研磨盤組自轉、水滴循環(原 blend 機件是靜態的,只有魔法陣材質閃爍)
"""
import bpy
import math
import os
import sys

D = bpy.data
SC = bpy.context.scene
HERE = os.path.dirname(os.path.abspath(bpy.data.filepath))

FPS = 30
F_END = 150            # 5 秒
F_ARRIVE = 135         # 攝影機/螺旋到位幀,之後定格 0.5 秒
FOCUS = (0.01, -0.01, 0.15)   # hero 注視點(與 Key_t/Fill_t 同高)

# 品牌雙色(取自場景既有材質 mc_purple / mc_gold 的 emission 色)
COL_PURPLE = (0.50, 0.32, 1.00)
COL_GOLD = (1.00, 0.80, 0.42)

# ---------------------------------------------------------------- helpers
def ease_pts():
    """運鏡節奏:前段快掃,中段減速,135 幀到位後定格。回傳 (frame, factor) 控制點。"""
    return [(1, 0.0), (50, 0.50), (100, 0.86), (F_ARRIVE, 1.0), (F_END, 1.0)]

def ease_at(frame):
    """對 ease_pts 做線性內插(烘焙領先目標用;平滑交給 keyframe bezier)。"""
    pts = ease_pts()
    if frame <= pts[0][0]:
        return pts[0][1]
    for (f0, v0), (f1, v1) in zip(pts, pts[1:]):
        if frame <= f1:
            return v0 + (v1 - v0) * (frame - f0) / (f1 - f0)
    return pts[-1][1]

def cam_pos(t):
    """攝影機螺旋參數:t=0 遠處高位,t=1 hero 構圖。方位終點對齊 Key 燈方向。"""
    th_end = math.degrees(math.atan2(-0.70, 0.55))       # ≈ -51.8°
    th = math.radians(th_end + 240.0 * (1.0 - t))        # 掃 240°收進來
    r = 2.2 + (1.50 - 2.2) * t
    z = 1.2 + (0.70 - 1.2) * t
    return (r * math.cos(th), r * math.sin(th), z)

def make_bezier(name, pts, cyclic=False):
    cu = D.curves.new(name, 'CURVE')
    cu.dimensions = '3D'
    sp = cu.splines.new('BEZIER')
    sp.bezier_points.add(len(pts) - 1)
    for bp, p in zip(sp.bezier_points, pts):
        bp.co = p
        bp.handle_left_type = bp.handle_right_type = 'AUTO'
    sp.use_cyclic_u = cyclic
    ob = D.objects.new(name, cu)
    SC.collection.objects.link(ob)
    return ob

def anim_fcurves(ob_or_id):
    """Blender 5.x slotted actions:fcurve 在 action.layers[0].strips[0].channelbag(slot)。"""
    ad = ob_or_id.animation_data
    if not (ad and ad.action):
        return []
    act = ad.action
    if hasattr(act, 'fcurves') and not act.is_action_layered:
        return act.fcurves
    try:
        cb = act.layers[0].strips[0].channelbag(ad.action_slot)
        return cb.fcurves if cb else []
    except Exception:
        return getattr(act, 'fcurves', [])

def set_interp(ob_or_id, mode='BEZIER'):
    for fc in anim_fcurves(ob_or_id):
        for kp in fc.keyframe_points:
            kp.interpolation = mode
            if mode == 'BEZIER':
                kp.handle_left_type = kp.handle_right_type = 'AUTO_CLAMPED'

def emission_mat(name, color, strength):
    m = D.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (*color, 1.0)
    em.inputs['Strength'].default_value = strength
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    return m

# ---------------------------------------------------------------- build
def build():
    # ---- 場景基本設定(整段覆寫:EEVEE / 1080p30 / 150fr) ----
    SC.render.engine = 'BLENDER_EEVEE'
    SC.render.resolution_x = 1920
    SC.render.resolution_y = 1080
    SC.render.resolution_percentage = 100
    SC.render.fps = FPS
    SC.frame_start = 1
    SC.frame_end = F_END
    SC.eevee.taa_render_samples = 64
    SC.render.image_settings.file_format = 'PNG'
    SC.render.image_settings.color_mode = 'RGB'
    SC.render.image_settings.compression = 15

    # ---- 攝影機路徑 ----
    path = make_bezier('IntroCamPath', [cam_pos(i / 14) for i in range(15)])

    cam_data = D.cameras.new('IntroCamData')
    cam_data.lens = 42
    cam_data.clip_start = 0.05
    cam_data.clip_end = 100
    cam = D.objects.new('IntroCam', cam_data)
    SC.collection.objects.link(cam)

    target = D.objects.new('IntroTarget', None)
    target.empty_display_size = 0.05
    SC.collection.objects.link(target)

    fp = cam.constraints.new('FOLLOW_PATH')
    fp.target = path
    fp.use_fixed_location = True
    tt = cam.constraints.new('TRACK_TO')
    tt.target = target
    tt.track_axis = 'TRACK_NEGATIVE_Z'
    tt.up_axis = 'UP_Y'

    # 運鏡節奏 keyframes(快掃→減速→定格)
    for f, v in ease_pts():
        fp.offset_factor = v
        cam.keyframe_insert(f'constraints["{fp.name}"].offset_factor', frame=f)
    set_interp(cam)

    # ---- 領先注視目標(往前看再到位,不死盯中心) ----
    for f in list(range(1, F_END + 1, 5)) + [F_ARRIVE, F_END]:
        e = ease_at(f)
        # 攝影機行進切線(數值微分)
        p0, p1 = cam_pos(e), cam_pos(min(e + 0.02, 1.0))
        dx, dy = p1[0] - p0[0], p1[1] - p0[1]
        L = math.hypot(dx, dy) or 1.0
        lead = 0.16 * (1.0 - e) ** 1.2          # 領先量隨接近而歸零
        target.location = (FOCUS[0] + dx / L * lead,
                           FOCUS[1] + dy / L * lead,
                           FOCUS[2] + 0.10 * (1.0 - e))
        target.keyframe_insert('location', frame=f)
    set_interp(target)
    SC.camera = cam

    # ---- 魔法粒子螺旋 ----
    # 方位錨點:z=0 從地面魔法陣外緣起,z=0.1035 經過 RuneRing(θ=180°),
    # z=0.282 經過 CarriageRune(θ≈354°),z=0.5 收在 MastCap 上方
    anchors = [(0.000, -80.0), (0.1035, 180.0), (0.282, 713.7), (0.500, 1160.0)]

    def spiral_pt(t):
        z = 0.5 * t
        for (z0, a0), (z1, a1) in zip(anchors, anchors[1:]):
            if z <= z1:
                th = math.radians(a0 + (a1 - a0) * (z - z0) / (z1 - z0))
                break
        r = 0.58 + (0.30 - 0.58) * t             # 整體隨高度收細,頂部貼緊機身
        for zp, rp in ((0.1035, 0.33), (0.282, 0.28)):   # 錨點處壓低半徑「灌注」
            g = math.exp(-((z - zp) / 0.05) ** 2)
            r = r + (rp - r) * g
        return (r * math.cos(th), r * math.sin(th), z)

    n_sp = 96
    spiral = make_bezier('IntroMagicSpiral', [spiral_pt(i / (n_sp - 1)) for i in range(n_sp)])
    scu = spiral.data
    scu.bevel_depth = 0.0028
    scu.bevel_resolution = 8
    scu.use_fill_caps = True
    scu.bevel_factor_mapping_start = scu.bevel_factor_mapping_end = 'SPLINE'

    # 生長動畫:與運鏡同節奏,135 幀一起到位
    for f, v in [(1, 0.0), (50, 0.50), (100, 0.86), (F_ARRIVE, 1.0), (F_END, 1.0)]:
        scu.bevel_factor_end = v
        scu.keyframe_insert('bevel_factor_end', frame=f)
    set_interp(scu)

    # 紫→金漸層材質(以世界 Z 0→0.5 映射,與場景 mc_purple/mc_gold 同色)
    m = D.materials.new('intro_spiral')
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    mr = nt.nodes.new('ShaderNodeMapRange')
    mr.inputs['From Min'].default_value = 0.0
    mr.inputs['From Max'].default_value = 0.5
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (*COL_PURPLE, 1.0)
    ramp.color_ramp.elements[1].color = (*COL_GOLD, 1.0)
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Strength'].default_value = 7.0
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(tc.outputs['Object'], sep.inputs['Vector'])
    nt.links.new(sep.outputs['Z'], mr.inputs['Value'])
    nt.links.new(mr.outputs['Result'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], em.inputs['Color'])
    nt.links.new(em.outputs['Emission'], out.inputs['Surface'])
    spiral.data.materials.append(m)

    # ---- 粒子塵(沿螺旋撒發光小顆) ----
    n_em = 240
    me = D.meshes.new('IntroSpiralEmit')
    me.from_pydata([spiral_pt(i / (n_em - 1)) for i in range(n_em)], [], [])
    emitter = D.objects.new('IntroSpiralEmit', me)
    SC.collection.objects.link(emitter)
    emitter.show_instancer_for_render = False
    emitter.show_instancer_for_viewport = False

    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.0035, subdivisions=1, location=(0, 0, -1.5))
    spark = bpy.context.active_object
    spark.name = 'IntroSparkInst'
    spark.data.materials.append(emission_mat('intro_spark', (1.0, 0.86, 0.60), 30.0))

    psys_mod = emitter.modifiers.new('IntroSparks', 'PARTICLE_SYSTEM')
    ps = psys_mod.particle_system.settings
    ps.type = 'EMITTER'
    ps.count = n_em
    ps.frame_start = 1
    ps.frame_end = F_ARRIVE - 2      # 出生順序沿頂點序 = 跟著生長由下往上點亮
    ps.lifetime = 34
    ps.lifetime_random = 0.4
    ps.emit_from = 'VERT'
    ps.use_emit_random = False
    ps.normal_factor = 0.0
    ps.brownian_factor = 0.03        # 塵粒輕微亂飄
    ps.drag_factor = 0.06
    ps.effector_weights.gravity = 0.0
    ps.render_type = 'OBJECT'
    ps.instance_object = spark
    ps.particle_size = 1.0
    ps.size_random = 0.6

    # ---- 附帶動態:研磨盤組自轉 + 水滴循環(blend 內機件原本靜態) ----
    for name in ('LapDisk', 'Groove_0', 'Groove_1', 'Groove_2', 'RuneRing', 'SpindleNut'):
        ob = D.objects.get(name)
        if not ob:
            continue
        ob.rotation_euler.z = 0.0
        ob.keyframe_insert('rotation_euler', index=2, frame=1)
        ob.rotation_euler.z = 3 * 2 * math.pi          # 5 秒 3 轉
        ob.keyframe_insert('rotation_euler', index=2, frame=F_END)
        set_interp(ob, 'LINEAR')

    drop = D.objects.get('WaterDrop')
    if drop:
        z0 = drop.location.z
        for f, z in ((1, 0.150), (12, 0.106), (15, 0.150)):
            drop.location.z = z
            drop.keyframe_insert('location', index=2, frame=f)
        set_interp(drop)
        for fc in anim_fcurves(drop):
            fc.modifiers.new('CYCLES')
        drop.location.z = z0

    # ---- Compositor Glare(Bloom)---- Blender 5.x:compositing_node_group + socket 化參數
    ng = D.node_groups.new('IntroComposite', 'CompositorNodeTree')
    try:
        ng.interface.new_socket('Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    except Exception as ex:
        print('[intro] interface socket:', ex)
    rl = ng.nodes.new('CompositorNodeRLayers')
    gl = ng.nodes.new('CompositorNodeGlare')
    for key, val in (('Type', 'BLOOM'), ('Quality', 'HIGH')):
        for cand in (val, val.capitalize(), val.title()):
            try:
                gl.inputs[key].default_value = cand
                break
            except Exception:
                continue
    for key, val in (('Threshold', 1.4), ('Strength', 0.50), ('Size', 0.85),
                     ('Smoothness', 0.15), ('Saturation', 1.0)):
        try:
            gl.inputs[key].default_value = val
        except Exception as ex:
            print('[intro] glare input', key, ex)
    go = ng.nodes.new('NodeGroupOutput')
    ng.links.new(rl.outputs['Image'], gl.inputs['Image'])
    ng.links.new(gl.outputs[0], go.inputs[0])
    SC.compositing_node_group = ng
    SC.render.use_compositing = True
    try:
        SC.use_nodes = True
    except Exception:
        pass

    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'intro_flythrough.blend'))
    print('[intro] build ok → intro_flythrough.blend')

# ---------------------------------------------------------------- render
def warm_sim(upto):
    """粒子模擬要從第 1 幀逐幀走到目標幀,快取才正確(單幀 still 用)。"""
    for f in range(1, upto + 1):
        SC.frame_set(f)

def render_stills(frames):
    outdir = os.path.join(HERE, 'intro_frames')
    os.makedirs(outdir, exist_ok=True)
    for f in frames:
        warm_sim(f)
        SC.render.filepath = os.path.join(outdir, f'preview_f{f:03d}.png')
        bpy.ops.render.render(write_still=True)
        print('[intro] still', f, '→', SC.render.filepath)

def render_anim():
    outdir = os.path.join(HERE, 'intro_frames')
    os.makedirs(outdir, exist_ok=True)
    SC.render.filepath = os.path.join(outdir, 'intro_')
    bpy.ops.render.render(animation=True)
    print('[intro] anim done →', outdir)

# ---------------------------------------------------------------- main
argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else ['build']
build()
if argv and argv[0] == 'still':
    render_stills([int(a) for a in argv[1:]] or [1, 75, 150])
elif argv and argv[0] == 'anim':
    render_anim()
