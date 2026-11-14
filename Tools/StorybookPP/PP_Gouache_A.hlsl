// =====================================================================
// Storybook Gouache PP - Pass A (Scene Color Before DOF, HDR)
//   1. Light ramp: lighting = SceneColor / DiffuseColor -> 3 soft tones
//   2. Grade: soft desaturation, accent colors preserved
//   3. Aerial perspective haze by depth
//   DebugMode 1 = tone bands, 2 = log2(light ratio) bands (for LitLevel)
// Colored outlines + Kuwahara live in Pass B (PP_Gouache_B.hlsl), after
// tonemapping, so the paint is flattened before lines are drawn.
//
// Source of truth for the Custom node in /Game/Dev/Materials/M_PP_Gouache.
// Rebuild with Tools/StorybookPP/build_pp_gouache.py (run in editor).
// =====================================================================
struct FSBG
{
    float Lum(float3 c) { return dot(c, float3(0.2126, 0.7152, 0.0722)); }
    float3 Sat(float3 c, float s) { float l = Lum(c); return max(0.0, lerp(float3(l, l, l), c, s)); }
    float3 Show(float3 tint, float brightness) { return tint / max(Lum(tint), 0.05) * max(brightness, 0.05); }
};
FSBG G;

float3 scene = Scene.rgb;
float  z     = Depth.r;
float3 alb   = Diffuse.rgb;

float sLum  = G.Lum(scene);
float aLum  = G.Lum(alb);
float valid = smoothstep(0.004, 0.02, aLum) * (1.0 - step(200000.0, z));
float ratio = sLum / max(aLum, 0.004);
float light = ratio / max(LitLevel, 1e-4);
float emissive = smoothstep(2.5, 4.0, light);

// ---------------------------------------------------------------- 1. ramp
float soft   = max(RampSoftness, 1e-3);
float tone   = smoothstep(ShadowEdge - soft, ShadowEdge + soft, light);
float hiTone = smoothstep(HighEdge - soft, HighEdge + soft, light);
hiTone *= smoothstep(0.08, 0.16, aLum);   // ratio is unreliable on very dark albedo

if (DebugMode > 0.5 && DebugMode < 1.5)
{
    float3 d = lerp(float3(0.20, 0.30, 1.00), float3(1, 1, 1), tone);
    d = lerp(d, float3(1.00, 0.80, 0.10), hiTone);
    d = lerp(d, float3(0.10, 1.00, 0.25), emissive);
    d = lerp(float3(0.80, 0.10, 0.80), d, valid);
    return G.Show(d, sLum);
}
if (DebugMode > 1.5)
{
    // band k = floor(log2(ratio)); colors cycle red,yellow,green,cyan,blue,magenta for k = 0..5
    float l2 = log2(max(ratio, 1e-4));
    float k  = floor(l2);
    float m  = k - 6.0 * floor(k / 6.0);
    float3 pal = m < 0.5 ? float3(1, 0, 0) : m < 1.5 ? float3(1, 1, 0) : m < 2.5 ? float3(0, 1, 0)
               : m < 3.5 ? float3(0, 1, 1) : m < 4.5 ? float3(0, 0, 1) : float3(1, 0, 1);
    return G.Show(pal * (0.45 + 0.55 * frac(l2)), sLum);
}

float3 rampTint = lerp(ShadowTint.rgb, LitTint.rgb, tone);
rampTint = lerp(rampTint, HighlightTint.rgb, hiTone * HighlightAmount);
float3 painted = alb * rampTint * LitLevel;
float3 col = lerp(scene, painted, saturate(valid * (1.0 - emissive) * RampAmount));

// ---------------------------------------------------------------- 2. grade
float mx = max(alb.r, max(alb.g, alb.b));
float mn = min(alb.r, min(alb.g, alb.b));
float chroma = (mx - mn) / max(mx, 0.05);
float satK = lerp(Saturation, 1.0, smoothstep(0.55, 0.85, chroma) * AccentPreserve);
col = G.Sat(col, satK) * GradeTint.rgb;

// ---------------------------------------------------------------- 3. aerial perspective
float h = smoothstep(HazeStart, max(HazeEnd, HazeStart + 1.0), z) * HazeAmount;
col = lerp(col, HazeColor.rgb * LitLevel, saturate(h));

return col;
