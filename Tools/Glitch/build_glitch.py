"""Comic glitch: MPC_Glitch, MF_ComicGlitch (object reload flicker), M_PP_ComicGlitch (full screen),
M_PP_ComicGlitchObject (tear limited to marked objects).

Run inside the editor (execute_python / runpy). Rebuilds the nodes each time: build().

A  object tear   M_PP_ComicGlitchObject: the full-screen print tear, only on meshes with Render
                 CustomDepth + stencil 128..255 (tear amount = (stencil-128)/127). Needs
                 r.CustomDepth=3 (DefaultEngine.ini); the gouache pass B ignores stencil > 0 as backdrop.
B  reload flicker MF_ComicGlitch (in M_Master_ComicGlitch): whole object old look <-> new look.
                 OldLook = Custom Primitive Data 1 (per object, BPC_AssetReload); Reload = min(MI,
                 MPC_Glitch.Reload) for a whole-scene reload without components.
BPC_AssetReload (/Game/Dev/Blueprints) alternates A and B ("tear, switch, tear, switch ...").

MF_ComicGlitch is only called by M_Master_ComicGlitch; hook_master() replaces the call node after a
rebuild (outputs get new ids). If another master starts calling the MF, add it to MASTERS.
"""
import os
import unreal

mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
atools = unreal.AssetToolsHelpers.get_asset_tools()
HERE = os.path.join(unreal.Paths.project_dir(), "Tools", "Glitch")
D = "/Game/Dev/Materials/Glitch"
MPC_PATH = D + "/MPC_Glitch"
MF_PATH = D + "/MF_ComicGlitch"
PP_PATH = D + "/M_PP_ComicGlitch"
PPO_PATH = D + "/M_PP_ComicGlitchObject"
MASTERS = ["/Game/Dev/Materials/Glitch/M_Master_ComicGlitch"]
GROUP = "Comic Glitch"
ST = unreal.SceneTextureId

MPC_SCALARS = [("Amount", 0.0), ("Reload", 1.0)]
INKS = [("InkCyan", (0.025, 0.95, 0.79)), ("InkMagenta", (1.0, 0.015, 0.38)), ("InkYellow", (0.93, 1.0, 0.02))]

OBJ_SCALARS = [  # name, default, custom input (None = goes through the MPC min)
    ("Reload", 1.0, None),
    ("GlitchStepsPerSecond", 7.0, "Rate"),
    ("PreviewLoop", 0.0, "Loop"),
    ("PreviewPeriod", 4.0, "Period"),
]
OBJ_INPUTS = ["Base", "Seed", "T", "OldLook", "Reload", "Rate", "Loop", "Period", "FromColor"]

PP_SCALARS = [("GlitchAmount", 0.0, "Amount"), ("PreviewLoop", 0.0, "Loop"), ("PreviewPeriod", 3.0, "Period"),
              ("TearWidth", 0.065, "Width"), ("ColorSplit", 0.008, "Split"), ("ScreenShift", 0.055, "Shift"),
              ("GlitchStepsPerSecond", 9.0, "Steps")]
PP_INPUTS = ["Scene", "UV", "ViewSize", "T", "Amount", "Loop", "Period", "Width", "Split", "Shift", "Steps",
             "InkCyan", "InkMagenta", "InkYellow"]

PPO_SCALARS = [("GlitchAmount", 1.0, "Amount"), ("TearWidth", 0.03, "Width"), ("ColorSplit", 0.006, "Split"),
               ("ScreenShift", 0.03, "Shift"), ("GlitchStepsPerSecond", 12.0, "Steps")]
PPO_INPUTS = ["Scene", "StencilProbe", "DepthProbe", "CustomDepthProbe", "UV", "ViewSize", "T", "Amount",
              "Width", "Split", "Shift", "Steps", "InkCyan", "InkMagenta", "InkYellow"]


def _read(name):
    with open(os.path.join(HERE, name), encoding="utf-8") as f:
        return f.read()


def _get_or_create(path, cls, factory):
    a = unreal.load_asset(path)
    if a:
        return a
    folder, name = path.rsplit("/", 1)
    return atools.create_asset(name, folder, cls, factory)


def _custom_inputs(names):
    out = []
    for n in names:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        out.append(ci)
    return out


