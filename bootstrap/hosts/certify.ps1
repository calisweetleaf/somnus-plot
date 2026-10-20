#Requires -Version 5.0
<#
 Somnus Plot host certification runner for Windows x64 (PowerShell 5+ or 7). P07-07, contracts section 11.

   powershell -ExecutionPolicy Bypass -File bootstrap\hosts\certify.ps1 -Out D:\plot-cert [-Quick]

 Copies the seed (no .git, no .grave) to a disposable directory, obtains Node through bootstrap\plot.ps1,
 runs bootstrap plan/acquire/verify and the Node suites on that Node, and records stdout, stderr and the
 exit code of every step under <Out>\win32-<arch>-<UTC stamp>\. It never writes PASS for the host:
 summary.json lists exit codes and a reviewer records the result in bootstrap\hosts\README.md.
 Suites that need sh or POSIX semantics fail or report NOT RUN on Windows; record them as such.
 $env:PLOT_KIT, $env:PLOT_OFFLINE and $env:PLOT_NODE pass through unchanged. -Quick is accepted for
 parity with certify.sh (there is no shell gate on Windows).
#>
param([Parameter(Mandatory = $true)][string]$Out, [switch]$Quick)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
$seed = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$arch = if ([Environment]::Is64BitOperatingSystem) { 'x64' } else { 'x86' }
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$dir = Join-Path (Resolve-Path -LiteralPath $Out).ProviderPath "win32-$arch-$stamp"
New-Item -ItemType Directory -Path $dir | Out-Null
$work = Join-Path ([IO.Path]::GetTempPath()) ('plot-certify-' + [Guid]::NewGuid().ToString('N').Substring(0, 8))
New-Item -ItemType Directory -Path $work | Out-Null
$steps = New-Object System.Collections.ArrayList
function Record([string]$name, [string]$exe, [string[]]$argv) {
  $o = Join-Path $dir "$name.out"; $e = Join-Path $dir "$name.err"
  try {
    $p = Start-Process -FilePath $exe -ArgumentList $argv -WorkingDirectory $work -NoNewWindow -Wait -PassThru `
      -RedirectStandardOutput $o -RedirectStandardError $e
    $code = $p.ExitCode
  } catch { Set-Content -LiteralPath $e -Value $_.Exception.Message; $code = -1 }
  [Console]::Error.WriteLine("$name exit=$code")
  [void]$steps.Add([ordered]@{ step = $name; exit = $code })
}
try {
  Get-ChildItem -LiteralPath $seed -Force | Where-Object { $_.Name -notin @('.git', '.grave', 'data.json') } |
    ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination $work -Recurse -Force }
  @("os: $([Environment]::OSVersion.VersionString)", "ps: $($PSVersionTable.PSVersion)", "cpu: $env:PROCESSOR_IDENTIFIER",
    "seed: $seed", "work: $work", "PLOT_KIT=$env:PLOT_KIT PLOT_OFFLINE=$env:PLOT_OFFLINE PLOT_NODE=$env:PLOT_NODE") |
    Set-Content -LiteralPath (Join-Path $dir 'host.txt')
  $ps = (Get-Process -Id $PID).Path
  Record 'node-path' $ps @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', (Join-Path $work 'bootstrap\plot.ps1'), '--node-path')
  $node = (Get-Content -LiteralPath (Join-Path $dir 'node-path.out') -ErrorAction SilentlyContinue | Select-Object -Last 1)
  if (-not $node -or -not (Test-Path -LiteralPath $node)) {
    [Console]::Error.WriteLine("certify: no Node obtained; see $dir\node-path.err")
  } else {
    $kit = @(); if ($env:PLOT_KIT) { $kit = @('--kit', $env:PLOT_KIT) }
    $off = @(); if ($env:PLOT_OFFLINE -eq '1') { $off = @('--offline') }
    Record 'node-version' $node @('--version')
    Record 'plan' $node (@('capabilities\bootstrap.mjs', 'plan', '--root', $work) + $kit + $off + @('--quiet'))
    Record 'acquire' $node (@('capabilities\bootstrap.mjs', 'acquire', 'python', 'git', '--root', $work) + $kit + $off + @('--quiet'))
    Record 'verify' $node @('capabilities\bootstrap.mjs', 'verify', '--root', $work, '--quiet')
    foreach ($suite in @('integration', 'resident', 'resident-env', 'cartographer', 'assembler', 'bootstrap', 'e2e', 'package-smoke')) {
      Record "suite-$suite" $node @("tests\$suite.mjs")
    }
    Get-ChildItem -Path (Join-Path $work '.grave\host') -Filter '.plot-host.json' -Recurse -Force -ErrorAction SilentlyContinue |
      ForEach-Object { Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $dir ($_.Directory.Name + '.plot-host.json')) }
  }
} finally {
  [ordered]@{ schema = 'plot.certify/1'; family = "win32-$arch"; at = $stamp; quick = [bool]$Quick
    status = 'RECORDED (review required; not a PASS)'; steps = $steps } | ConvertTo-Json -Depth 4 |
    Set-Content -LiteralPath (Join-Path $dir 'summary.json')
  Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
  [Console]::Error.WriteLine("certify: recorded $dir")
}
