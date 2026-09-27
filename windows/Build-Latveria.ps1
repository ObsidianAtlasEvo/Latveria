<#
.SYNOPSIS
    Builds Castle Doom and Doomstadt in Minecraft Java 26.1.2 by typing the
    construction commands into chat, one at a time, at a gentle pace.

.DESCRIPTION
    No server files, datapacks or mods are needed - only operator permission
    (or cheats enabled in single player).

      1. Stand on the block you want as the centre of Doomstadt's plaza.
      2. Press F3 and note the "Block:" X Y Z (the block your feet are in).
      3. Run Build-Latveria.bat, type those three numbers, then click back
         into Minecraft and leave the keyboard and mouse alone.

    Hotkeys while it runs:   F7 = pause / resume     F10 = stop (progress is saved)
    If the Minecraft window loses focus the sender pauses by itself, so it can
    never type into another program. Run it again later to resume.

.PARAMETER DelayMs
    Pause after every command, in milliseconds (default 60). Raise it on a slow
    or busy server.
.PARAMETER ChatOpenMs
    Wait between pressing the chat key and pasting (default 80). Raise it if
    commands get lost (the chat box opens too slowly).
.PARAMETER HeavyFactor
    Multiplier for the extra pauses after big fills (default 1.0; 2.0 = twice as gentle).
.PARAMETER WindowMatch
    Text that must appear in the focused window's title (default "Minecraft").
.PARAMETER ChatKey
    The key that opens chat in your controls (default T).
.PARAMETER FromSection
    Start at the first section whose title contains this text (for example
    "Doom Tower"), to rebuild one part - e.g. if chunks were not loaded yet.
    Sections are listed in README.md and printed while the script runs.
.PARAMETER DryRun
    Do not type anything; write the final commands with real coordinates to
    latveria_resolved.txt so you can inspect them.
#>
[CmdletBinding()]
param(
    [string]$CommandFile = '',
    [int]$DelayMs = 60,
    [int]$ChatOpenMs = 80,
    [double]$HeavyFactor = 1.0,
    [string]$WindowMatch = 'Minecraft',
    [string]$ChatKey = 'T',
    [string]$FromSection = '',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
# Windows PowerShell 5.1 leaves $PSScriptRoot empty inside param(), so work out the folder here
$Here = $PSScriptRoot
if (-not $Here) { $Here = Split-Path -Parent $MyInvocation.MyCommand.Definition }
if (-not $Here) { $Here = (Get-Location).Path }
if (-not $CommandFile) { $CommandFile = Join-Path $Here 'latveria_commands.txt' }
$Inv = [Globalization.CultureInfo]::InvariantCulture
$ProgressFile = Join-Path $Here 'latveria_progress.txt'
$LogFile = Join-Path $Here 'latveria_log.txt'

# ---------------------------------------------------------------------------
# Win32 keyboard input (SendInput) and window/hotkey helpers
# ---------------------------------------------------------------------------
if (-not ('LatvInput' -as [type])) {
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;
public static class LatvInput {
    [StructLayout(LayoutKind.Sequential)] struct MOUSEINPUT { public int dx; public int dy; public uint mouseData; public uint dwFlags; public uint time; public IntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Sequential)] struct KEYBDINPUT { public ushort wVk; public ushort wScan; public uint dwFlags; public uint time; public IntPtr dwExtraInfo; }
    [StructLayout(LayoutKind.Explicit)] struct INPUTUNION { [FieldOffset(0)] public MOUSEINPUT mi; [FieldOffset(0)] public KEYBDINPUT ki; }
    [StructLayout(LayoutKind.Sequential)] struct INPUT { public uint type; public INPUTUNION u; }
    [DllImport("user32.dll", SetLastError = true)] static extern uint SendInput(uint n, INPUT[] inputs, int size);
    [DllImport("user32.dll")] static extern uint MapVirtualKey(uint code, uint mapType);
    [DllImport("user32.dll")] static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll", CharSet = CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder sb, int max);
    [DllImport("user32.dll")] static extern short GetAsyncKeyState(int vk);

    static INPUT Key(ushort vk, bool up) {
        INPUT i = new INPUT();
        i.type = 1;
        i.u.ki.wVk = vk;
        i.u.ki.wScan = (ushort)MapVirtualKey(vk, 0);
        i.u.ki.dwFlags = up ? 2u : 0u;
        return i;
    }
    static void Send(INPUT[] a) { SendInput((uint)a.Length, a, Marshal.SizeOf(typeof(INPUT))); }
    public static void Tap(int vk) { Send(new INPUT[] { Key((ushort)vk, false), Key((ushort)vk, true) }); }
    public static void Chord(int mod, int vk) {
        Send(new INPUT[] { Key((ushort)mod, false), Key((ushort)vk, false), Key((ushort)vk, true), Key((ushort)mod, true) });
    }
    public static bool Down(int vk) { return (GetAsyncKeyState(vk) & 0x8001) != 0; }
    public static string ForegroundTitle() {
        StringBuilder sb = new StringBuilder(512);
        GetWindowText(GetForegroundWindow(), sb, 512);
        return sb.ToString();
    }
}
'@
}

