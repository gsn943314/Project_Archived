// =====================================================================
// Exit portal halo + rays (Masked, Unlit, on /Engine/BasicShapes/Plane)
//   A storybook "look here" mark around the exit arch: a solid glowing band
//   hugging the stone frame, then hand-drawn rays fanning out from it.
//   Flat painted shapes (masked, not translucent) so the Storybook PP keeps
//   them and treats them like the rest of the painting.
//   Coordinates: plane local XY * PlaneScale = cm, origin at the arch's
//   spring line (centre of the top semicircle), +Y up (FlipY fixes it).
// Source of truth for the Custom node in /Game/Dev/Materials/M_PortalHalo.
// =====================================================================
struct FPH
{
    float Hash(float n) { return frac(sin(n * 12.9898) * 43758.5453); }
    float Noise(float x) { float i = floor(x); float f = frac(x); f = f * f * (3.0 - 2.0 * f); return lerp(Hash(i), Hash(i + 1.0), f); }
};
FPH G;

float2 p = Local.xy * PlaneScale;
p.y *= FlipY;
float  t = Clock;
float  W = InnerHalfW;

// distance outside the frame outline (d) and arc-length position along it (s, 0 at the top)
float d, s;
if (p.y >= 0.0) { d = length(p) - W; s = atan2(p.x, p.y) * W; }
else            { d = abs(p.x) - W; s = sign(p.x) * (1.5707963 * W - p.y); }
if (p.y < -GroundDepth || d < 0.0) return float4(0, 0, 0, 0);

// ---- halo band hugging the frame (lumpy, slowly breathing)
float bw   = BandWidth * (0.75 + 0.5 * G.Noise(s / 35.0 + t * 0.6));
float band = 1.0 - step(bw, d);

// ---- rays
float rs   = s / RaySpacing;
float id   = floor(rs);
float f    = frac(rs) - 0.5;
float h    = G.Hash(id + 3.7);
float h2   = G.Hash(id * 1.91 + 11.3);
float on   = step(h2, RayDensity);
float len  = RayLength * (0.4 + 0.6 * h) * (0.8 + 0.2 * sin(t * RaySpeed + h * 6.2832));
float st   = bw + RayGap * (0.6 + 0.8 * h2);
float tr   = (d - st) / max(len, 1.0);
float half_ = (RayWidth / RaySpacing) * 0.5 * (1.0 - 0.8 * saturate(tr));      // tapering stroke
f += (G.Noise(d / 40.0 + id * 5.0) - 0.5) * 0.15 * saturate(tr);               // slight hand wobble
float ray  = on * step(0.0, tr) * step(tr, 1.0) * step(abs(f), half_);

float  m   = max(band, ray);
float3 c   = band > 0.5 ? BandColor.rgb : lerp(RayColor.rgb, RayTipColor.rgb, saturate(tr));
return float4(c * Glow, m);
