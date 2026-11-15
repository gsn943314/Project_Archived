// =====================================================================
// Exit teleport pad - floor ring (Additive, Unlit, After-DOF translucency)
//   On /Engine/BasicShapes/Plane laid flat on the floor in front of the
//   exit arch. Bright ring line + rotating dash ring + soft inner fill.
//   After-DOF translucency is composited after the Storybook PP passes,
//   so the glow stays soft and is not repainted / outlined / erased.
// Source of truth for the Custom node in /Game/Dev/Materials/M_PortalRing.
// =====================================================================
float2 p  = Local.xy * PlaneScale;
float  r  = length(p) / max(Radius, 1.0);
float  a  = atan2(p.y, p.x);
float  t  = Clock;
float  pulse = 0.85 + 0.15 * sin(t * PulseSpeed);

float line_  = exp(-pow((r - 1.0) / max(RingWidth, 1e-3), 2.0));                 // main ring
float glow   = exp(-pow((r - 1.0) / max(RingWidth * 6.0, 1e-3), 2.0)) * 0.35;     // halo around it
float outer  = exp(-pow((r - 1.18) / max(RingWidth * 0.5, 1e-3), 2.0)) * 0.5;     // thin outer ring
float dashes = step(0.45, frac(a / 6.2831853 * DashCount + t * DashSpeed))
             * exp(-pow((r - 0.86) / max(RingWidth * 0.7, 1e-3), 2.0)) * 0.7;    // rotating ticks
float fill   = (1.0 - smoothstep(0.0, 1.0, r)) * InnerFill;

float i = (line_ + glow + outer + dashes + fill) * pulse;
return Color.rgb * i * Intensity * (1.0 - smoothstep(1.25, 1.4, r));
