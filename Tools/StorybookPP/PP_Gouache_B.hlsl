// =====================================================================
// Storybook Gouache PP - Pass B (Scene Color After DOF, HDR, render res,
// BEFORE TSR - so temporal upscaling resolves line / edge jitter)
//   0. Solid background: sky + any actor with Render CustomDepth on
//      (Maze_Backdrop) filled with BackgroundColor * BackgroundExposure
//   1. Generalized Kuwahara (8 sectors, polynomial weights): flattens
//      texture detail into paint patches, radius grows with depth
//   2. Colored brush outlines drawn on the flattened paint
//      (silhouette / crease / material boundary, world-anchored noise)
//   Kuwahara and lines work in a compressed "paint" space
//   p = sqrt(x / (x + PaintRange)) so thresholds behave like display values.
//   DebugMode 1 = line mask only, 2 = Kuwahara off (lines only on source),
//             3 = raw PPI0 lookup (pre-exposure corrected), 4 = Scene pin (3 and 4 must match)
//
// Source of truth for the Custom node in /Game/Dev/Materials/M_PP_GouacheB.
// Rebuild with Tools/StorybookPP/build_pp_gouache.py (run in editor).
// =====================================================================
struct FSBK
{
    float Hash(float3 p)
    {
        p = frac(p * 0.3183099 + float3(0.71, 0.113, 0.419));
        p *= 17.0;
        return frac(p.x * p.y * p.z * (p.x + p.y + p.z));
    }
    float Noise(float3 x)
    {
        float3 i = floor(x);
        float3 f = frac(x);
        f = f * f * (3.0 - 2.0 * f);
        float a = lerp(Hash(i + float3(0, 0, 0)), Hash(i + float3(1, 0, 0)), f.x);
        float b = lerp(Hash(i + float3(0, 1, 0)), Hash(i + float3(1, 1, 0)), f.x);
        float c = lerp(Hash(i + float3(0, 0, 1)), Hash(i + float3(1, 0, 1)), f.x);
        float d = lerp(Hash(i + float3(0, 1, 1)), Hash(i + float3(1, 1, 1)), f.x);
        return lerp(lerp(a, b, f.y), lerp(c, d, f.y), f.z);
    }
    float Lum(float3 c) { return dot(c, float3(0.2126, 0.7152, 0.0722)); }
    float3 ToPaint(float3 x, float k)   { x = max(x, 0.0); return sqrt(x / (x + k)); }
    float3 FromPaint(float3 p, float k) { float3 q = min(p * p, 0.995); return k * q / (1.0 - q); }
};
FSBK G;

float  K   = max(PaintRange, 0.01);
float2 uvC = GetDefaultSceneTextureUV(Parameters, 14);
float2 uvD = GetDefaultSceneTextureUV(Parameters, 1);
float2 pxC = SceneInvSize.xy;
float2 pxD = DepthInvSize.xy;
float  z   = Depth.r;
float3 src = Scene.rgb;
float  sky = step(200000.0, z);

// Before tonemapping, raw SceneTextureLookup(PostProcessInput0) is pre-exposed while the
// Scene pin is not; scale lookups by OneOverPreExposure so neighbours match the pin.
float preExp = View.OneOverPreExposure;
if (DebugMode > 3.5) return src;                                                 // 4: Scene pin
if (DebugMode > 2.5) return SceneTextureLookup(uvC, 14, false).rgb * preExp;     // 3: PPI0 lookup (should match 4)

// ---------------------------------------------------------------- 0. background mask
// Custom depth holds the backdrop even where it is covered, so a pixel is backdrop
// when its scene depth reaches the custom depth. Runs before TSR, so the edge is
// anti-aliased and stable.
float cd = CustomDepth.r;
float backdrop = (1.0 - smoothstep(0.003, 0.02, (cd - z) / max(z, 1.0))) * step(cd, 1000000.0);
float bgMask = saturate(max(backdrop, sky * SkyIsBackground) * BackgroundAmount);
float3 bgHDR = max(BackgroundColor.rgb, 0.0) * BackgroundExposure;
if (bgMask > 0.999 && DebugMode < 0.5)
{
    return bgHDR;                           // pure background: skip Kuwahara and lines
}

