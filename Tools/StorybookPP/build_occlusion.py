"""Occlusion cutout prototype: MPC + material function + hook into wall masters.

Run inside the editor (execute_python / runpy).  Idempotent.
  build()            -> MPC, MF, hooks M_Master + M_PrototypeGrid, enables the wall MIs
  set_target(...)    -> preview helper: writes MPC values in the editor world (not saved)

Masters stay Opaque; the hook is behind a static switch "OcclusionCutout"
(default off), and only MIs that turn it on override their blend mode to
Masked.  Floors / stairs / props sharing the same master are untouched.
"""
import os
import unreal

mel = unreal.MaterialEditingLibrary
atools = unreal.AssetToolsHelpers.get_asset_tools()
HERE = os.path.join(unreal.Paths.project_dir(), "Tools", "StorybookPP")

MPC_PATH = "/Game/Dev/Materials/MPC_Occlusion"
MF_PATH = "/Game/Dev/Materials/Functions/MF_OcclusionCutout"
SWITCH = "OcclusionCutout"

SCALARS = [("Enable", 0.0), ("Radius", 170.0), ("NearMargin", 60.0), ("FootOffset", -40.0),
           ("EdgeNoise", 0.12), ("RimWidth", 0.06)]
VECTORS = [("Target", (0.0, 0.0, 0.0, 0.0)), ("RimColor", (0.55, 0.36, 0.22, 1.0))]

MASTERS = {
    "/Game/Dev/Materials/M_Master": "MaterialExpressionStaticSwitchParameter_1",
    "/Game/LevelPrototyping/Materials/M_PrototypeGrid": "MaterialExpressionLinearInterpolate_5",
}
WALL_MIS = ["/Game/Dev/Materials/" + n for n in [
    "MI_StoneWall01", "MI_StoneWallDecor", "MI_StoneWallWindow", "MI_StoneWallDamaged",
    "MI_StoneCliff01", "MI_StoneCliff02", "MI_StoneCliff03", "MI_StoneCliff04", "MI_StoneCliff05",
    "MI_StoneCliff06", "MI_StoneCliff07", "MI_StoneCliff08", "MI_StoneCliff09", "MI_StoneCliff10",
    "MI_StoneCliff11", "MI_StoneArchway", "MI_StoneArchRuined", "MI_StoneMonument",
]] + ["/Game/Project/Art/Materials/MI_MazeWall"]


def _get_or_create(path, cls, factory):
    a = unreal.load_asset(path)
    if a:
        return a, False
    folder, name = path.rsplit("/", 1)
    return atools.create_asset(name, folder, cls, factory), True


def build_mpc():
    mpc, _ = _get_or_create(MPC_PATH, unreal.MaterialParameterCollection,
                            unreal.MaterialParameterCollectionFactoryNew())
    have_s = {str(p.get_editor_property("parameter_name")) for p in mpc.get_editor_property("scalar_parameters")}
    have_v = {str(p.get_editor_property("parameter_name")) for p in mpc.get_editor_property("vector_parameters")}
    sc = list(mpc.get_editor_property("scalar_parameters"))
    for n, d in SCALARS:
        if n not in have_s:
            p = unreal.CollectionScalarParameter()
            p.set_editor_property("parameter_name", n)
            p.set_editor_property("default_value", d)
            sc.append(p)
    vc = list(mpc.get_editor_property("vector_parameters"))
    for n, d in VECTORS:
        if n not in have_v:
            p = unreal.CollectionVectorParameter()
            p.set_editor_property("parameter_name", n)
            p.set_editor_property("default_value", unreal.LinearColor(*d))
            vc.append(p)
    mpc.set_editor_property("scalar_parameters", sc)
    mpc.set_editor_property("vector_parameters", vc)
    unreal.EditorAssetLibrary.save_loaded_asset(mpc)
    return mpc


def _coll(mf, mpc, name, x, y):
    e = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionCollectionParameter, x, y)
    e.set_editor_property("collection", mpc)
    e.set_editor_property("parameter_name", name)
    return e


