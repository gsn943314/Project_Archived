// MF_ComicGlitch - whole-object reload flicker (the fox's "reloading" look) for scene objects.
// Old look = ReloadFromColor shaded by the base luminance ("not loaded yet" clay).
//   OldLook (Custom Primitive Data 1, default 0): BPC_AssetReload flips it per step -> exact control.
//   Reload  (min of MI param and MPC_Glitch.Reload, default 1): whole-scene reload without a
//           component - each object flickers on its own phase, share of new grows with Reload.
//   PreviewLoop: Reload cycles by itself every PreviewPeriod (editor preview).
// Inputs: Base Seed T OldLook Reload Rate Loop Period FromColor
float seed = frac(sin(dot(Seed, float3(0.0127, 0.0311, 0.0219))) * 43758.5453);
float R = saturate(Reload);
if (Loop > 0.5)
{
    float c = frac(T / max(Period, 0.5) + seed * 0.37);
    R = saturate(c * 1.45 - 0.12);
}
float phase = frac(T * max(Rate, 0.1) + seed);
float globalOld = R >= 1.0 ? 0.0 : (R <= 0.0 ? 1.0 : step(R, phase));
float old = saturate(max(OldLook, globalOld));
float lum = dot(Base, float3(0.3, 0.59, 0.11));
float3 oldc = FromColor * (0.55 + 0.45 * saturate(lum * 1.6));
return lerp(Base, oldc, old);