// Far pixels (fully hazed by pass A, flat already): fade Kuwahara + lines out
// before SkipDepth and skip both loops beyond it.
float farKeep = 1.0 - smoothstep(SkipDepth * 0.85, max(SkipDepth, 1.0), z);
if (farKeep < 0.001 && DebugMode < 0.5)
{
    return lerp(src, bgHDR, bgMask);
}

// ---------------------------------------------------------------- 1. Kuwahara (paint space)
float kFar = smoothstep(KuwaharaNear, max(KuwaharaFar, KuwaharaNear + 1.0), z);
float rad  = lerp(RadiusNear, RadiusFar, kFar);
float3 col = G.ToPaint(src, K);
if (rad > 0.5 && KuwaharaAmount > 0.001 && DebugMode < 1.5)
{
    float4 m[8];
    float3 s[8];
    [unroll] for (int i = 0; i < 8; ++i) { m[i] = 0; s[i] = 0; }

    const int N = 3;                         // 7x7 grid (37 taps inside the disk), spaced rad/N pixels
    float zeta = Zeta;
    float zc   = 0.58;
    float sz   = sin(zc);
    float eta  = (zeta + cos(zc)) / (sz * sz);

    [loop] for (int y = -N; y <= N; ++y)
    {
        [loop] for (int x = -N; x <= N; ++x)
        {
            float2 v  = float2(x, y) / N;
            float  r2 = dot(v, v);
            if (r2 > 1.0) continue;
            float2 suv = ClampSceneTextureUV(uvC + float2(x, y) * (rad / N) * pxC, 14);
            float3 c   = G.ToPaint(SceneTextureLookup(suv, 14, true).rgb * preExp, K);

            float w[8];
            float vxx = zeta - eta * v.x * v.x;
            float vyy = zeta - eta * v.y * v.y;
            float t;
            t = max(0.0,  v.y + vxx); w[0] = t * t;
            t = max(0.0, -v.x + vyy); w[2] = t * t;
            t = max(0.0, -v.y + vxx); w[4] = t * t;
            t = max(0.0,  v.x + vyy); w[6] = t * t;
            float2 vr = 0.70710678 * float2(v.x - v.y, v.x + v.y);
            vxx = zeta - eta * vr.x * vr.x;
            vyy = zeta - eta * vr.y * vr.y;
            t = max(0.0,  vr.y + vxx); w[1] = t * t;
            t = max(0.0, -vr.x + vyy); w[3] = t * t;
            t = max(0.0, -vr.y + vxx); w[5] = t * t;
            t = max(0.0,  vr.x + vyy); w[7] = t * t;

            float sum = w[0] + w[1] + w[2] + w[3] + w[4] + w[5] + w[6] + w[7];
            float g   = exp(-3.125 * r2) / max(sum, 1e-5);
            [unroll] for (int k = 0; k < 8; ++k)
            {
                float wk = w[k] * g;
                m[k] += float4(c * wk, wk);
                s[k] += c * c * wk;
            }
        }
    }

    float3 mean[8];
    float  sig[8];
    float  minSig = 1e9;
    [unroll] for (int k1 = 0; k1 < 8; ++k1)
    {
        float  wsum = max(m[k1].w, 1e-6);
        mean[k1]    = m[k1].rgb / wsum;
        float3 sk   = abs(s[k1] / wsum - mean[k1] * mean[k1]);
        sig[k1]     = sk.r + sk.g + sk.b;
        minSig      = min(minSig, sig[k1]);
    }
    // Variance relative to the calmest sector: flat areas behave like the classic
    // 1/(1+(h*s)^q) weighting, high-contrast edges no longer underflow to black.
    float floorSig = minSig + 1.0 / max(Hardness * 1000.0, 1.0);
    float4 o = 0;
    [unroll] for (int k2 = 0; k2 < 8; ++k2)
    {
        float wk = 1.0 / (1.0 + pow(sig[k2] / floorSig, 0.5 * Sharpness));
        o += float4(mean[k2] * wk, wk);
    }
    col = lerp(col, o.rgb / max(o.w, 1e-5), saturate(KuwaharaAmount) * farKeep);
}

