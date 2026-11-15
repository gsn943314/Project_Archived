// =====================================================================
// Exit teleport pad - rising light shafts (Additive, Unlit, After-DOF)
//   On /Engine/BasicShapes/Cylinder (r 50, h 100, pivot at centre), two
//   sided so front and back walls both add up like a light column.
//   Vertical streaks of random height + a soft base glow, shimmering up.
// Source of truth for the Custom node in /Game/Dev/Materials/M_PortalBeams.
// =====================================================================
struct FPB { float Hash(float n) { return frac(sin(n * 12.9898 + 4.1) * 43758.5453); } };
FPB G;

float  z  = saturate(Local.z / 100.0 + 0.5);                 // 0 at -Z end .. 1 at +Z end
if (FlipZ < 0.0) z = 1.0 - z;                                // z = 0 where the light comes from
z = saturate((z - StartZ) / max(1.0 - StartZ, 1e-3));       // light starts at StartZ (e.g. the door plane)
float  rr = length(Local.xy);
float  rs = ConeMode > 0.5 ? 50.0 * (0.5 - Local.z / 100.0) : 50.0;   // side radius at this height
if (rr < rs * 0.9 || z <= 0.0) return float4(0, 0, 0, 0);   // caps / part behind the door
float  a  = atan2(Local.y, Local.x) / 6.2831853 + 0.5;      // 0..1 around
float  t  = Clock;

float  cell = a * StreakCount;
float  id   = floor(cell);
float  f    = frac(cell) - 0.5;
float  h1   = G.Hash(id);
float  h2   = G.Hash(id + 17.0);
float  w    = StreakWidth * (0.5 + h1);
float  streak = exp(-pow(f / max(w, 1e-3), 2.0));
float  top  = 0.25 + 0.75 * h2;                              // streak height
float  vfade = pow(saturate(1.0 - z / top), 1.6);
float  shimmer = 0.65 + 0.35 * sin(z * 18.0 - t * RiseSpeed + h1 * 6.2831853);
float  s    = streak * vfade * shimmer * (0.4 + 0.6 * h1);

float  base = pow(1.0 - z, 5.0) * BaseGlow;                  // glow hugging the ring
float  i    = (s + base) * (0.85 + 0.15 * sin(t * 2.0));
i *= smoothstep(0.0, max(FadeIn, 1e-3), z);                  // no hard edge where the light starts
// Translucent: colour from Color*Intensity, coverage from the streak pattern.
// Bright Color = glowing shafts, dark Color = smoky shadow shafts.
return float4(Color.rgb * Intensity * lerp(1.0, i, ColorFromPattern), saturate(i * Opacity));