$VK_RETURN = 0x0D; $VK_CONTROL = 0x11; $VK_A = 0x41; $VK_V = 0x56
$VK_F7 = 0x76; $VK_F10 = 0x79
$VK_CHAT = [int][char]($ChatKey.ToUpper()[0])
if ($ChatKey -eq '/') { $VK_CHAT = 0xBF }

function Write-Log([string]$msg) {
    Add-Content -Path $LogFile -Value ("{0:yyyy-MM-dd HH:mm:ss}  {1}" -f (Get-Date), $msg)
}

# ---------------------------------------------------------------------------
# load the command list
# ---------------------------------------------------------------------------
if (-not (Test-Path $CommandFile)) { throw "Command file not found: $CommandFile" }
$items = New-Object System.Collections.Generic.List[object]
$section = 'Start'
foreach ($line in [IO.File]::ReadAllLines($CommandFile)) {
    if ($line.Length -eq 0 -or $line.StartsWith('#')) { continue }
    $parts = $line.Split("`t")
    if ($parts[0] -eq '!section') { $section = $parts[1]; continue }
    if ($parts[0] -eq '!wait') {
        $items.Add([pscustomobject]@{ Kind = 'wait'; Wait = [int]$parts[1]; Text = $parts[2]; Section = $section })
        continue
    }
    $items.Add([pscustomobject]@{ Kind = 'cmd'; Wait = [int]$parts[0]; Text = $parts[1]; Section = $section })
}
$total = $items.Count

# ---------------------------------------------------------------------------
# centre coordinates and resume
# ---------------------------------------------------------------------------
Write-Host ''
Write-Host '  ==========================================================' -ForegroundColor DarkGreen
Write-Host '     CASTLE DOOM & DOOMSTADT  -  Latverian construction script' -ForegroundColor Green
Write-Host '  ==========================================================' -ForegroundColor DarkGreen
Write-Host ("  {0} commands loaded from {1}" -f $total, (Split-Path $CommandFile -Leaf))
Write-Host ''

$start = 0
$cx = $null
if ((Test-Path $ProgressFile) -and -not $DryRun) {
    $p = (Get-Content $ProgressFile -Raw).Trim().Split(' ')
    if ($p.Count -ge 4) {
        $ans = Read-Host ("  A previous build stopped at command {0} of {1} (centre {2} {3} {4}). Resume it? [Y/n]" -f $p[3], $total, $p[0], $p[1], $p[2])
        if ($ans -notmatch '^[nN]') {
            $cx = [int]$p[0]; $cy = [int]$p[1]; $cz = [int]$p[2]
            $start = [Math]::Max(0, [int]$p[3] - 3)
        }
    }
}
if ($null -eq $cx) {
    Write-Host '  Stand on the centre block (the middle of the future plaza), press F3 and'
    Write-Host '  read the "Block:" line - the block your FEET are in.'
    while ($true) {
        $raw = Read-Host '  Centre X Y Z'
        $nums = [regex]::Matches($raw, '-?\d+') | ForEach-Object { [int]$_.Value }
        if ($nums.Count -eq 3) { $cx, $cy, $cz = $nums; break }
        Write-Host '  Please type three whole numbers, e.g.  120 68 -340' -ForegroundColor Yellow
    }
}
if ($FromSection -ne '') {
    $found = -1
    for ($i = 0; $i -lt $total; $i++) {
        if ($items[$i].Section -like "*$FromSection*") { $found = $i; break }
    }
    if ($found -lt 0) { Write-Host "  No section matches '$FromSection'." -ForegroundColor Red; exit 1 }
    $start = $found
    Write-Host ("  Starting from section: {0}" -f $items[$found].Section) -ForegroundColor Cyan
    Write-Host '  (If the build site is far from you, run the "Preparing the site" section first so the chunks are force-loaded.)'
}
if ($cy - 12 -lt -64 -or $cy + 130 -gt 319) {
    Write-Host ("  Y={0} is out of range: the build needs Y between -52 and 189." -f $cy) -ForegroundColor Red
    exit 1
}

