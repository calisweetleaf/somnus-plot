#Requires -Version 5.0
<#
 Somnus Plot Node-absent launcher for Windows (entry B, docs/V07-CONTRACTS.md section 11).

 Irreducible host inputs, declared rather than assumed:
   - Windows PowerShell 5.0+ (or PowerShell 7) with .NET Framework 4.5+ (Expand-Archive, Get-FileHash,
     System.Net.HttpWebRequest, Add-Type for one kernel32 CreateDirectoryW call)
   - either HTTPS reachability to nodejs.org, or $env:PLOT_KIT naming an offline kit directory
     (kit.json + SHA256SUMS + archives, built by `node capabilities/bootstrap.mjs kit <dir> --hosts win32-x64`)
 Node is obtained into <root>\.grave\host\node-<ver>-win32-<arch>-XXXXXX, completion marker written
 last, then the same main.js runs. No administrator rights, no winget/choco/scoop, no remote script.

 Environment: PLOT_ROOT, PLOT_KIT, PLOT_OFFLINE=1, PLOT_NODE (operator-supplied node.exe),
 PLOT_NODE_MIRROR (same layout as https://nodejs.org/dist; artifacts stay sha256-pinned), PLOT_LOCK_WAIT (seconds).
 `plot.ps1 bootstrap <args>` runs capabilities\bootstrap.mjs; `plot.ps1 --node-path` prints node.exe.
#>
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$NodeVersion = '24.22.0'
# Pins mirror bootstrap/recipes/node.json (tests/bootstrap.mjs asserts they agree).
$Pins = @{
  'win32-x64' = @{ File = "node-v$NodeVersion-win-x64.zip"; Sha256 = 'f9683a19877e12a9b167305c8db71040d812876359de21f0d2e97c3f321f80c3'; Size = 37733703 }
}
function Say([string]$m) { [Console]::Error.WriteLine("[plot.ps1] $m") }
function Die([string]$m) { Say $m; exit 1 }

$seed = Split-Path -Parent $PSScriptRoot
$main = Join-Path $seed 'main.js'
if (-not (Test-Path -LiteralPath $main)) { Die "main.js not found at $main" }
$root = if ($env:PLOT_ROOT) { (Resolve-Path -LiteralPath $env:PLOT_ROOT).ProviderPath } else { $seed }

function Start-Seed([string]$node, [object[]]$rest) {
  $env:PATH = (Split-Path -Parent $node) + ';' + $env:PATH
  $env:PLOT_ROOT = $root
  if ($rest.Count -gt 0 -and $rest[0] -eq '--node-path') { Write-Output $node; exit 0 }
  if ($rest.Count -gt 0 -and $rest[0] -eq 'bootstrap') {
    $tail = @(); if ($rest.Count -gt 1) { $tail = $rest[1..($rest.Count - 1)] }
    & $node (Join-Path $seed 'capabilities\bootstrap.mjs') @tail; exit $LASTEXITCODE
  }
  & $node $main --root $root @rest; exit $LASTEXITCODE
}

if ($env:PLOT_NODE) {
  if (-not (Test-Path -LiteralPath $env:PLOT_NODE)) { Die "PLOT_NODE does not exist: $env:PLOT_NODE" }
  Say "using operator-supplied Node $env:PLOT_NODE (no acquisition)"
  Start-Seed $env:PLOT_NODE $args
}

$arch = switch ($env:PROCESSOR_ARCHITECTURE) { 'AMD64' { 'x64' } 'ARM64' { 'arm64' } default { $env:PROCESSOR_ARCHITECTURE } }
if ($env:PROCESSOR_ARCHITEW6432 -eq 'AMD64') { $arch = 'x64' }
$key = "win32-$arch"
if (-not $Pins.ContainsKey($key)) { Die "unsupported host ${key}: no pinned Node archive (see bootstrap/recipes/node.json); set PLOT_NODE to a node.exe you provide" }
$pin = $Pins[$key]
$base = if ($env:PLOT_NODE_MIRROR) { $env:PLOT_NODE_MIRROR } else { 'https://nodejs.org/dist' }
$url = "$base/v$NodeVersion/$($pin.File)"
$id = "node-$NodeVersion-$key"
$hostDir = Join-Path $root '.grave\host'
$lockDir = Join-Path $hostDir ".locks\$id"
$nameRx = '^' + [regex]::Escape($id) + '-[A-Za-z0-9]{6}$'

function Test-Install([string]$d) {
  $m = Join-Path $d '.plot-host.json'
  if (-not (Test-Path -LiteralPath $m) -or -not (Test-Path -LiteralPath (Join-Path $d 'node.exe'))) { return $false }
  try { $j = [IO.File]::ReadAllText($m) | ConvertFrom-Json } catch { return $false }
  return ($j.schema -eq 'plot.host/1' -and $j.id -eq $id -and $j.source.sha256 -eq $pin.Sha256 -and $j.path -eq (Get-Item -LiteralPath $d).FullName)
}
function Find-Install {
  if (-not (Test-Path -LiteralPath $hostDir)) { return $null }
  foreach ($d in (Get-ChildItem -LiteralPath $hostDir -Directory | Where-Object { $_.Name -match $nameRx } | Sort-Object Name)) {
    if (Test-Install $d.FullName) { return $d.FullName }
  }
  return $null
}
function Get-Sha([string]$f) { (Get-FileHash -Algorithm SHA256 -LiteralPath $f).Hash.ToLowerInvariant() }

$found = Find-Install
if ($found) { Start-Seed (Join-Path $found 'node.exe') $args }

foreach ($d in '.locks', '.stage', '.dl', '.attempts') { [void][IO.Directory]::CreateDirectory((Join-Path $hostDir $d)) }
# Directory.CreateDirectory succeeds on an existing directory; the lock needs CreateDirectoryW's exclusivity.
Add-Type -Namespace PlotNative -Name Kernel32 -MemberDefinition '[DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)] public static extern bool CreateDirectoryW(string path, System.IntPtr security);'
$attempt = (Get-Date).ToUniversalTime().ToString('yyyyMMddHHmmss') + "-$PID-ps1"
$locked = $false; $stage = $null; $final = $null
function Clear-Attempt {
  if ($script:stage -and (Test-Path -LiteralPath $script:stage)) { Remove-Item -LiteralPath $script:stage -Recurse -Force }
  if ($script:final -and (Test-Path -LiteralPath $script:final) -and -not (Test-Path -LiteralPath (Join-Path $script:final '.plot-host.json'))) { Remove-Item -LiteralPath $script:final -Recurse -Force }
  if ($script:locked) { Remove-Item -LiteralPath (Join-Path $lockDir 'owner.json') -Force -ErrorAction SilentlyContinue; Remove-Item -LiteralPath $lockDir -Force -ErrorAction SilentlyContinue; $script:locked = $false }
}

try {
  $limit = if ($env:PLOT_LOCK_WAIT) { [int]$env:PLOT_LOCK_WAIT } else { 1800 }
  $t0 = Get-Date; $waited = $false
  while (-not [PlotNative.Kernel32]::CreateDirectoryW($lockDir, [IntPtr]::Zero)) {
    $own = $null; $ownerFile = Join-Path $lockDir 'owner.json'
    try { $own = [IO.File]::ReadAllText($ownerFile) } catch { }
    $stale = $false
    if ($own) {
      $o = $own | ConvertFrom-Json
      if (-not (Get-Process -Id ([int]$o.pid) -ErrorAction SilentlyContinue)) { $stale = $true }
    } elseif (((Get-Date) - (Get-Item -LiteralPath $lockDir).LastWriteTime).TotalSeconds -gt 10) { $stale = $true }
    if ($stale -and [PlotNative.Kernel32]::CreateDirectoryW("$lockDir.break", [IntPtr]::Zero)) {
      try {
        $again = $null; try { $again = [IO.File]::ReadAllText($ownerFile) } catch { }
        if ($again -eq $own) { $dead = Join-Path $hostDir ".locks\.dead-$id-$PID"; Move-Item -LiteralPath $lockDir -Destination $dead; Remove-Item -LiteralPath $dead -Recurse -Force; Say 'broke stale lock' }
      } finally { Remove-Item -LiteralPath "$lockDir.break" -Force }
      continue
    }
    if (-not $waited) { Say "waiting for concurrent acquisition of $id" }; $waited = $true
    if (((Get-Date) - $t0).TotalSeconds -gt $limit) { Die "lock on $id held beyond $limit s" }
    Start-Sleep -Milliseconds 200
  }
  $locked = $true
  [IO.File]::WriteAllText((Join-Path $lockDir 'owner.json'), ('{"pid":' + $PID + ',"birth":null,"attempt":"' + $attempt + '","writer":"plot.ps1"}'))
  $found = Find-Install
  if ($found) { Clear-Attempt; Say "shared concurrent acquisition $found"; Start-Seed (Join-Path $found 'node.exe') $args }
  Get-ChildItem -LiteralPath $hostDir -Directory | Where-Object { $_.Name -match $nameRx -and -not (Test-Path -LiteralPath (Join-Path $_.FullName '.plot-host.json')) } | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force; Say "removed interrupted stage $($_.FullName)" }
  Get-ChildItem -LiteralPath (Join-Path $hostDir '.stage') -Directory | Where-Object { $_.Name.StartsWith("$id-") } | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }

  $kitFile = if ($env:PLOT_KIT) { Join-Path $env:PLOT_KIT $pin.File } else { $null }
  if ($kitFile -and (Test-Path -LiteralPath $kitFile)) {
    $sums = Join-Path $env:PLOT_KIT 'SHA256SUMS'
    if ((Test-Path -LiteralPath $sums) -and -not (Select-String -LiteralPath $sums -SimpleMatch "$($pin.Sha256)  $($pin.File)" -Quiet)) { Die "kit SHA256SUMS does not record the pinned sha256 for $($pin.File)" }
    if ((Get-Sha $kitFile) -ne $pin.Sha256) { Die "kit file $kitFile does not match pinned sha256 $($pin.Sha256)" }
    $archive = $kitFile; $source = [ordered]@{ kind = 'kit'; file = $pin.File; url = $null; path = $kitFile }
  } else {
    if ($env:PLOT_OFFLINE) { Die "offline and no kit carries $($pin.File) (set PLOT_KIT)" }
    $archive = Join-Path $hostDir ".dl\$($pin.Sha256).zip"; $part = "$archive.part"
    if (-not (Test-Path -LiteralPath $archive)) {
      [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
      for ($i = 0; $i -lt 4; $i++) {
        $have = 0; if (Test-Path -LiteralPath $part) { $have = (Get-Item -LiteralPath $part).Length }
        if ($have -gt $pin.Size) { Remove-Item -LiteralPath $part -Force; $have = 0 }
        if ($have -eq $pin.Size) { break }
        try {
          $req = [Net.HttpWebRequest]::Create($url); $req.Timeout = 60000; $req.ReadWriteTimeout = 60000; $req.AllowAutoRedirect = $true
          if ($have -gt 0) { $req.AddRange([long]$have); Say "resuming at byte $have" }
          $res = $req.GetResponse()
          $mode = if ($have -gt 0 -and [int]$res.StatusCode -eq 206) { [IO.FileMode]::Append } else { [IO.FileMode]::Create }
          $out = [IO.File]::Open($part, $mode, [IO.FileAccess]::Write)
          try { $in = $res.GetResponseStream(); $buf = New-Object byte[] 1048576; while (($n = $in.Read($buf, 0, $buf.Length)) -gt 0) { $out.Write($buf, 0, $n) }; $out.Flush($true) }
          finally { $out.Dispose(); $res.Close() }
        } catch [Net.WebException] {
          $code = $null; if ($_.Exception.Response) { $code = [int]$_.Exception.Response.StatusCode }
          if ($code -in 400, 401, 403, 404, 410) { Die "source unavailable: $url answered HTTP $code; supply PLOT_KIT" }
          Say "transient: $($_.Exception.Message); retry $($i + 1)"
          Start-Sleep -Milliseconds ([int](500 * [math]::Pow(2, $i) * (0.5 + (Get-Random -Minimum 0.0 -Maximum 1.0))))
        }
      }
      if (-not (Test-Path -LiteralPath $part) -or (Get-Item -LiteralPath $part).Length -ne $pin.Size) { Die "download failed: $url (rerun to resume, or set PLOT_KIT)" }
      $got = Get-Sha $part
      if ($got -ne $pin.Sha256) { Remove-Item -LiteralPath $part -Force; Die "sha256 mismatch for ${url}: got $got, pinned $($pin.Sha256); discarded" }
      Move-Item -LiteralPath $part -Destination $archive
    }
    $source = [ordered]@{ kind = 'online'; file = $pin.File; url = $url; path = $null }
  }

  $suffix = -join ((48..57) + (65..90) + (97..122) | Get-Random -Count 6 | ForEach-Object { [char]$_ })
  $stage = Join-Path $hostDir ".stage\$id-$suffix"
  [void][IO.Directory]::CreateDirectory($stage)
  Expand-Archive -LiteralPath $archive -DestinationPath $stage
  $top = Join-Path $stage ($pin.File -replace '\.zip$', '')
  if (-not (Test-Path -LiteralPath (Join-Path $top 'node.exe'))) { Die "archive $($pin.File) did not contain node.exe" }
  $final = Join-Path $hostDir "$id-$suffix"
  Move-Item -LiteralPath $top -Destination $final
  Remove-Item -LiteralPath $stage -Recurse -Force; $stage = $null
  $node = Join-Path $final 'node.exe'
  $out = (& $node --version | Out-String).Trim()
  if ($out -ne "v$NodeVersion") { Die "acquired node reports '$out', expected v$NodeVersion" }
  $source.sha256 = $pin.Sha256; $source.size = $pin.Size; $source.publisher = 'Node.js project (official release)'
  $marker = [ordered]@{ schema = 'plot.host/1'; id = $id; tool = 'node'; version = $NodeVersion; platform = 'win32'; arch = $arch; libc = $null; route = 'binary'; provenance = 'pinned-recipe'; source = $source; inputs = $null
    path = (Get-Item -LiteralPath $final).FullName; exe = 'node.exe'; bin = '.'; probe = [ordered]@{ args = @('--version'); output = $out }; tree = $null; writer = 'plot.ps1'; attempt = $attempt; at = (Get-Date).ToUniversalTime().ToString('o') }
  $tmp = Join-Path $final '.plot-host.json.tmp'
  [IO.File]::WriteAllText($tmp, ($marker | ConvertTo-Json -Compress -Depth 6), (New-Object Text.UTF8Encoding $false))
  Move-Item -LiteralPath $tmp -Destination (Join-Path $final '.plot-host.json')
  if ($source.kind -eq 'online') { Remove-Item -LiteralPath $archive -Force }
  Say "acquired $id from $($source.kind) into $final"
  $final = $null
} finally { Clear-Attempt }
Start-Seed $node $args
