// =====================================================================
// Occlusion cutout (Custom node inside MF_OcclusionCutout)
//   Cuts a hole in walls that sit between the camera and a target point
//   (the fox in Play, the cursor / dragged block in edit mode).
//   The hole is a cone from the camera, so it keeps the same size on screen
//   whatever the zoom. Only pixels in front of the target and above its
//   feet are cut, so floors behind / below stay intact. The edge wobbles
//   like torn paper and gets a thin rim colour.
//   Driven by MPC_Occlusion (Enable = 0 -> no effect anywhere).
//   Returns float2(opacity mask 0/1, rim 0..1).
// Source of truth for the Custom node in /Game/Dev/Materials/Functions/MF_OcclusionCutout.
// =====================================================================
if (Enable < 0.5) return float2(1.0, 0.0);
float3 D = Target.xyz - CamPos;
float  L = length(D);
if (L < 1.0) return float2(1.0, 0.0);
float3 n = D / L;
float3 q = WorldPos - CamPos;
float  t = dot(q, n);                                   // depth along the view axis
float3 perp = q - t * n;
float  r = length(perp);
float  R = Radius * max(t, 0.0) / L;                    // cone: constant size on screen

// irregular, brushy outline (fixed in space around the view axis)
float3 up = abs(n.z) > 0.99 ? float3(1.0, 0.0, 0.0) : float3(0.0, 0.0, 1.0);
float3 u  = normalize(cross(up, n));
float3 v  = cross(n, u);
float  a  = atan2(dot(perp, v), dot(perp, u));
float  wob = 0.55 * sin(a * 3.0 + 1.3) + 0.30 * sin(a * 7.0 + 4.1) + 0.15 * sin(a * 13.0 + 2.7);
float  Re = R * (1.0 + EdgeNoise * wob);

// where cutting is allowed: in front of the target, above its feet
float front = saturate((L - NearMargin - t) / 20.0);
float above = saturate((WorldPos.z - (Target.z + FootOffset)) / 20.0);
float allow = front * above;

float cut  = (r < Re) ? allow : 0.0;
float mask = cut > 0.5 ? 0.0 : 1.0;
float band = max(Re * RimWidth, 1.0);
float rim  = (r >= Re) ? allow * (1.0 - saturate((r - Re) / band)) : 0.0;
return float2(mask, rim);
