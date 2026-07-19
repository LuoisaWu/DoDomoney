Add-Type -AssemblyName System.Drawing

$outputDirectory = Join-Path $PSScriptRoot "..\static\tabbar"
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

function New-CatIcon {
    param(
        [string]$Name,
        [string]$Color,
        [ValidateSet("ai", "entries", "insights", "loans", "more")]
        [string]$Kind
    )

    $bitmap = New-Object System.Drawing.Bitmap 81, 81
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
    $graphics.Clear([System.Drawing.Color]::Transparent)

    $strokeColor = [System.Drawing.ColorTranslator]::FromHtml($Color)
    $pen = New-Object System.Drawing.Pen $strokeColor, 5
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round

    $path = New-Object System.Drawing.Drawing2D.GraphicsPath
    $path.StartFigure()
    $path.AddLine(14, 33, 14, 13)
    $path.AddLine(14, 13, 29, 24)
    $path.AddBezier(29, 24, 36, 21, 45, 21, 52, 24)
    $path.AddLine(52, 24, 67, 13)
    $path.AddLine(67, 13, 67, 33)
    $path.AddBezier(67, 33, 74, 41, 72, 58, 62, 66)
    $path.AddBezier(62, 66, 51, 75, 30, 75, 19, 66)
    $path.AddBezier(19, 66, 9, 58, 7, 41, 14, 33)
    $path.CloseFigure()
    $graphics.DrawPath($pen, $path)

    switch ($Kind) {
        "ai" {
            $graphics.DrawEllipse($pen, 25, 39, 3, 3)
            $graphics.DrawEllipse($pen, 53, 39, 3, 3)
            $graphics.DrawArc($pen, 30, 43, 21, 14, 15, 150)
            $graphics.DrawLine($pen, 57, 29, 57, 37)
            $graphics.DrawLine($pen, 53, 33, 61, 33)
        }
        "entries" {
            $graphics.DrawLine($pen, 24, 38, 57, 38)
            $graphics.DrawLine($pen, 24, 48, 57, 48)
            $graphics.DrawLine($pen, 24, 58, 47, 58)
        }
        "insights" {
            $graphics.DrawLine($pen, 23, 59, 23, 51)
            $graphics.DrawLine($pen, 39, 59, 39, 42)
            $graphics.DrawLine($pen, 55, 59, 55, 33)
            $graphics.DrawLine($pen, 20, 61, 59, 61)
        }
        "loans" {
            $graphics.DrawEllipse($pen, 25, 34, 31, 31)
            $graphics.DrawLine($pen, 33, 43, 48, 43)
            $graphics.DrawLine($pen, 36, 50, 45, 50)
            $graphics.DrawLine($pen, 40, 43, 40, 59)
        }
        "more" {
            $brush = New-Object System.Drawing.SolidBrush $strokeColor
            $graphics.FillEllipse($brush, 23, 45, 7, 7)
            $graphics.FillEllipse($brush, 37, 45, 7, 7)
            $graphics.FillEllipse($brush, 51, 45, 7, 7)
            $brush.Dispose()
        }
    }

    $target = Join-Path $outputDirectory $Name
    $bitmap.Save($target, [System.Drawing.Imaging.ImageFormat]::Png)

    $path.Dispose()
    $pen.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
}

$icons = @("ai", "entries", "insights", "loans", "more")
foreach ($icon in $icons) {
    New-CatIcon -Name "$icon.png" -Color "#8a8072" -Kind $icon
    New-CatIcon -Name "$icon-active.png" -Color "#dc744d" -Kind $icon
}
