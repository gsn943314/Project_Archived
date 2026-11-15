// M_PP_ComicGlitch - full-screen print tear (after tonemapping, so it sits on top of the gouache passes).
// Meant as short pulses: Amount = max(MI GlitchAmount, MPC_Glitch.Amount); PreviewLoop fires a
// spike-and-decay every PreviewPeriod seconds. Bands: random slant per step, some bands split into
// thin slivers, rare "jump" bands, halftone only on a few bands, aspect-correct dots.
// Inputs: Scene UV ViewSize T Amount Loop Period Width Split Shift Steps InkCyan InkMagenta InkYellow
float A = saturate(Amount);
if (Loop > 0.5)
{
    float c = frac(T / max(Period, 0.5));
    A = max(A, saturate(1.0 - c * 2.4));
}
if (A <= 0.0001) return Scene.rgb;
float frame = floor(T * max(Steps, 1.0));
float fh = frac(sin(frame * 3.17) * 43758.5453);
float slant = 0.38 + (fh - 0.5) * 0.30;
float aspect = ViewSize.x / max(ViewSize.y, 1.0);
float diagonal = (UV.y + UV.x * slant) / max(0.005, Width);
float coarse = floor(diagonal);
float ch = frac(sin(coarse * 17.31 + frame * 7.13) * 43758.5453);
float thin = step(0.62, frac(ch * 13.7));
float bandId = thin > 0.5 ? floor(diagonal * 4.0) + 1000.0 : coarse;
float hash = frac(sin(bandId * 12.99 + frame * 7.13) * 43758.5453);
float active = step(1.0 - 0.32 * A, hash);
float jump = step(0.94, hash);
float shift = (hash > 0.80 ? 1.0 : -0.75) * Shift * A * (1.0 + jump * 2.5);
float2 moved = saturate(UV + float2(shift, -shift * 0.26) * active);
float2 split = float2(Split, Split * -0.25) * A * active;
float2 redUV = ClampSceneTextureUV(ViewportUVToSceneTextureUV(saturate(moved + split), 14), 14);
float2 greenUV = ClampSceneTextureUV(ViewportUVToSceneTextureUV(moved, 14), 14);
float2 blueUV = ClampSceneTextureUV(ViewportUVToSceneTextureUV(saturate(moved - split), 14), 14);
float3 color = float3(SceneTextureLookup(redUV, 14, false).r, SceneTextureLookup(greenUV, 14, false).g, SceneTextureLookup(blueUV, 14, false).b);
float phase = thin > 0.5 ? frac(diagonal * 4.0) : frac(diagonal);
float edge = 1.0 - smoothstep(0.05, 0.15, phase);
float deep = 1.0 - smoothstep(0.015, 0.048, phase);
float3 ink = hash > 0.88 ? InkMagenta : (hash > 0.77 ? InkCyan : InkYellow);
float2 grid = (UV - moved * 0.12) * float2(112.5 * aspect, 112.5);
float dots = (1.0 - smoothstep(0.18, 0.30, length(frac(grid) - 0.5))) * step(0.85, frac(hash * 7.31));
color = lerp(color, ink, A * saturate(edge + 0.55 * dots) * 0.9);
color = lerp(color, float3(0.014, 0.01, 0.035), deep * A * 0.94 * (1.0 - thin * 0.6));
return lerp(Scene.rgb, color, active);