def build_mpc():
    mpc = _get_or_create(MPC_PATH, unreal.MaterialParameterCollection, unreal.MaterialParameterCollectionFactoryNew())
    have = {str(p.get_editor_property("parameter_name")) for p in mpc.get_editor_property("scalar_parameters")}
    sc = list(mpc.get_editor_property("scalar_parameters"))
    for n, d in MPC_SCALARS:
        if n not in have:
            p = unreal.CollectionScalarParameter()
            p.set_editor_property("parameter_name", n)
            p.set_editor_property("default_value", d)
            sc.append(p)
    mpc.set_editor_property("scalar_parameters", sc)
    eal.save_loaded_asset(mpc)
    return mpc


def build_mf(mpc):
    mf = _get_or_create(MF_PATH, unreal.MaterialFunction, unreal.MaterialFunctionFactoryNew())
    mel.delete_all_material_expressions_in_function(mf)
    new = lambda cls, x, y: mel.create_material_expression_in_function(mf, cls, x, y)

    inp = new(unreal.MaterialExpressionFunctionInput, -900, -300)
    inp.set_editor_property("input_name", "BaseColor")
    inp.set_editor_property("input_type", unreal.FunctionInputType.FUNCTION_INPUT_VECTOR3)
    c = new(unreal.MaterialExpressionCustom, -300, 0)
    c.set_editor_property("description", "ComicGlitch reload flicker")
    c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    c.set_editor_property("inputs", _custom_inputs(OBJ_INPUTS))
    c.set_editor_property("code", _read("glitch_object_reload.hlsl"))
    mel.connect_material_expressions(inp, "", c, "Base")
    mel.connect_material_expressions(new(unreal.MaterialExpressionObjectPositionWS, -900, -200), "", c, "Seed")
    mel.connect_material_expressions(new(unreal.MaterialExpressionTime, -900, -140), "", c, "T")

    old = new(unreal.MaterialExpressionScalarParameter, -900, -60)
    old.set_editor_property("parameter_name", "OldLook")
    old.set_editor_property("default_value", 0.0)
    old.set_editor_property("group", GROUP)
    old.set_editor_property("use_custom_primitive_data", True)
    old.set_editor_property("primitive_data_index", 1)
    mel.connect_material_expressions(old, "", c, "OldLook")

    y = 20
    params = {}
    for name, d, pin in OBJ_SCALARS:
        p = new(unreal.MaterialExpressionScalarParameter, -900, y)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", d)
        p.set_editor_property("group", GROUP)
        params[name] = p
        if pin:
            mel.connect_material_expressions(p, "", c, pin)
        y += 70
    fc = new(unreal.MaterialExpressionVectorParameter, -900, y)
    fc.set_editor_property("parameter_name", "ReloadFromColor")
    fc.set_editor_property("default_value", unreal.LinearColor(0.42, 0.42, 0.46, 1.0))
    fc.set_editor_property("group", GROUP)
    mel.connect_material_expressions(fc, "", c, "FromColor")
    y += 140
    cp = new(unreal.MaterialExpressionCollectionParameter, -900, y)
    cp.set_editor_property("collection", mpc)
    cp.set_editor_property("parameter_name", "Reload")
    mn = new(unreal.MaterialExpressionMin, -650, y)
    mel.connect_material_expressions(params["Reload"], "", mn, "A")
    mel.connect_material_expressions(cp, "", mn, "B")
    mel.connect_material_expressions(mn, "", c, "Reload")

    o = new(unreal.MaterialExpressionFunctionOutput, 100, 0)
    o.set_editor_property("output_name", "BaseColor")
    mel.connect_material_expressions(c, "", o, "")
    mel.update_material_function(mf)
    eal.save_loaded_asset(mf)
    return mf


