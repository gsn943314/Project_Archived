// M_PP_ComicGlitchObject - the full-screen print tear, but only on marked objects.
// A mesh is marked by Render CustomDepth + stencil 128..255: tear amount = (stencil - 128) / 127
// (BPC_AssetReload writes it). Only where the marked mesh is the visible surface (custom depth
// reaches scene depth). Per pixel: if the band is active, the object's slice is shown shifted
// (RGB split + ink edge); where the slice moved away, the hole is filled with dark ink + halftone.
// Inputs: Scene StencilProbe DepthProbe CustomDepthProbe (bind the scene textures) UV ViewSize T
//         Amount Width Split Shift Steps InkCyan InkMagenta InkYellow
float frame = floor(T * max(Steps, 1.0));
float fh = frac(sin(frame * 3.17) * 43758.5453);
float slant = 0.38 + (fh - 0.5) * 0.30;
float aspect = ViewSize.x / max(ViewSize.y, 1.0);
float diagonal = (UV.y + UV.x * slant) / max(0.002, Width);
float coarse = floor(diagonal);
float ch = frac(sin(coarse * 17.31 + frame * 7.13) * 43758.5453);
float thin = step(0.62, frac(ch * 13.7));
float bandId = thin > 0.5 ? floor(diagonal * 4.0) + 1000.0 : coarse;
float hash = frac(sin(bandId * 12.99 + frame * 7.13) * 43758.5453);
float jump = step(0.92, hash);
float sgn = hash > 0.5 ? 1.0 : -0.8;
float2 shiftV = float2(Shift, -Shift * 0.26) * sgn * (0.5 + frac(hash * 3.7) * 0.5) * (1.0 + jump * 2.0);

float2 srcUV = saturate(UV - shiftV);
float2 sUV0 = ClampSceneTextureUV(ViewportUVToSceneTextureUV(UV, 25), 25);
float2 sUV1 = ClampSceneTextureUV(ViewportUVToSceneTextureUV(srcUV, 25), 25);
float st0 = SceneTextureLookup(sUV0, 25, false).r;
float st1 = SceneTextureLookup(sUV1, 25, false).r;
float cd0 = SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(UV, 13), 13), 13, false).r;
float cd1 = SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(srcUV, 13), 13), 13, false).r;
float sd0 = SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(UV, 1), 1), 1, false).r;
float sd1 = SceneTextureLookup(ClampSceneTextureUV(ViewportUVToSceneTextureUV(srcUV, 1), 1), 1, false).r;
float aHere = (st0 > 127.5 ? (st0 - 128.0) / 127.0 : 0.0) * step(cd0, sd0 * 1.003 + 2.0);
float aSrc  = (st1 > 127.5 ? (st1 - 128.0) / 127.0 : 0.0) * step(cd1, sd1 * 1.003 + 2.0);
float g = saturate(Amount);
aHere *= g; aSrc *= g;
if (max(aHere, aSrc) <= 0.001) return Scene.rgb;

float activeSrc  = aSrc  > 0.001 ? step(1.0 - 0.6 * aSrc, hash)  : 0.0;
float activeHere = aHere > 0.001 ? step(1.0 - 0.6 * aHere, hash) : 0.0;
float phase = thin > 0.5 ? frac(diagonal * 4.0) : frac(diagonal);
float edge = 1.0 - smoothstep(0.06, 0.18, phase);
float3 ink = hash > 0.88 ? InkMagenta : (hash > 0.77 ? InkCyan : InkYellow);
if (activeSrc > 0.5)
{
    float2 split = float2(Split, Split * -0.25) * aSrc;
    float2 rUV = ClampSceneTextureUV(ViewportUVToSceneTextureUV(saturate(srcUV + split), 14), 14);
    float2 gUV = ClampSceneTextureUV(ViewportUVToSceneTextureUV(srcUV, 14), 14);
    float2 bUV = ClampSceneTextureUV(ViewportUVToSceneTextureUV(saturate(srcUV - split), 14), 14);
    float3 c = float3(SceneTextureLookup(rUV, 14, false).r, SceneTextureLookup(gUV, 14, false).g, SceneTextureLookup(bUV, 14, false).b);
    return lerp(c, ink, edge * aSrc * 0.9);
}
if (activeHere > 0.5)
{
    float2 grid = UV * float2(140.0 * aspect, 140.0);
    float dots = 1.0 - smoothstep(0.18, 0.30, length(frac(grid) - 0.5));
    float3 hole = lerp(float3(0.014, 0.01, 0.035), ink, dots * 0.8);
    return lerp(Scene.rgb, hole, aHere);
}
return Scene.rgb;