function Resolve-Cmd([string]$text) {
    return [regex]::Replace($text, '\$([xyz])\((-?[0-9.]+)\)', {
        param($m)
        $v = [double]::Parse($m.Groups[2].Value, $Inv)
        switch ($m.Groups[1].Value) { 'x' { $v += $cx } 'y' { $v += $cy } 'z' { $v += $cz } }
        if ($v -eq [Math]::Floor($v)) { return ([long]$v).ToString($Inv) }
        return $v.ToString('0.###', $Inv)
    })
}

if ($DryRun) {
    $out = Join-Path $Here 'latveria_resolved.txt'
    $sb = New-Object System.Text.StringBuilder
    foreach ($it in $items) {
        if ($it.Kind -eq 'cmd') { [void]$sb.AppendLine('/' + (Resolve-Cmd $it.Text)) }
        else { [void]$sb.AppendLine('# wait ' + $it.Wait + ' ms: ' + $it.Text) }
    }
    [IO.File]::WriteAllText($out, $sb.ToString())
    Write-Host "  Dry run: wrote $out" -ForegroundColor Green
    exit 0
}

# time estimate
$perCmd = $ChatOpenMs + $DelayMs + 60
$remainMs = 0
for ($i = $start; $i -lt $total; $i++) {
    $it = $items[$i]
    if ($it.Kind -eq 'cmd') { $remainMs += $perCmd + $it.Wait * $HeavyFactor } else { $remainMs += $it.Wait }
}
Write-Host ''
Write-Host ("  Centre: {0} {1} {2}    starting at command {3}" -f $cx, $cy, $cz, ($start + 1))
Write-Host ("  Estimated time: about {0:N0} minutes" -f ($remainMs / 60000))
Write-Host ''
Write-Host '  BEFORE YOU CONTINUE' -ForegroundColor Yellow
Write-Host '   - you must be an operator (or have cheats on in single player)'
Write-Host '   - creative mode is recommended; you will be lifted onto a glass viewing platform'
Write-Host '   - everything within ~150 blocks east/west and from 250 north to 110 south of you'
Write-Host '     will be replaced. Back up your world first!'
Write-Host '   - F7 pauses / resumes, F10 stops. Alt-tabbing away pauses automatically.'
Write-Host ''
Read-Host '  Press Enter, then click into Minecraft (close any menus) within 10 seconds'
for ($s = 10; $s -gt 0; $s--) { Write-Host -NoNewline ("`r  Starting in {0,2} s ... " -f $s); Start-Sleep -Seconds 1 }
Write-Host ''
[void][LatvInput]::Down($VK_F7); [void][LatvInput]::Down($VK_F10)   # clear stale key presses
Write-Log ("start: centre {0} {1} {2}, index {3}" -f $cx, $cy, $cz, $start)

# ---------------------------------------------------------------------------
# the sender loop
# ---------------------------------------------------------------------------
function Save-Progress([int]$i) { Set-Content -Path $ProgressFile -Value ("{0} {1} {2} {3}" -f $cx, $cy, $cz, $i) }

function Wait-Released([int]$vk) { while ([LatvInput]::Down($vk)) { Start-Sleep -Milliseconds 30 } }

