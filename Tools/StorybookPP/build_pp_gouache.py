"""Builds the Storybook Gouache post-process materials from the .hlsl sources.

  Pass A  /Game/Dev/Materials/M_PP_Gouache   (+ MI_PP_Gouache)   PP_Gouache_A.hlsl
          Before DOF (HDR): light ramp, grade, aerial haze
  Pass B  /Game/Dev/Materials/M_PP_GouacheB  (+ MI_PP_GouacheB)  PP_Gouache_B.hlsl
          After DOF, before TSR: solid background, Kuwahara, colored brush outlines

Run inside the Unreal Editor (Python / MCP execute_python). Safe to re-run:
each material graph is rebuilt from scratch; material instances (and their
overrides) are kept. Does not touch M_PP_Storybook or any level.

  build()          -> both passes
  build("A"/"B")   -> one pass
"""
import os
import unreal

MAT_DIR = "/Game/Dev/Materials"
SRC_DIR = os.path.join(unreal.Paths.project_dir(), "Tools", "StorybookPP")
ST = unreal.SceneTextureId

PASSES = {
    "A": {
        "material": "M_PP_Gouache",
        "instance": "MI_PP_Gouache",
        "hlsl": "PP_Gouache_A.hlsl",
        "location": unreal.BlendableLocation.BL_SCENE_COLOR_BEFORE_DOF,
        "description": "Storybook Gouache A (ramp, grade, haze)",
        # (custom input, SceneTextureId, output pin)
        "scene_textures": [
            ("Scene", ST.PPI_POST_PROCESS_INPUT0, "Color"),
            ("Depth", ST.PPI_SCENE_DEPTH, "Color"),
            ("Diffuse", ST.PPI_DIFFUSE_COLOR, "Color"),
        ],
        "world_position": False,
        # (name, default, group)
        "scalars": [
            ("LitLevel", 5.0, "1 Ramp"),          # calibrated with DebugMode 2 in Lvl_StorybookPreview
            ("RampAmount", 1.0, "1 Ramp"),
            ("ShadowEdge", 0.62, "1 Ramp"),
            ("HighEdge", 1.2, "1 Ramp"),
            ("RampSoftness", 0.1, "1 Ramp"),       # wide enough that Lumen noise doesn't flip tones
            ("HighlightAmount", 0.35, "1 Ramp"),
            ("Saturation", 0.78, "3 Grade"),
            ("AccentPreserve", 0.3, "3 Grade"),
            ("HazeStart", 5000.0, "4 Haze"),
            ("HazeEnd", 14000.0, "4 Haze"),
            ("HazeAmount", 0.8, "4 Haze"),
            ("DebugMode", 0.0, "9 Debug"),
        ],
        "vectors": [
            ("ShadowTint", (0.48, 0.45, 0.70), "1 Ramp"),
            ("LitTint", (1.00, 0.98, 0.93), "1 Ramp"),
            ("HighlightTint", (1.10, 1.05, 0.92), "1 Ramp"),
            ("GradeTint", (1.03, 1.00, 0.95), "3 Grade"),
            ("HazeColor", (0.70, 0.68, 0.74), "4 Haze"),
        ],
    },
    "B": {
        "material": "M_PP_GouacheB",
        "instance": "MI_PP_GouacheB",
        "hlsl": "PP_Gouache_B.hlsl",
        # Before TSR on purpose: lines/edges read jittered render-res GBuffers, and only
        # running ahead of temporal upscaling lets TSR resolve that jitter (no shimmer).
        # Same location as pass A, ordered after it by priority. (At After DOF,
        # SceneTextureLookup(PostProcessInput0) returned the pre-A scene color.)
        "location": unreal.BlendableLocation.BL_SCENE_COLOR_BEFORE_DOF,
        "priority": 10,
        "description": "Storybook Gouache B (background, Kuwahara, colored outlines)",
        "scene_textures": [
            ("Scene", ST.PPI_POST_PROCESS_INPUT0, "Color"),
            ("SceneInvSize", ST.PPI_POST_PROCESS_INPUT0, "InvSize"),
            ("Depth", ST.PPI_SCENE_DEPTH, "Color"),
            ("DepthInvSize", ST.PPI_SCENE_DEPTH, "InvSize"),
            ("Diffuse", ST.PPI_DIFFUSE_COLOR, "Color"),
            ("Normal", ST.PPI_WORLD_NORMAL, "Color"),
            ("CustomDepth", ST.PPI_CUSTOM_DEPTH, "Color"),   # backdrop mask (Maze_Backdrop has Render CustomDepth)
        ],
        "world_position": True,
        "scalars": [
            ("BackgroundAmount", 1.0, "0 Background"),
            ("SkyIsBackground", 1.0, "0 Background"),
            ("BackgroundExposure", 3.0, "0 Background"),   # HDR brightness of the fill (goes through tonemapper)
            ("PaintRange", 1.5, "1 Kuwahara"),             # HDR -> paint-space compression knee
            ("KuwaharaAmount", 1.0, "1 Kuwahara"),
            ("SkipDepth", 14000.0, "1 Kuwahara"),  # beyond this (= pass A HazeEnd) no Kuwahara / lines
            ("RadiusNear", 2.5, "1 Kuwahara"),     # render-resolution pixels (pass runs before TSR)
            ("RadiusFar", 4.5, "1 Kuwahara"),
            ("KuwaharaNear", 3000.0, "1 Kuwahara"),
            ("KuwaharaFar", 9000.0, "1 Kuwahara"),
            ("Hardness", 8.0, "1 Kuwahara"),
            ("Sharpness", 8.0, "1 Kuwahara"),
            ("Zeta", 0.4, "1 Kuwahara"),
            ("LineOpacity", 1.0, "2 Line"),
            ("LineWidth", 2.5, "2 Line"),          # render-resolution pixels
            ("LineWidthMin", 0.45, "2 Line"),
            ("LineWidthMax", 1.5, "2 Line"),
            ("LineShadowBoost", 1.35, "2 Line"),
            ("LineLitThin", 0.55, "2 Line"),
            ("LineLitOpacity", 0.8, "2 Line"),
            ("LineToneLo", 0.25, "2 Line"),
            ("LineToneHi", 0.6, "2 Line"),
            ("LineNoiseScale", 120.0, "2 Line"),
            ("LineBreakup", 0.35, "2 Line"),
            ("LineDry", 0.35, "2 Line"),
            ("LineDryScale", 18.0, "2 Line"),
            ("LineGamma", 1.7, "2 Line"),
            ("LineValue", 0.6, "2 Line"),
            ("SilWeight", 1.0, "2 Line"),
            ("CreaseWeight", 0.6, "2 Line"),
            ("MatWeight", 0.35, "2 Line"),
            ("DepthSensitivity", 2.5, "2 Line"),
            ("LineFadeNear", 4000.0, "2 Line"),
            ("LineFadeFar", 15000.0, "2 Line"),
            ("LineFarScale", 0.5, "2 Line"),
            ("LineFarFade", 0.6, "2 Line"),
            ("DebugMode", 0.0, "9 Debug"),
        ],
        "vectors": [
            ("BackgroundColor", (0.33, 0.30, 0.36), "0 Background"),   # linear, as the color picker shows it
            ("LineTint", (0.92, 0.82, 1.00), "2 Line"),
        ],
    },
}

mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def get_or_create(name, cls, factory):
    path = f"{MAT_DIR}/{name}"
    if eal.does_asset_exist(path):
        return eal.load_asset(path), False
    return tools.create_asset(name, MAT_DIR, cls, factory), True


def build_pass(key):
    spec = PASSES[key]
    with open(os.path.join(SRC_DIR, spec["hlsl"]), "r", encoding="utf-8") as f:
        code = f.read()

    mat, _ = get_or_create(spec["material"], unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_POST_PROCESS)
    mat.set_editor_property("blendable_location", spec["location"])
    mat.set_editor_property("blendable_priority", spec.get("priority", 0))

    custom = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, 600, 0)
    custom.set_editor_property("description", spec["description"])
    custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    names = [s[0] for s in spec["scene_textures"]]
    names += ["World"] if spec["world_position"] else []
    names += [s[0] for s in spec["scalars"]] + [v[0] for v in spec["vectors"]]
    inputs = []
    for n in names:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        inputs.append(ci)
    custom.set_editor_property("inputs", inputs)
    custom.set_editor_property("code", code)

    y = 0
    st_nodes = {}
    for inp, tex_id, pin in spec["scene_textures"]:
        node = st_nodes.get(tex_id)
        if node is None:
            node = mel.create_material_expression(mat, unreal.MaterialExpressionSceneTexture, 0, y)
            node.set_editor_property("scene_texture_id", tex_id)
            st_nodes[tex_id] = node
            y += 120
        mel.connect_material_expressions(node, pin, custom, inp)

    if spec["world_position"]:
        wp = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, 0, y)
        mel.connect_material_expressions(wp, "", custom, "World")
        y += 120

    for name, default, group in spec["scalars"]:
        p = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, 0, y)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", default)
        p.set_editor_property("group", group)
        mel.connect_material_expressions(p, "", custom, name)
        y += 80
    for name, rgb, group in spec["vectors"]:
        p = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, 0, y)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
        p.set_editor_property("group", group)
        mel.connect_material_expressions(p, "", custom, name)
        y += 140

    mel.connect_material_property(custom, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.layout_material_expressions(mat)
    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)

    mi, created = get_or_create(spec["instance"], unreal.MaterialInstanceConstant,
                                unreal.MaterialInstanceConstantFactoryNew())
    if created or mi.get_editor_property("parent") != mat:
        mel.set_material_instance_parent(mi, mat)
    eal.save_loaded_asset(mi)
    return f"{key}: {mat.get_path_name()} ({len(names)} inputs), MI {'created' if created else 'kept'}"


def build(which="AB"):
    return "; ".join(build_pass(k) for k in which)


if __name__ == "__main__":
    print(build())
