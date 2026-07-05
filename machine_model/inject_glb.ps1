# 把 gem_faceting_machine.glb 以 base64 內嵌進 gemcraft.html
# 重跑 build_machine.py 產生新 GLB 後,執行本腳本更新遊戲內的機台
$root  = Split-Path -Parent $PSScriptRoot
$glb   = Join-Path $PSScriptRoot "gem_faceting_machine.glb"
$html  = Join-Path $root "gemcraft.html"
$b64   = [Convert]::ToBase64String([IO.File]::ReadAllBytes($glb))
$doc   = [IO.File]::ReadAllText($html)
$pattern = 'window\.MACHINE_GLB_B64="[^"]*";'
$doc   = [Regex]::Replace($doc, $pattern, ('window.MACHINE_GLB_B64="' + $b64 + '";'))
[IO.File]::WriteAllText($html, $doc)
Write-Host ("INJECT_OK base64 length = {0} KB" -f [math]::Round($b64.Length/1KB))