$paused = $false
function Check-Controls([int]$i) {
    # returns $false if the user asked to stop
    if ([LatvInput]::Down($VK_F10)) {
        Wait-Released $VK_F10
        Save-Progress $i
        Write-Host "`n  Stopped at command $($i + 1). Run the script again to resume." -ForegroundColor Yellow
        Write-Log "stopped by user at $i"
        return $false
    }
    if ([LatvInput]::Down($VK_F7)) {
        Wait-Released $VK_F7
        $script:paused = -not $script:paused
        if ($script:paused) { Save-Progress $i; Write-Host "`n  PAUSED (F7 to resume, F10 to stop)" -ForegroundColor Yellow }
        else { Write-Host "  resumed" -ForegroundColor Green; Start-Sleep -Milliseconds 800 }
    }
    return $true
}

$lastSection = ''
$sent = 0
$sw = [Diagnostics.Stopwatch]::StartNew()
for ($i = $start; $i -lt $total; $i++) {
    $it = $items[$i]
    if ($it.Section -ne $lastSection) {
        $lastSection = $it.Section
        Write-Host ("`n  [{0,5:N1}%]  {1}" -f (100.0 * $i / $total), $lastSection) -ForegroundColor Cyan
    }
    if (-not (Check-Controls $i)) { exit 0 }
    while ($paused) {
        Start-Sleep -Milliseconds 100
        if (-not (Check-Controls $i)) { exit 0 }
    }
    if ($it.Kind -eq 'wait') {
        Write-Host ("  waiting {0} s: {1}" -f [int]($it.Wait / 1000), $it.Text)
        $end = (Get-Date).AddMilliseconds($it.Wait)
        while ((Get-Date) -lt $end) {
            Start-Sleep -Milliseconds 200
            if (-not (Check-Controls $i)) { exit 0 }
        }
        continue
    }

    $cmd = '/' + (Resolve-Cmd $it.Text)
    if ($cmd.Length -gt 256) {
        Write-Host "  skipped (longer than chat allows): $cmd" -ForegroundColor Red
        Write-Log "SKIPPED too long: $cmd"
        continue
    }

    # never type unless Minecraft is the focused window
    $warned = $false
    while ([LatvInput]::ForegroundTitle() -notmatch [regex]::Escape($WindowMatch)) {
        if (-not $warned) {
            Write-Host "  Minecraft is not the active window - paused. Click back into the game to continue." -ForegroundColor Yellow
            Save-Progress $i
            $warned = $true
        }
        Start-Sleep -Milliseconds 250
        if (-not (Check-Controls $i)) { exit 0 }
    }
    if ($warned) { Write-Host "  continuing" -ForegroundColor Green; Start-Sleep -Milliseconds 1500 }

    for ($try = 0; $try -lt 5; $try++) {
        try { Set-Clipboard -Value $cmd; break } catch { Start-Sleep -Milliseconds 50 }
    }
    [LatvInput]::Tap($VK_CHAT)
    Start-Sleep -Milliseconds $ChatOpenMs
    [LatvInput]::Chord($VK_CONTROL, $VK_A)
    [LatvInput]::Chord($VK_CONTROL, $VK_V)
    Start-Sleep -Milliseconds 30
    [LatvInput]::Tap($VK_RETURN)
    $sent++
    Start-Sleep -Milliseconds ([int]($DelayMs + $it.Wait * $HeavyFactor))

    if ($sent % 25 -eq 0) {
        Save-Progress ($i + 1)
        $rate = $sent / [Math]::Max(1, $sw.Elapsed.TotalSeconds)
        $left = ($total - $i - 1) / [Math]::Max(0.1, $rate) / 60
        Write-Progress -Activity 'Building Latveria' -Status ("{0} / {1}   {2}   (~{3:N0} min left)" -f ($i + 1), $total, $lastSection, $left) -PercentComplete (100.0 * ($i + 1) / $total)
    }
}
Write-Progress -Activity 'Building Latveria' -Completed
if (Test-Path $ProgressFile) { Remove-Item $ProgressFile }
Write-Log "finished"
Write-Host ''
Write-Host '  Latveria is complete. Doom welcomes you.' -ForegroundColor Green
