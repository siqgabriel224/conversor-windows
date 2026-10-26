using System.Runtime.InteropServices;
using System.Windows.Threading;

namespace Conversor;

internal sealed class GestureService : IDisposable
{
    [StructLayout(LayoutKind.Sequential)]
    internal struct PointNative
    {
        public int X, Y;
    }
    [DllImport("user32.dll")] internal static extern bool GetCursorPos(out PointNative point);
    [DllImport("user32.dll")] internal static extern short GetAsyncKeyState(int key);
    private readonly DispatcherTimer timer = new() { Interval = TimeSpan.FromMilliseconds(25) };
    private readonly RadialWindow ring;
    private PointNative origin;
    private bool down, shown;
    private DateTime released;
    internal bool Enabled { get; set; } = true;
    internal int Modifier { get; set; } = 0x11;
    private bool tab;
    internal GestureService(RadialWindow ring)
    {
        this.ring = ring;
        timer.Tick += Tick;
        timer.Start();
    }
    private void Tick(object? sender, EventArgs args)
    {
        var pressed = (GetAsyncKeyState(1) & 0x8000) != 0;
        var ctrl = (GetAsyncKeyState(Modifier) & 0x8000) != 0;
        var next = (GetAsyncKeyState(0x09) & 0x8000) != 0;
        if (next && !tab && ring.IsVisible)
            ring.NextPage();
        tab = next;
        GetCursorPos(out var p);
        if (pressed && !down)
        {
            origin = p;
            shown = false;
        }
        if (pressed && down && !shown && ctrl && Enabled && (Math.Abs(p.X - origin.X) + Math.Abs(p.Y - origin.Y) > 18))
        {
            shown = true;
            ring.ShowAtCursor();
            Diagnostics.Write("gesture", "Ctrl + arrastar detectado");
        }
        if ((GetAsyncKeyState(0x1B) & 0x8000) != 0)
        {
            ring.Hide();
            if (pressed)
                shown = true;
        }
        if (!pressed && down)
            released = DateTime.UtcNow;
        if (!pressed && ring.IsVisible && (DateTime.UtcNow - released).TotalMilliseconds > 250)
            ring.Hide();
        down = pressed;
    }
    public void Dispose() => timer.Stop();
}
