param([string]$Grey, [string]$Final, [string]$Out, [double]$Top = 0.58, [double]$Bottom = 0.42)
# Split promo image: grey box left of a diagonal, final render right, thin white divider with a soft shadow.
# Top / Bottom: where the divider meets the top / bottom edge, as a fraction of the width.
Add-Type -AssemblyName System.Drawing
$f = [Drawing.Image]::FromFile($Final)
$g0 = [Drawing.Image]::FromFile($Grey)
$W = $f.Width; $H = $f.Height
$bmp = New-Object Drawing.Bitmap $W, $H
$gr = [Drawing.Graphics]::FromImage($bmp)
$gr.SmoothingMode = 'AntiAlias'
$gr.DrawImage($f, 0, 0, $W, $H)
$x0 = [float]($W * $Top); $x1 = [float]($W * $Bottom)
$poly = [Drawing.PointF[]]@((New-Object Drawing.PointF 0, 0), (New-Object Drawing.PointF $x0, 0), (New-Object Drawing.PointF $x1, $H), (New-Object Drawing.PointF 0, $H))
$path = New-Object Drawing.Drawing2D.GraphicsPath
$path.AddPolygon($poly)
$gr.SetClip($path)
$gr.DrawImage($g0, 0, 0, $W, $H)
$gr.ResetClip()
$lw = [float]([Math]::Max(4, $W / 500))
$sh = New-Object Drawing.Pen ([Drawing.Color]::FromArgb(90, 0, 0, 0)), ($lw * 3)
$gr.DrawLine($sh, $x0 + $lw, 0, $x1 + $lw, $H)
$pen = New-Object Drawing.Pen ([Drawing.Color]::FromArgb(255, 255, 252, 240)), $lw
$gr.DrawLine($pen, $x0, 0, $x1, $H)
$bmp.Save($Out, [Drawing.Imaging.ImageFormat]::Png)
$gr.Dispose(); $bmp.Dispose(); $f.Dispose(); $g0.Dispose()
