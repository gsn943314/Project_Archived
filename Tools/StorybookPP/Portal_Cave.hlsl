// =====================================================================
// Magic cave portal surface (Opaque, Unlit, emissive HDR)
//   Mesh: SM_ArchwayMagic (flat arch card in local XZ, Y = 0).
//   UVs of that card are not usable (triangle fan -> zigzags / seam), so
//   everything is computed from local position.
//   - fake depth: 4 parallax layers along the local view vector
//   - painted swirl bands in few flat tones (reads as gouache after PP)
//   - tunnel base: warm light at the far end (CoreColor), cave shadow towards
//     the walls (DeepColor); shifts most with parallax. Drifting motes inside
//   - warm gold brushy rim = the one bright accent of the level
//   Unlit -> DiffuseColor = 0 -> Storybook PP pass A leaves it alone.
//
// Source of truth for the Custom node in /Game/Dev/Materials/M_PortalCave.
// Rebuild with Tools/StorybookPP/build_portal.py (run in editor).
// =====================================================================
struct FPC
{
    float Hash(float2 p) { p = frac(p * float2(0.3183099, 0.3678794) + float2(0.71, 0.113)); p *= 17.0; return frac(p.x * p.y * (p.x + p.y)); }
    float2 Hash2(float2 p) { return float2(Hash(p), Hash(p + 19.19)); }
    float Noise(float2 x)
    {
        float2 i = floor(x); float2 f = frac(x); f = f * f * (3.0 - 2.0 * f);
        return lerp(lerp(Hash(i), Hash(i + float2(1, 0)), f.x), lerp(Hash(i + float2(0, 1)), Hash(i + float2(1, 1)), f.x), f.y);
    }
    float Fbm(float2 x) { return 0.6 * Noise(x) + 0.3 * Noise(x * 2.07 + 5.3) + 0.1 * Noise(x * 4.13 + 1.7); }
    float Band(float x, float lo, float soft) { return smoothstep(lo - soft, lo + soft, x); }
};
FPC G;

float2 p   = Local.xz;
float3 v   = normalize(ViewLocal + 1e-5);
float2 par = -v.xz / max(abs(v.y), 0.3);           // offset per unit of depth behind the card
float  t   = Clock * SwirlSpeed;
float2 c   = float2(EyeCenterX, EyeCenterZ);
float  R   = max(EyeRadius, 1.0);

// ------------------------------------------------ distance to the arch outline (0 at edge, ~1 at centre)
// Fitted to the visible stone opening, not to the card (the card runs behind the frame).
float2 e   = (p - float2(OpenX, OpenSpring)) / float2(OpenHalfW, OpenTop - OpenSpring);
float  dA  = (p.y < OpenSpring) ? (1.0 - abs(e.x)) : (1.0 - length(e));
dA = min(dA, (p.y - 4.0) / 90.0);                 // floor line glows too
if (DebugRim > 0.5 && DebugRim < 1.5) return float3(frac(saturate(dA) * 5.0), step(dA, 0.0), 0.0) * 2.0;

// ------------------------------------------------ interior, back to front
// Tunnel base seen at the far end: warm light in the middle, cave shadow towards the walls.
// Taken deeper than the last swirl layer so it slides most with parallax.
float2 qd = (p + par * DepthStep * 5.0 - c) / (R * 1.8);
float  rD = length(qd);
float3 col = lerp(MidColor.rgb * 0.55, DeepColor.rgb, smoothstep(0.35, 1.0, rD));
col = lerp(CoreColor.rgb * CoreAmount, col, smoothstep(0.04, 0.32, rD));
const int L = 4;
[unroll] for (int i = L - 1; i >= 0; --i)
{
    float  depth = i * DepthStep;
    float2 pl    = p + par * depth;
    float2 q     = (pl - c) / (R * (1.0 + 0.35 * i));
    float  r     = length(q);
    float  a     = atan2(q.y, q.x);
    float  n     = G.Fbm(pl / 55.0 + float2(i * 7.3, t * 0.15));

    // spiral bands, each deeper layer turns faster and is darker
    float  sw    = a * Arms + r * Twist - t * (1.0 + 0.45 * i) + n * 2.2 + i * 1.7;
    float  band  = 0.5 + 0.5 * sin(sw);
    float  fade  = exp(-i * 0.55);
    float  hole  = G.Band(r, HoleSize * (1.0 + 0.25 * i), 0.08);          // dark centre of this layer
    float  m     = G.Band(band, 0.62 - 0.05 * i, 0.06) * hole;             // flat paint patch
    float3 lc    = lerp(MidColor.rgb, SwirlColor.rgb, G.Band(band, 0.82, 0.05));
    lc           = lerp(lc, DeepColor.rgb, (1.0 - fade) * 0.6);
    lc          *= lerp(1.0, 1.0 - EdgeShade, smoothstep(0.55, 1.05, r));     // cave mouth: walls fall into shadow
    col          = lerp(col, lc, m * (i == 0 ? FrontCoverage : 1.0));

    // drifting motes in the two deepest layers
    if (i >= 2)
    {
        float2 g    = pl / 26.0 + float2(0.0, -t * 0.35 * (i - 1));
        float2 cell = floor(g);
        float2 o    = G.Hash2(cell + i * 3.1);
        float  on   = step(1.0 - MoteDensity, G.Hash(cell + 9.7 + i));
        float  tw   = 0.5 + 0.5 * sin(Clock * (1.5 + 2.0 * o.x) + o.y * 6.28);
        float  dot_ = 1.0 - smoothstep(0.08, 0.16, length(frac(g) - (0.25 + 0.5 * o)));
        col         = lerp(col, MoteColor.rgb, dot_ * on * tw * hole);
    }
}

// ------------------------------------------------ warm brushy rim (the accent)
float ang  = atan2(p.y - 150.0, p.x - 12.0);
float rn   = G.Fbm(float2(ang * 9.0 + t * 0.4, dA * 6.0 - t * 0.3));
float rimW = RimWidth * (0.45 + 1.6 * smoothstep(0.45, 0.75, rn));   // steady band + brush licks reaching inward
float rim  = 1.0 - G.Band(dA, rimW, 0.015);
float halo = exp(-max(dA - rimW, 0.0) / max(RimSoft, 1e-3)) * (0.6 + 0.4 * rn);
if (DebugRim > 1.5) return float3(rim, rn, halo) * 2.0;
col = lerp(col, RimColor.rgb * RimBoost, rim);
col += RimColor.rgb * halo * HaloAmount * (1.0 - rim);

return max(col, 0.0) * Glow;