// ---------------------------------------------------------------- 2. colored brush outlines (paint space)
float3 nrm  = normalize(Normal.rgb + 1e-5);
float3 alb  = Diffuse.rgb;
float  aLum = G.Lum(alb);
float  lumC = G.Lum(col);
float  tone = smoothstep(LineToneLo, LineToneHi, lumC);           // 0 = shadow paint, 1 = lit paint

float3 wp   = World;
float nW    = G.Noise(wp / max(LineNoiseScale, 1.0));
float nB    = G.Noise(wp / max(LineNoiseScale * 0.5, 1.0) + 17.31);
float nD    = G.Noise(wp / max(LineDryScale, 1.0) + 41.7);
float farT  = smoothstep(LineFadeNear, max(LineFadeFar, LineFadeNear + 1.0), z);

float w = LineWidth * lerp(LineWidthMin, LineWidthMax, nW);      // pressure variation
w *= lerp(LineShadowBoost, LineLitThin, tone);                    // lost & found edges
w *= lerp(1.0, LineFarScale, farT);
w = max(w, 0.75);

float sil = 0.0, crease = 0.0, matb = 0.0;
[unroll] for (int t2 = 0; t2 < 8; ++t2)
{
    float ang  = t2 * 0.78539816 + nB * 0.8;
    float2 suv = ClampSceneTextureUV(uvD + float2(cos(ang), sin(ang)) * pxD * w, 1);
    float  zn  = SceneTextureLookup(suv, 1, false).r;
    float3 nn  = SceneTextureLookup(suv, 8, false).rgb;
    float3 an  = SceneTextureLookup(suv, 2, false).rgb;
    float  dz  = (zn - z) / max(z, 50.0);
    float same = 1.0 - smoothstep(0.01, 0.03, abs(dz));
    sil    = max(sil, smoothstep(0.015, 0.05, dz * DepthSensitivity));     // drawn on the near object
    crease = max(crease, smoothstep(0.20, 0.55, 1.0 - dot(nrm, nn)) * same);
    matb   = max(matb, smoothstep(0.10, 0.28, length(an - alb)) * same * step(aLum, G.Lum(an))); // darker side
}
float edge  = max(sil * SilWeight, max(crease * CreaseWeight, matb * MatWeight));
float cover = lerp(1.0, smoothstep(0.30, 0.60, nB), saturate(LineBreakup));  // stroke gaps
cover      *= lerp(1.0, smoothstep(0.25, 0.65, nD), saturate(LineDry));      // dry-brush skips
float lineA = saturate(edge * cover * LineOpacity * lerp(1.0, LineLitOpacity, tone)
                       * (1.0 - farT * LineFarFade) * (1.0 - sky) * farKeep);

if (DebugMode > 0.5 && DebugMode < 1.5)
{
    return (1.0 - lineA.xxx) * K;
}

float3 lc = pow(max(col, 1e-4), LineGamma) * LineTint.rgb;                    // darker mix of the local paint
lc = lc / max(G.Lum(lc), 1e-4) * (lumC * LineValue);
col = lerp(col, saturate(lc), lineA);

// ---------------------------------------------------------------- 3. back to HDR, blend background edge
float3 outHDR = G.FromPaint(col, K);
return lerp(outHDR, bgHDR, bgMask);