def hook_master(path, mf):
    """Replace the MF call in the master: base colour in from whatever fed the old call, out to
    BaseColor. Undoes the earlier band version's extras (emissive add, WPO)."""
    mat = unreal.load_asset(path)
    MP = unreal.MaterialProperty
    old = None
    for i in range(32):
        n = unreal.find_object(mat, "MaterialExpressionMaterialFunctionCall_%d" % i)
        if n and n.get_editor_property("material_function") == mf:
            old = n
    base_src = unreal.find_object(mat, "MaterialExpressionStaticSwitchParameter_2")
    x, y = 600, 0
    if old is not None:
        ins = mel.get_inputs_for_material_expression(mat, old)
        if ins and ins[0]:
            base_src = ins[0]
        x, y = old.get_editor_property("material_expression_editor_x"), old.get_editor_property("material_expression_editor_y")
        mel.delete_material_expression(mat, old)
    emis = mel.get_material_property_input_node(mat, MP.MP_EMISSIVE_COLOR)
    if emis is not None and emis.get_class().get_name() == "MaterialExpressionAdd" and \
            emis.get_editor_property("desc") == "ComicGlitch emissive":
        ins = mel.get_inputs_for_material_expression(mat, emis)
        mel.delete_material_expression(mat, emis)
        if ins and ins[0]:
            mel.connect_material_property(ins[0], "", MP.MP_EMISSIVE_COLOR)

    fc = mel.create_material_expression(mat, unreal.MaterialExpressionMaterialFunctionCall, x, y)
    fc.set_editor_property("material_function", mf)
    mel.connect_material_expressions(base_src, "", fc, "BaseColor")
    mel.connect_material_property(fc, "BaseColor", MP.MP_BASE_COLOR)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return path + ": hooked"


def _pp_material(path, code, inputs, scalars, mpc_amount, probes):
    mat = _get_or_create(path, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    mat.set_editor_property("blendable_location", unreal.BlendableLocation.BL_SCENE_COLOR_AFTER_TONEMAPPING)
    c = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, 600, 0)
    c.set_editor_property("description", "Comic print tear")
    c.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    c.set_editor_property("inputs", _custom_inputs(inputs))
    c.set_editor_property("code", code)
    y = 0
    for pin, tex in [("Scene", ST.PPI_POST_PROCESS_INPUT0)] + probes:
        st = mel.create_material_expression(mat, unreal.MaterialExpressionSceneTexture, 0, y)
        st.set_editor_property("scene_texture_id", tex)
        mel.connect_material_expressions(st, "Color", c, pin)
        y += 120
    sp = mel.create_material_expression(mat, unreal.MaterialExpressionScreenPosition, 0, y)
    mel.connect_material_expressions(sp, "ViewportUV", c, "UV")
    mel.connect_material_expressions(mel.create_material_expression(mat, unreal.MaterialExpressionViewSize, 0, y + 80), "", c, "ViewSize")
    mel.connect_material_expressions(mel.create_material_expression(mat, unreal.MaterialExpressionTime, 0, y + 140), "", c, "T")
    y += 220
    for name, d, pin in scalars:
        p = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, 0, y)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", d)
        p.set_editor_property("group", GROUP)
        if name == "GlitchAmount" and mpc_amount is not None:
            cp = mel.create_material_expression(mat, unreal.MaterialExpressionCollectionParameter, 0, y + 60)
            cp.set_editor_property("collection", mpc_amount)
            cp.set_editor_property("parameter_name", "Amount")
            m = mel.create_material_expression(mat, unreal.MaterialExpressionMax, 300, y)
            mel.connect_material_expressions(p, "", m, "A")
            mel.connect_material_expressions(cp, "", m, "B")
            mel.connect_material_expressions(m, "", c, pin)
            y += 60
        else:
            mel.connect_material_expressions(p, "", c, pin)
        y += 70
    for name, rgb in INKS:
        p = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, 0, y)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        p.set_editor_property("group", GROUP)
        mel.connect_material_expressions(p, "", c, name)
        y += 140
    mel.connect_material_property(c, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return path + ": rebuilt"


def build():
    mpc = build_mpc()
    mf = build_mf(mpc)
    res = [hook_master(p, mf) for p in MASTERS]
    res.append(_pp_material(PP_PATH, _read("glitch_pp.hlsl"), PP_INPUTS, PP_SCALARS, mpc, []))
    res.append(_pp_material(PPO_PATH, _read("glitch_object_tear.hlsl"), PPO_INPUTS, PPO_SCALARS, None,
                            [("StencilProbe", ST.PPI_CUSTOM_STENCIL), ("DepthProbe", ST.PPI_SCENE_DEPTH),
                             ("CustomDepthProbe", ST.PPI_CUSTOM_DEPTH)]))
    return res


def set_mpc(amount=None, reload=None):
    """Preview: write MPC_Glitch values for the editor world (not saved)."""
    w = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    mpc = unreal.load_asset(MPC_PATH)
    if amount is not None:
        unreal.MaterialLibrary.set_scalar_parameter_value(w, mpc, "Amount", amount)
    if reload is not None:
        unreal.MaterialLibrary.set_scalar_parameter_value(w, mpc, "Reload", reload)
