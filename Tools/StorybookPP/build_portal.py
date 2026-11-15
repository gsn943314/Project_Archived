"""Builds the magic cave portal (exit / goal) materials from .hlsl sources.

  M_PortalCave  (+ MI_PortalCave)  Portal_Cave.hlsl  Opaque Unlit surface for SM_ArchwayMagic
  M_PortalMote  (+ MI_PortalMote)  Portal_Mote.hlsl  Masked Unlit sprite for the Niagara motes

Both are opaque/masked on purpose: they write depth + GBuffer, so the Storybook
PP (pass A ramp, pass B background fill / Kuwahara / lines) treats them like
painted objects instead of recolouring or erasing them (translucency would be).

Run inside the Unreal Editor. Safe to re-run: graphs rebuilt, instances kept.
  build()  /  build("cave")  /  build("mote")
"""
import os
import unreal

MAT_DIR = "/Game/Dev/Materials"
SRC_DIR = os.path.join(unreal.Paths.project_dir(), "Tools", "StorybookPP")

SPECS = {
    "cave": {
        "material": "M_PortalCave", "instance": "MI_PortalCave", "hlsl": "Portal_Cave.hlsl",
        "blend": unreal.BlendMode.BLEND_OPAQUE, "two_sided": True, "output": "emissive",
        "description": "Magic cave portal",
        "inputs": ["Local", "ViewLocal", "Clock"],
        "scalars": [
            ("Glow", 1.0, "0 Main"),
            ("SwirlSpeed", 0.35, "1 Swirl"),
            ("Arms", 3.0, "1 Swirl"),
            ("Twist", 5.0, "1 Swirl"),
            ("FrontCoverage", 0.55, "1 Swirl"),
            ("DepthStep", 70.0, "2 Depth"),          # cm between parallax layers
            ("EyeCenterX", 12.0, "2 Depth"),
            ("EyeCenterZ", 150.0, "2 Depth"),
            ("EyeRadius", 150.0, "2 Depth"),
            ("HoleSize", 0.3, "2 Depth"),
            ("CoreAmount", 1.0, "2 Depth"),
            ("EdgeShade", 0.6, "2 Depth"),          # darkening of swirl towards the opening edge
            ("MoteDensity", 0.3, "2 Depth"),
            ("OpenX", 12.0, "3 Rim"),               # visible stone opening (card local cm)
            ("OpenSpring", 183.0, "3 Rim"),
            ("OpenHalfW", 160.0, "3 Rim"),
            ("OpenTop", 355.0, "3 Rim"),
            ("DebugRim", 0.0, "9 Debug"),
            ("RimWidth", 0.07, "3 Rim"),
            ("RimSoft", 0.12, "3 Rim"),
            ("RimBoost", 1.0, "3 Rim"),
            ("HaloAmount", 0.6, "3 Rim"),
        ],
        "vectors": [
            ("DeepColor", (0.10, 0.10, 0.45), "0 Main"),
            ("MidColor", (0.25, 1.10, 1.30), "0 Main"),
            ("SwirlColor", (1.10, 2.60, 2.50), "0 Main"),
            ("MoteColor", (3.00, 2.60, 1.60), "0 Main"),
            ("CoreColor", (2.40, 2.10, 1.40), "0 Main"),
            ("RimColor", (6.00, 3.80, 1.60), "3 Rim"),
        ],
    },
    "halo": {
        "material": "M_PortalHalo", "instance": "MI_PortalHalo", "hlsl": "Portal_Halo.hlsl",
        "blend": unreal.BlendMode.BLEND_MASKED, "two_sided": True, "output": "emissive+mask",
        "description": "Exit portal halo + rays",
        "inputs": ["Local", "Clock"],
        "scalars": [
            ("Glow", 1.0, "0 Main"),
            ("PlaneScale", 6.0, "0 Main"),         # = actor scale of the 100x100 engine plane
            ("FlipY", 1.0, "0 Main"),
            ("InnerHalfW", 200.0, "1 Shape"),      # cm, outer edge of the stone frame
            ("GroundDepth", 120.0, "1 Shape"),     # cm below the spring line where the floor is
            ("BandWidth", 14.0, "1 Shape"),
            ("RayGap", 14.0, "2 Rays"),
            ("RaySpacing", 34.0, "2 Rays"),
            ("RayWidth", 9.0, "2 Rays"),
            ("RayLength", 90.0, "2 Rays"),
            ("RayDensity", 0.8, "2 Rays"),
            ("RaySpeed", 1.6, "2 Rays"),
        ],
        "vectors": [
            ("BandColor", (2.6, 1.6, 0.45), "0 Main"),
            ("RayColor", (2.4, 1.3, 0.3), "2 Rays"),
            ("RayTipColor", (1.6, 0.55, 0.12), "2 Rays"),
        ],
    },
    # Teleport pad: additive glow composited AFTER the Storybook PP (After-DOF
    # translucency) so it stays soft and is not repainted or erased by the background fill.
    "ring": {
        "material": "M_PortalRing", "instance": "MI_PortalRing", "hlsl": "Portal_Ring.hlsl",
        "blend": unreal.BlendMode.BLEND_ADDITIVE, "two_sided": True, "output": "emissive", "after_dof": True,
        "description": "Exit pad floor ring",
        "inputs": ["Local", "Clock"],
        "scalars": [
            ("Intensity", 3.0, "0 Main"), ("PlaneScale", 3.4, "0 Main"), ("Radius", 130.0, "0 Main"),
            ("RingWidth", 0.03, "0 Main"), ("InnerFill", 0.25, "0 Main"),
            ("DashCount", 24.0, "1 Anim"), ("DashSpeed", 0.05, "1 Anim"), ("PulseSpeed", 2.0, "1 Anim"),
        ],
        "vectors": [("Color", (0.25, 0.85, 1.0), "0 Main")],
    },
    "spill": {
        "material": "M_PortalSpill", "instance": "MI_PortalSpill", "hlsl": "Portal_Spill.hlsl",
        "blend": unreal.BlendMode.BLEND_TRANSLUCENT, "two_sided": True, "output": "emissive+opacity", "after_dof": True,
        "description": "Exit portal light spill",
        "inputs": ["Local", "Clock"],
        "scalars": [
            ("Intensity", 3.0, "0 Main"), ("PlaneScale", 6.0, "0 Main"), ("FlipY", -1.0, "0 Main"),
            ("OpenHalfW", 135.0, "1 Shape"), ("GroundDepth", 125.0, "1 Shape"),
            ("LineWidth", 6.0, "2 Light"), ("LineAmount", 1.0, "2 Light"),
            ("SpillFalloff", 45.0, "2 Light"), ("SpillAmount", 0.5, "2 Light"),
            ("InnerFalloff", 25.0, "2 Light"), ("InnerAmount", 0.4, "2 Light"),
            ("Opacity", 1.0, "0 Main"), ("ColorFromPattern", 1.0, "0 Main"),   # 1 = brightness follows pattern (glow), 0 = flat colour (dark smoke)
            ("Streaks", 0.7, "2 Light"), ("StreakSpacing", 22.0, "2 Light"), ("MaxReach", 70.0, "2 Light"),
        ],
        "vectors": [("Color", (1.0, 0.55, 0.15), "0 Main")],
    },
    "beams": {
        "material": "M_PortalBeams", "instance": "MI_PortalBeams", "hlsl": "Portal_Beams.hlsl",
        "blend": unreal.BlendMode.BLEND_TRANSLUCENT, "two_sided": True, "output": "emissive+opacity", "after_dof": True,
        "description": "Exit pad light shafts",
        "inputs": ["Local", "Clock"],
        "scalars": [
            ("Intensity", 2.0, "0 Main"), ("StreakCount", 22.0, "0 Main"), ("StreakWidth", 0.12, "0 Main"),
            ("BaseGlow", 0.6, "0 Main"), ("RiseSpeed", 3.0, "1 Anim"), ("FlipZ", 1.0, "0 Main"),
            ("StartZ", 0.0, "0 Main"), ("ConeMode", 0.0, "0 Main"), ("FadeIn", 0.15, "0 Main"),
            ("Opacity", 1.0, "0 Main"), ("ColorFromPattern", 1.0, "0 Main"),    # cone mesh: light from the tip, starting at StartZ
        ],
        "vectors": [("Color", (0.25, 0.85, 1.0), "0 Main")],
    },
    "mote": {
        "material": "M_PortalMote", "instance": "MI_PortalMote", "hlsl": "Portal_Mote.hlsl",
        "blend": unreal.BlendMode.BLEND_MASKED, "two_sided": True, "output": "emissive+mask",
        "usage": [unreal.MaterialUsage.MATUSAGE_NIAGARA_SPRITES],
        "description": "Portal paint mote",
        "inputs": ["UV", "Particle", "ParticleA"],
        "scalars": [("Glow", 1.0, "0 Main")],
        "vectors": [],
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


def make_input_node(mat, name, y):
    """Engine-provided inputs of the Custom node."""
    if name == "Local":
        n = mel.create_material_expression(mat, unreal.MaterialExpressionLocalPosition, 0, y)
        return n, ""
    if name == "ViewLocal":
        cv = mel.create_material_expression(mat, unreal.MaterialExpressionCameraVectorWS, -300, y)
        tr = mel.create_material_expression(mat, unreal.MaterialExpressionTransform, 0, y)
        tr.set_editor_property("transform_source_type", unreal.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD)
        tr.set_editor_property("transform_type", unreal.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
        mel.connect_material_expressions(cv, "", tr, "")
        return tr, ""
    if name == "Clock":
        return mel.create_material_expression(mat, unreal.MaterialExpressionTime, 0, y), ""
    if name == "Particle":        # default pin is RGB only
        return mel.create_material_expression(mat, unreal.MaterialExpressionParticleColor, 0, y), ""
    if name == "ParticleA":
        return mel.create_material_expression(mat, unreal.MaterialExpressionParticleColor, 0, y), "A"
    if name == "UV":
        return mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, 0, y), ""
    raise ValueError(name)


def build_one(key):
    spec = SPECS[key]
    with open(os.path.join(SRC_DIR, spec["hlsl"]), "r", encoding="utf-8") as f:
        code = f.read()
    mat, _ = get_or_create(spec["material"], unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(mat)
    mat.set_editor_property("material_domain", unreal.MaterialDomain.MD_SURFACE)
    mat.set_editor_property("blend_mode", spec["blend"])
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", spec["two_sided"])
    if spec.get("after_dof"):
        mat.set_editor_property("translucency_pass", unreal.MaterialTranslucencyPass.MTP_AFTER_DOF)
    for flag in spec.get("usage", []):
        mel.set_material_usage(mat, flag)

    custom = mel.create_material_expression(mat, unreal.MaterialExpressionCustom, 600, 0)
    custom.set_editor_property("description", spec["description"])
    out4 = spec["output"] in ("emissive+mask", "emissive+opacity")
    custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT4 if out4
                               else unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    names = spec["inputs"] + [s[0] for s in spec["scalars"]] + [v[0] for v in spec["vectors"]]
    ins = []
    for n in names:
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", n)
        ins.append(ci)
    custom.set_editor_property("inputs", ins)
    custom.set_editor_property("code", code)

    y = 0
    for n in spec["inputs"]:
        node, pin = make_input_node(mat, n, y)
        mel.connect_material_expressions(node, pin, custom, n)
        y += 140
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

    if out4:
        rgb = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, 900, 0)
        rgb.set_editor_property("r", True); rgb.set_editor_property("g", True); rgb.set_editor_property("b", True)
        rgb.set_editor_property("a", False)
        al = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, 900, 200)
        for ch, on in (("r", False), ("g", False), ("b", False), ("a", True)):
            al.set_editor_property(ch, on)
        mel.connect_material_expressions(custom, "", rgb, "")
        mel.connect_material_expressions(custom, "", al, "")
        mel.connect_material_property(rgb, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
        mel.connect_material_property(al, "", unreal.MaterialProperty.MP_OPACITY_MASK if spec["output"] == "emissive+mask"
                                      else unreal.MaterialProperty.MP_OPACITY)
    else:
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


def build(which=None):
    return "; ".join(build_one(k) for k in (which.split(",") if which else SPECS))


if __name__ == "__main__":
    print(build())

