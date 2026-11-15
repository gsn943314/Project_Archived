// =====================================================================
// Portal paint mote (Masked, Unlit sprite for Niagara)
//   A soft-cornered brush dab instead of a glowing sparkle. Masked (not
//   translucent) so it writes depth: the Storybook PP keeps it over the
//   solid background and paints / outlines it like any other object.
//   Particle colour alpha dissolves the dab (shrinks it) for fade in/out.
// Source of truth for the Custom node in /Game/Dev/Materials/M_PortalMote.
// =====================================================================
float2 q   = UV * 2.0 - 1.0;
float  r   = length(q);
float  a   = atan2(q.y, q.x);
float  rim = 0.78 + 0.12 * sin(a * 3.0 + 1.3) + 0.07 * sin(a * 7.0 + 0.4);   // lumpy brush outline
float  sh  = rim - r;                                                      // > 0 inside the dab
float  core = smoothstep(0.0, 0.55, sh);
float  fade = saturate(ParticleA);
float  mask = saturate(0.5 + 3.0 * (sh - (1.0 - fade) * 0.75));
float3 c   = Particle.rgb * lerp(0.75, 1.25, core) * Glow;
return float4(c, mask);
