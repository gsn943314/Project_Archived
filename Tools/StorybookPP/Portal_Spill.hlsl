// =====================================================================
// Exit portal light spill (Additive, Unlit, After-DOF translucency)
//   Vertical plane just in front of the exit arch: a bright line along the
//   opening edge, light pouring over the stone frame outside it, and a
//   brighter rim just inside. Pairs with M_PortalBeams laid out of the door.
//   Coordinates: plane local XY * PlaneScale = cm, origin at the spring line
//   of the opening (centre of the top semicircle); FlipY fixes the up axis.
// Source of truth for the Custom node in /Game/Dev/Materials/M_PortalSpill.
// =====================================================================
struct FPS
{
    float Hash(float n) { return frac(sin(n * 12.9898) * 43758.5453); }
    float Noise(float x) { float i = floor(x); float f = frac(x); f = f * f * (3.0 - 2.0 * f); return lerp(Hash(i), Hash(i + 1.0), f); }
};
FPS G;

float2 p = Local.xy * PlaneScale;
p.y *= FlipY;
if (p.y < -GroundDepth) return float4(0, 0, 0, 0);
float W = OpenHalfW;
float d, s;                                   // d > 0 outside the opening, s = arc length (0 at top)
if (p.y >= 0.0) { d = length(p) - W; s = atan2(p.x, p.y) * W; }
else            { d = abs(p.x) - W; s = sign(p.x) * (1.5707963 * W - p.y); }

float t    = Clock;
float var  = 0.6 + 0.4 * G.Noise(s / 28.0 + t * 0.8);                  // flickering along the edge
// radial streaks: narrow bands across the edge, each with its own length, slowly breathing
float sc   = s / max(StreakSpacing, 1.0);
float sid  = floor(sc);
float sh   = G.Hash(sid + 5.3);
float sw   = exp(-pow((frac(sc) - 0.5) / 0.22, 2.0));
float slen = 0.5 + sh * (0.8 + 0.3 * sin(t * 1.3 + sh * 6.2832));
var = lerp(var, sw * slen * 1.6, saturate(Streaks));
float fallMul = lerp(1.0, 0.5 + slen, saturate(Streaks));               // longer streaks reach further
float edge = exp(-pow(d / max(LineWidth, 0.1), 2.0));
float outF = d > 0.0 ? exp(-d / max(SpillFalloff * fallMul, 1.0)) * var : 0.0;
outF *= 1.0 - smoothstep(MaxReach * 0.7, MaxReach, d);                  // hard limit: never reaches the walls around
float inF  = d < 0.0 ? exp(d / max(InnerFalloff, 1.0)) : 0.0;
float i    = edge * LineAmount + outF * SpillAmount + inF * InnerAmount;
i *= 0.9 + 0.1 * sin(t * 2.0);
return float4(Color.rgb * Intensity * lerp(1.0, i, ColorFromPattern), saturate(i * Opacity));
