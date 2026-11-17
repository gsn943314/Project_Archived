param([string]$In, [string]$Out, [double]$CropCenter = 0.5, [double]$LogoScale = 0.62)
# itch promo frame: 16:9 crop, real main-menu logo (Project tab + Archived paper) top-left,
# small olive pills "EDIT MODE" bottom-left / "PLAY MODE" bottom-right.
Add-Type -AssemblyName System.Drawing
$A = Join-Path $PSScriptRoot '..\MainMenu\Assets'
$OLIVE = [Drawing.Color]::FromArgb(255, 112, 120, 56)
$CREAM = [Drawing.Color]::FromArgb(255, 248, 232, 200)
function RRect([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $p = New-Object Drawing.Drawing2D.GraphicsPath; $d = 2 * $r
    $p.AddArc($x, $y, $d, $d, 180, 90); $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90); $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $p.CloseFigure(); return $p
}
function Soft($g, [Drawing.RectangleF]$r, [float]$rad, [float]$u) {
    for ($i = 5; $i -ge 1; $i--) {
        $e = $i * 3 * $u; $b = New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(9, 40, 30, 20))
        $p = RRect ($r.X - $e + 4 * $u) ($r.Y - $e + 8 * $u) ($r.Width + 2 * $e) ($r.Height + 2 * $e) ($rad + $e)
        $g.FillPath($b, $p); $b.Dispose(); $p.Dispose()
    }
}
function Pill($g, [string]$t, [float]$u, [float]$x, [float]$y, [bool]$alignRight) {
    $f = New-Object Drawing.Font 'Segoe UI', (34 * $u), ([Drawing.FontStyle]::Bold), ([Drawing.GraphicsUnit]::Pixel)
    $w = $g.MeasureString($t, $f).Width + 56 * $u; $h = 62 * $u
    if ($alignRight) { $x = $x - $w }
    $r = New-Object Drawing.RectangleF $x, $y, $w, $h
    Soft $g $r ($h / 2) ($u * 0.7)
    $p = RRect $x $y $w $h ($h / 2); $b = New-Object Drawing.SolidBrush $OLIVE; $g.FillPath($b, $p); $b.Dispose(); $p.Dispose()
    $sf = New-Object Drawing.StringFormat; $sf.Alignment = 'Center'; $sf.LineAlignment = 'Center'
    $b = New-Object Drawing.SolidBrush $CREAM; $g.DrawString($t, $f, $b, (New-Object Drawing.RectangleF $x, ($y + 2 * $u), $w, $h), $sf); $b.Dispose(); $f.Dispose()
}
$src = [Drawing.Image]::FromFile($In)
$H = $src.Height; $W = [int][Math]::Round($H * 16 / 9)
$cx = [int]([Math]::Min([Math]::Max($src.Width * $CropCenter - $W / 2, 0), $src.Width - $W))
$bmp = New-Object Drawing.Bitmap $W, $H
$g = [Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'; $g.InterpolationMode = 'HighQualityBicubic'
$g.DrawImage($src, (New-Object Drawing.Rectangle 0, 0, $W, $H), (New-Object Drawing.Rectangle $cx, 0, $W, $H), [Drawing.GraphicsUnit]::Pixel)
$u = $H / 1339.0
# logo: Archived paper with the Project tab overlapping its top-left, as on the main menu
$title = [Drawing.Image]::FromFile("$A\Title.png"); $proj = [Drawing.Image]::FromFile("$A\Project.png")
$s = $LogoScale * $u
$tw = $title.Width * $s; $th = $title.Height * $s; $pw = $proj.Width * $s; $ph = $proj.Height * $s
$lx = 64 * $u; $ly = 56 * $u + $ph * 0.55
Soft $g (New-Object Drawing.RectangleF $lx, $ly, $tw, $th) (30 * $s) $u
$g.DrawImage($title, $lx, $ly, $tw, $th)
$g.DrawImage($proj, $lx + 4 * $u, 56 * $u, $pw, $ph)
$title.Dispose(); $proj.Dispose()
Pill $g 'EDIT MODE' $u (64 * $u) ($H - 64 * $u - 62 * $u) $false
Pill $g 'PLAY MODE' $u ($W - 64 * $u) ($H - 64 * $u - 62 * $u) $true
$bmp.Save($Out, [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose(); $src.Dispose()