def build_mf(mpc):
    mf, created = _get_or_create(MF_PATH, unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    mel.delete_all_material_expressions_in_function(mf)
    with open(os.path.join(HERE, "Occlusion_Cutout.hlsl"), encoding="utf-8") as f:
        code = f.read()

    inp = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionFunctionInput, -900, -300)
    inp.set_editor_property("input_name", "BaseColor")
    inp.set_editor_property("input_type", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3)
    inp.set_editor_property("sort_priority", 0)

    custom = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionCustom, -300, 0)
    custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    names = ["WorldPos", "CamPos", "Target"] + [s[0] for s in SCALARS]
    ins = []
    for n in names:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        ins.append(ci)
    custom.set_editor_property("inputs", ins)
    custom.set_editor_property("code", code)
    custom.set_editor_property("description", "OcclusionCutout")

    wp = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionWorldPosition, -700, -100)
    cp = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionCameraPositionWS, -700, -40)
    mel.connect_material_expressions(wp, "", custom, "WorldPos")
    mel.connect_material_expressions(cp, "", custom, "CamPos")
    tgt = _coll(mf, mpc, "Target", -700, 20)
    mel.connect_material_expressions(tgt, "", custom, "Target")
    for i, (n, _) in enumerate(SCALARS):
        e = _coll(mf, mpc, n, -700, 100 + i * 60)
        mel.connect_material_expressions(e, "", custom, n)

    m_r = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionComponentMask, 0, 0)
    m_r.set_editor_property("r", True); m_r.set_editor_property("g", False)
    m_r.set_editor_property("b", False); m_r.set_editor_property("a", False)
    m_g = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionComponentMask, 0, 100)
    m_g.set_editor_property("r", False); m_g.set_editor_property("g", True)
    m_g.set_editor_property("b", False); m_g.set_editor_property("a", False)
    mel.connect_material_expressions(custom, "", m_r, "")
    mel.connect_material_expressions(custom, "", m_g, "")

    rimc = _coll(mf, mpc, "RimColor", -300, -200)
    rim_rgb = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionComponentMask, 0, -200)
    rim_rgb.set_editor_property("r", True); rim_rgb.set_editor_property("g", True)
    rim_rgb.set_editor_property("b", True); rim_rgb.set_editor_property("a", False)
    mel.connect_material_expressions(rimc, "", rim_rgb, "")
    lerp = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionLinearInterpolate, 250, -250)
    mel.connect_material_expressions(inp, "", lerp, "A")
    mel.connect_material_expressions(rim_rgb, "", lerp, "B")
    mel.connect_material_expressions(m_g, "", lerp, "Alpha")

    o_bc = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionFunctionOutput, 500, -250)
    o_bc.set_editor_property("output_name", "BaseColor")
    o_bc.set_editor_property("sort_priority", 0)
    o_m = mel.create_material_expression_in_function(mf, unreal.MaterialExpressionFunctionOutput, 500, 0)
    o_m.set_editor_property("output_name", "OpacityMask")
    o_m.set_editor_property("sort_priority", 1)
    mel.connect_material_expressions(lerp, "", o_bc, "")
    mel.connect_material_expressions(m_r, "", o_m, "")

    mel.update_material_function(mf)
    unreal.EditorAssetLibrary.save_loaded_asset(mf)
    return mf


def hook_master(path, base_src_name, mf):
    mat = unreal.load_asset(path)
    MP = unreal.MaterialProperty
    cur = mel.get_material_property_input_node(mat, MP.MP_BASE_COLOR)
    if cur is not None and cur.get_class().get_name() == "MaterialExpressionStaticSwitchParameter" \
            and str(cur.get_editor_property("parameter_name")) == SWITCH:
        mel.recompile_material(mat)
        return f"{path}: already hooked"
    if cur is None or cur.get_name() != base_src_name:
        return f"{path}: base colour source changed ({cur.get_name() if cur else None}), not touching it"
    out_name = mel.get_material_property_input_node_output_name(mat, MP.MP_BASE_COLOR)
    x = cur.get_editor_property("material_expression_editor_x") + 300
    y = cur.get_editor_property("material_expression_editor_y")

    fc = mel.create_material_expression(mat, unreal.MaterialExpressionMaterialFunctionCall, x, y + 200)
    fc.set_editor_property("material_function", mf)
    mel.connect_material_expressions(cur, out_name, fc, "BaseColor")

    sw_bc = mel.create_material_expression(mat, unreal.MaterialExpressionStaticSwitchParameter, x + 300, y)
    sw_bc.set_editor_property("parameter_name", SWITCH)
    sw_bc.set_editor_property("default_value", False)
    sw_bc.set_editor_property("group", "Occlusion")
    mel.connect_material_expressions(fc, "BaseColor", sw_bc, "True")
    mel.connect_material_expressions(cur, out_name, sw_bc, "False")
    mel.connect_material_property(sw_bc, "", MP.MP_BASE_COLOR)

    one = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, x, y + 420)
    one.set_editor_property("r", 1.0)
    sw_m = mel.create_material_expression(mat, unreal.MaterialExpressionStaticSwitchParameter, x + 300, y + 300)
    sw_m.set_editor_property("parameter_name", SWITCH)
    sw_m.set_editor_property("default_value", False)
    sw_m.set_editor_property("group", "Occlusion")
    mel.connect_material_expressions(fc, "OpacityMask", sw_m, "True")
    mel.connect_material_expressions(one, "", sw_m, "False")
    mel.connect_material_property(sw_m, "", MP.MP_OPACITY_MASK)

    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return f"{path}: hooked"


def enable_mi(path, on=True):
    mi = unreal.load_asset(path)
    if not mi:
        return f"{path}: missing"
    mel.set_material_instance_static_switch_parameter_value(mi, SWITCH, on)
    ov = mi.get_editor_property("base_property_overrides")
    ov.set_editor_property("override_blend_mode", on)
    ov.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED if on else unreal.BlendMode.BLEND_OPAQUE)
    mi.set_editor_property("base_property_overrides", ov)
    mel.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return f"{path}: {'on' if on else 'off'}"


def build():
    mpc = build_mpc()
    mf = build_mf(mpc)
    res = [hook_master(p, src, mf) for p, src in MASTERS.items()]
    res += [enable_mi(p) for p in WALL_MIS]
    return res


def set_target(x, y, z, radius=None, enable=1.0, **scalars):
    """Preview: write MPC values for the editor world (not saved)."""
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    mpc = unreal.load_asset(MPC_PATH)
    K = unreal.MaterialLibrary  # UKismetMaterialLibrary (Kismet prefix is stripped in Python)
    K.set_vector_parameter_value(w, mpc, "Target", unreal.LinearColor(x, y, z, 0.0))
    K.set_scalar_parameter_value(w, mpc, "Enable", enable)
    if radius is not None:
        K.set_scalar_parameter_value(w, mpc, "Radius", radius)
    for k, v in scalars.items():
        K.set_scalar_parameter_value(w, mpc, k, v)
    return "ok"
