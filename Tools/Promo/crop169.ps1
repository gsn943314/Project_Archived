param([string]$In, [string]$Out, [double]$Center = 0.5)
# Centre crop to 16:9 (full height).
Add-Type -AssemblyName System.Drawing
$src = [Drawing.Image]::FromFile($In)
$H = $src.Height; $W = [int][Math]::Round($H * 16 / 9)
$x = [int]([Math]::Min([Math]::Max($src.Width * $Center - $W / 2, 0), $src.Width - $W))
$bmp = New-Object Drawing.Bitmap $W, $H
$g = [Drawing.Graphics]::FromImage($bmp)
$g.DrawImage($src, (New-Object Drawing.Rectangle 0, 0, $W, $H), (New-Object Drawing.Rectangle $x, 0, $W, $H), [Drawing.GraphicsUnit]::Pixel)
$bmp.Save($Out, [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose(); $src.Dispose()
