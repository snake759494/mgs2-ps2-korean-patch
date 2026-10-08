# Windows 일본어 OCR: 폴더의 PNG -> TSV(파일명\t인식결과)
param([string]$InDir, [string]$OutFile)
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Graphics, ContentType = WindowsRuntime]
$null = [Windows.Globalization.Language, Windows.Globalization, ContentType = WindowsRuntime]
$asTask = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {
    $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' })[0]
function Await($op, [Type]$t) {
    $m = $asTask.MakeGenericMethod($t)
    $task = $m.Invoke($null, @($op))
    $task.Wait() | Out-Null
    $task.Result
}
$lang = New-Object Windows.Globalization.Language 'ja'
$eng = [Windows.Media.Ocr.OcrEngine]::TryCreateFromLanguage($lang)
$sw = New-Object System.IO.StreamWriter($OutFile, $false, [System.Text.Encoding]::UTF8)
foreach ($f in Get-ChildItem $InDir -Filter *.png) {
    try {
        $file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($f.FullName)) ([Windows.Storage.StorageFile])
        $stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
        $dec = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
        $bmp = Await ($dec.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
        $res = Await ($eng.RecognizeAsync($bmp)) ([Windows.Media.Ocr.OcrResult])
        foreach ($ln in $res.Lines) {
            $xs = $ln.Words | ForEach-Object { $_.BoundingRect }
            $x0 = ($xs | Measure-Object -Property X -Minimum).Minimum
            $y0 = ($xs | Measure-Object -Property Y -Minimum).Minimum
            $x1 = ($xs | ForEach-Object { $_.X + $_.Width } | Measure-Object -Maximum).Maximum
            $y1 = ($xs | ForEach-Object { $_.Y + $_.Height } | Measure-Object -Maximum).Maximum
            $sw.WriteLine($f.BaseName + "`t" + [int]$x0 + "," + [int]$y0 + "," + [int]$x1 + "," + [int]$y1 + "`t" + $ln.Text)
        }
        $stream.Dispose()
    } catch { $sw.WriteLine($f.BaseName + "`tERR") }
}
$sw.Close()
