"""Edit-mode highlight materials (replace the controller's DrawDebug boxes, which Shipping strips).

Run inside the editor. Rebuilds M_EditHighlight and (re)creates its four instances.
M_EditHighlight: translucent, unlit, rendered after motion blur (so the gouache passes do not repaint it).
Used two ways by BP_GizmoDirector:
  - on a shell (copy of the block's mesh, 4 % larger) around the hovered / selected / dragged block
  - on a cube at the drop spot while dragging (green = can drop, red = cannot)
"""
import unreal

mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
atools = unreal.AssetToolsHelpers.get_asset_tools()
D = "/Game/Dev/Materials/Highlight"
MAT = D + "/M_EditHighlight"
MIS = {
    "MI_Highlight_Hover": (0.75, 0.95, 1.0),
    "MI_Highlight_Selected": (1.0, 0.78, 0.12),
    "MI_Highlight_Valid": (0.15, 1.0, 0.3),
    "MI_Highlight_Invalid": (1.0, 0.12, 0.08),
}


def _get_or_create(path, cls, factory):
    a = unreal.load_asset(path)
    if a:
        return a
    folder, name = path.rsplit("/", 1)
    return atools.create_asset(name, folder, cls, factory)


def build():
    m = _get_or_create(MAT, unreal.Material, unreal.MaterialFactoryNew())
    mel.delete_all_material_expressions(m)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property("translucency_pass", unreal.MaterialTranslucencyPass.MTP_AFTER_MOTION_BLUR)
    m.set_editor_property("two_sided", False)
    # drawn on a shell 4 % larger than the block (Overlay Material did not show on these blocks), so the normal
    # depth test works: the shell is in front of the block's surface and still hidden behind walls
    m.set_editor_property("disable_depth_test", False)

    def p(cls, x, y):
        return mel.create_material_expression(m, cls, x, y)

    col = p(unreal.MaterialExpressionVectorParameter, -800, -200)
    col.set_editor_property("parameter_name", "Color")
    col.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
    fill = p(unreal.MaterialExpressionScalarParameter, -800, 0)
    fill.set_editor_property("parameter_name", "Fill")
    fill.set_editor_property("default_value", 0.18)
    edge = p(unreal.MaterialExpressionScalarParameter, -800, 80)
    edge.set_editor_property("parameter_name", "Edge")
    edge.set_editor_property("default_value", 0.9)
    glow = p(unreal.MaterialExpressionScalarParameter, -800, 160)
    glow.set_editor_property("parameter_name", "Glow")
    glow.set_editor_property("default_value", 1.6)
    fres = p(unreal.MaterialExpressionFresnel, -800, 260)
    fres.set_editor_property("exponent", 2.5)

    # opacity = saturate(Fill + Fresnel * Edge)
    fe = p(unreal.MaterialExpressionMultiply, -500, 200)
    mel.connect_material_expressions(fres, "", fe, "A")
    mel.connect_material_expressions(edge, "", fe, "B")
    op = p(unreal.MaterialExpressionAdd, -300, 120)
    mel.connect_material_expressions(fill, "", op, "A")
    mel.connect_material_expressions(fe, "", op, "B")
    sat = p(unreal.MaterialExpressionSaturate, -150, 120)
    mel.connect_material_expressions(op, "", sat, "")
    mel.connect_material_property(sat, "", unreal.MaterialProperty.MP_OPACITY)

    # emissive = Color * Glow * (0.6 + Fresnel)
    base = p(unreal.MaterialExpressionConstant, -500, 340)
    base.set_editor_property("r", 0.6)
    fa = p(unreal.MaterialExpressionAdd, -300, 300)
    mel.connect_material_expressions(base, "", fa, "A")
    mel.connect_material_expressions(fres, "", fa, "B")
    cg = p(unreal.MaterialExpressionMultiply, -500, -150)
    mel.connect_material_expressions(col, "", cg, "A")
    mel.connect_material_expressions(glow, "", cg, "B")
    em = p(unreal.MaterialExpressionMultiply, -150, -100)
    mel.connect_material_expressions(cg, "", em, "A")
    mel.connect_material_expressions(fa, "", em, "B")
    mel.connect_material_property(em, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    out = [MAT + ": rebuilt"]
    for name, rgb in MIS.items():
        mi = _get_or_create(D + "/" + name, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, m)
        mel.set_material_instance_vector_parameter_value(mi, "Color", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1))
        mel.update_material_instance(mi)
        eal.save_loaded_asset(mi)
        out.append(name)
    return out
