param([string]$Grey, [string]$Final, [string]$Out, [double]$Top = 0.58, [double]$Bottom = 0.42, [double]$Feather = 0.16, [double]$Noise = 0.0)
# Soft split: grey box on the left fades into the final render on the right across a diagonal band.
# Feather: band width as a fraction of the image width (smoothstep). Noise > 0 roughens the band like a brush edge.
Add-Type -AssemblyName System.Drawing
if (-not ('SoftSplit' -as [type])) {
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition @'
using System;
using System.Drawing;
using System.Drawing.Imaging;
using System.Runtime.InteropServices;
public static class SoftSplit {
    static double Hash(int x, int y) { unchecked { uint h = (uint)(x * 374761393 + y * 668265263); h = (h ^ (h >> 13)) * 1274126177u; return (h ^ (h >> 16)) / 4294967295.0; } }
    static double VNoise(double x, double y) {
        int ix = (int)Math.Floor(x), iy = (int)Math.Floor(y); double fx = x - ix, fy = y - iy;
        fx = fx * fx * (3 - 2 * fx); fy = fy * fy * (3 - 2 * fy);
        double a = Hash(ix, iy), b = Hash(ix + 1, iy), c = Hash(ix, iy + 1), d = Hash(ix + 1, iy + 1);
        return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy;
    }
    public static void Blend(string grey, string final, string outp, double top, double bottom, double feather, double noise) {
        using (var g = new Bitmap(grey)) using (var f = new Bitmap(final)) {
            int W = f.Width, H = f.Height;
            var outb = new Bitmap(W, H, PixelFormat.Format32bppArgb);
            var r = new Rectangle(0, 0, W, H);
            var dg = g.LockBits(r, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            var df = f.LockBits(r, ImageLockMode.ReadOnly, PixelFormat.Format32bppArgb);
            var dout = outb.LockBits(r, ImageLockMode.WriteOnly, PixelFormat.Format32bppArgb);
            int n = W * H * 4;
            byte[] bg = new byte[n], bf = new byte[n], bo = new byte[n];
            Marshal.Copy(dg.Scan0, bg, 0, n); Marshal.Copy(df.Scan0, bf, 0, n);
            double half = feather * W * 0.5;
            for (int y = 0; y < H; y++) {
                double xs = (top + (bottom - top) * y / (double)(H - 1)) * W;      // divider x at this row
                for (int x = 0; x < W; x++) {
                    double d = x - xs;
                    if (noise > 0) {
                        double s = 1.0 / (W * 0.035);
                        double nn = VNoise(x * s, y * s) * 0.6 + VNoise(x * s * 3.1, y * s * 3.1) * 0.3 + VNoise(x * s * 9.7, y * s * 9.7) * 0.1;
                        d += (nn - 0.5) * 2.0 * noise * half;
                    }
                    double t = Math.Min(1, Math.Max(0, (d + half) / (2 * half)));
                    t = t * t * (3 - 2 * t);                                          // 0 = grey, 1 = final
                    int i = (y * W + x) * 4;
                    for (int c = 0; c < 3; c++) bo[i + c] = (byte)(bg[i + c] + (bf[i + c] - bg[i + c]) * t + 0.5);
                    bo[i + 3] = 255;
                }
            }
            Marshal.Copy(bo, 0, dout.Scan0, n);
            g.UnlockBits(dg); f.UnlockBits(df); outb.UnlockBits(dout);
            outb.Save(outp, ImageFormat.Png);
            outb.Dispose();
        }
    }
}
'@
}
[SoftSplit]::Blend($Grey, $Final, $Out, $Top, $Bottom, $Feather, $Noise)
