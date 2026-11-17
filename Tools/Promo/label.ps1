param([string]$In, [string]$Out,
      [string]$LTag = 'EDIT MODE', [string]$LText = 'Rebuild the world',
      [string]$RTag = 'PLAY MODE', [string]$RText = 'Watch it come alive')
# Main-menu style labels (olive tab over a cream rounded panel, dark brown bold text) on a split promo image.
Add-Type -AssemblyName System.Drawing
$OLIVE = [Drawing.Color]::FromArgb(255, 112, 120, 56)
$CREAM = [Drawing.Color]::FromArgb(255, 248, 232, 200)
$BROWN = [Drawing.Color]::FromArgb(255, 80, 56, 48)

function RRect([float]$x, [float]$y, [float]$w, [float]$h, [float]$r) {
    $p = New-Object Drawing.Drawing2D.GraphicsPath
    $d = 2 * $r
    $p.AddArc($x, $y, $d, $d, 180, 90); $p.AddArc($x + $w - $d, $y, $d, $d, 270, 90)
    $p.AddArc($x + $w - $d, $y + $h - $d, $d, $d, 0, 90); $p.AddArc($x, $y + $h - $d, $d, $d, 90, 90)
    $p.CloseFigure(); return $p
}
function Shadow($g, [float]$x, [float]$y, [float]$w, [float]$h, [float]$r, [float]$u) {
    for ($i = 6; $i -ge 1; $i--) {
        $e = $i * 3 * $u
        $b = New-Object Drawing.SolidBrush ([Drawing.Color]::FromArgb(10, 40, 30, 20))
        $p = RRect ($x - $e + 6 * $u) ($y - $e + 10 * $u) ($w + 2 * $e) ($h + 2 * $e) ($r + $e)
        $g.FillPath($b, $p); $b.Dispose(); $p.Dispose()
    }
}
function Block($g, [float]$u, [bool]$right, [float]$W, [string]$tag, [string]$text) {
    $fTag = New-Object Drawing.Font 'Segoe UI', (40 * $u), ([Drawing.FontStyle]::Bold), ([Drawing.GraphicsUnit]::Pixel)
    $fTxt = New-Object Drawing.Font 'Segoe UI', (62 * $u), ([Drawing.FontStyle]::Bold), ([Drawing.GraphicsUnit]::Pixel)
    $sf = New-Object Drawing.StringFormat; $sf.Alignment = 'Center'; $sf.LineAlignment = 'Center'
    $tw = $g.MeasureString($text, $fTxt).Width; $gw = $g.MeasureString($tag, $fTag).Width
    $pw = $tw + 90 * $u; $ph = 120 * $u                    # cream panel
    $tgw = $gw + 64 * $u; $tgh = 70 * $u                   # olive tab
    $m = 70 * $u
    $px = if ($right) { $W - $m - $pw } else { $m }
    $py = $m + $tgh * 0.62
    $tx = $px + 26 * $u; $ty = $m
    Shadow $g $px $py $pw $ph (30 * $u) $u
    $p = RRect $px $py $pw $ph (30 * $u); $b = New-Object Drawing.SolidBrush $CREAM; $g.FillPath($b, $p); $b.Dispose(); $p.Dispose()
    Shadow $g $tx $ty $tgw $tgh ($tgh / 2) ($u * 0.6)
    $p = RRect $tx $ty $tgw $tgh ($tgh / 2); $b = New-Object Drawing.SolidBrush $OLIVE; $g.FillPath($b, $p); $b.Dispose(); $p.Dispose()
    $b = New-Object Drawing.SolidBrush $CREAM
    $g.DrawString($tag, $fTag, $b, (New-Object Drawing.RectangleF $tx, ($ty + 2 * $u), $tgw, $tgh), $sf); $b.Dispose()
    $b = New-Object Drawing.SolidBrush $BROWN
    $g.DrawString($text, $fTxt, $b, (New-Object Drawing.RectangleF $px, ($py + 14 * $u), $pw, $ph), $sf); $b.Dispose()
    $fTag.Dispose(); $fTxt.Dispose()
}
$src = [Drawing.Image]::FromFile($In)
$bmp = New-Object Drawing.Bitmap $src.Width, $src.Height
$g = [Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = 'AntiAlias'; $g.TextRenderingHint = 'AntiAliasGridFit'
$g.DrawImage($src, 0, 0, $src.Width, $src.Height)
$u = $src.Height / 1339.0
Block $g $u $false $src.Width $LTag $LText
Block $g $u $true $src.Width $RTag $RText
$bmp.Save($Out, [Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose(); $src.Dispose()
