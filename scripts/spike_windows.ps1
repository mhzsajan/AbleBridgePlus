param()
# Enumerate visible top-level window titles of the Ableton Live process.
# Used by the v0.7 stem-export spike to detect the Export dialog appearing.

Add-Type @"
using System;
using System.Text;
using System.Collections.Generic;
using System.Runtime.InteropServices;
public class WinEnum {
    [DllImport("user32.dll")] static extern bool EnumWindows(EnumWindowsProc cb, IntPtr lp);
    [DllImport("user32.dll")] static extern int GetWindowText(IntPtr h, StringBuilder sb, int max);
    [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
    [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
    delegate bool EnumWindowsProc(IntPtr h, IntPtr lp);
    public static List<string> Titles(uint targetPid) {
        var res = new List<string>();
        EnumWindows((h, lp) => {
            uint pid; GetWindowThreadProcessId(h, out pid);
            if (pid == targetPid && IsWindowVisible(h)) {
                var sb = new StringBuilder(256);
                GetWindowText(h, sb, 256);
                if (sb.Length > 0) res.Add(sb.ToString());
            }
            return true;
        }, IntPtr.Zero);
        return res;
    }
}
"@

$proc = Get-Process "Ableton Live 12 Suite" -ErrorAction Stop
$titles = [WinEnum]::Titles($proc.Id)
$titles | Sort-Object -Unique
