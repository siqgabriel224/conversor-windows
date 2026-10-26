using System.Windows.Interop;
using System.Windows.Shapes;

namespace Conversor;

internal sealed class RadialWindow : Window
{
    private readonly Canvas canvas = new();
    private string[] formats = ["png", "jpg", "webp", "pdf"];
    private string[] files = [];
    private string[] allFormats = [];
    private int page;
    internal event Action<string[], string>? ConvertRequested;
    internal Func<string[], string[]>? GetFormats
    {
        get; set;
    }
    internal RadialWindow()
    {
        Title = "Conversor • menu circular";
        Width = 460;
        Height = 460;
        WindowStyle = WindowStyle.None;
        AllowsTransparency = true;
        Background = Brushes.Transparent;
        ShowInTaskbar = false;
        Topmost = true;
        ShowActivated = false;
        AllowDrop = true;
        Content = canvas;
        canvas.Background = Brushes.Transparent;
        SourceInitialized += (_, _) => { var h = new WindowInteropHelper(this).Handle; var ex = Native.GetWindowLong(h, -20); Native.SetWindowLong(h, -20, ex | 0x08000000 | 0x80); };
        DragOver += OnDrag;
        Drop += OnDrop;
        Draw(-1);
    }
    internal void ShowAtCursor()
    {
        GestureService.GetCursorPos(out var p);
        var screen = System.Windows.Forms.Screen.FromPoint(new System.Drawing.Point(p.X, p.Y));
        // Place the window first so WPF receives the destination monitor's DPI.
        var dpi = IsVisible ? VisualTreeHelper.GetDpi(this).DpiScaleX : 1.0;
        Left = p.X / dpi - Width / 2;
        Top = p.Y / dpi - Height / 2;
        files = [];
        page = 0;
        allFormats = [];
        formats = [];
        Draw(-1);
        Show();
        dpi = VisualTreeHelper.GetDpi(this).DpiScaleX;
        var r = screen.WorkingArea;
        Left = Math.Clamp(p.X / dpi - Width / 2, r.Left / dpi, Math.Max(r.Left / dpi, r.Right / dpi - Width));
        Top = Math.Clamp(p.Y / dpi - Height / 2, r.Top / dpi, Math.Max(r.Top / dpi, r.Bottom / dpi - Height));
    }
    private void OnDrag(object sender, DragEventArgs e)
    {
        if (!e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            e.Effects = DragDropEffects.None;
            e.Handled = true;
            return;
        }
        var incoming = (string[])e.Data.GetData(DataFormats.FileDrop);
        if (!incoming.SequenceEqual(files))
        {
            files = incoming;
            page = 0;
            allFormats = GetFormats?.Invoke(files) ?? ["png", "jpg", "webp", "pdf"];
            formats = allFormats.Take(8).ToArray();
        }
        var index = Index(e.GetPosition(canvas));
        Draw(index);
        e.Effects = index >= 0 ? DragDropEffects.Copy : DragDropEffects.None;
        e.Handled = true;
    }
    internal void NextPage()
    {
        if (allFormats.Length <= 8)
            return;
        page = (page + 1) % ((allFormats.Length + 7) / 8);
        formats = allFormats.Skip(page * 8).Take(8).ToArray();
        Draw(-1);
    }
    private void OnDrop(object sender, DragEventArgs e)
    {
        var index = Index(e.GetPosition(canvas));
        if (e.Data.GetDataPresent(DataFormats.FileDrop) && index >= 0)
        {
            var paths = (string[])e.Data.GetData(DataFormats.FileDrop);
            var target = formats[index];
            Hide();
            ConvertRequested?.Invoke(paths, target);
            e.Effects = DragDropEffects.Copy;
        }
        e.Handled = true;
    }
    private int Index(Point p)
    {
        var x = p.X - 230;
        var y = p.Y - 230;
        var radius = Math.Sqrt(x * x + y * y);
        if (radius < 83 || radius > 196 || formats.Length == 0)
            return -1;
        var angle = (Math.Atan2(y, x) + Math.PI / 2 + Math.PI * 2) % (Math.PI * 2);
        return Math.Min(formats.Length - 1, (int)(angle / (Math.PI * 2) * formats.Length));
    }
    private void Draw(int active)
    {
        canvas.Children.Clear();
        for (var i = 0; i < formats.Length; i++)
        {
            var a = i * Math.PI * 2 / formats.Length - Math.PI / 2 + 0.022;
            var b = (i + 1) * Math.PI * 2 / formats.Length - Math.PI / 2 - 0.022;
            Point P(double r, double t) => new(230 + r * Math.Cos(t), 230 + r * Math.Sin(t));
            var geom = new StreamGeometry();
            using (var g = geom.Open())
            {
                g.BeginFigure(P(90, a), true, true);
                g.LineTo(P(192, a), true, false);
                g.ArcTo(P(192, b), new Size(192, 192), 0, b - a > Math.PI, SweepDirection.Clockwise, true, false);
                g.LineTo(P(90, b), true, false);
                g.ArcTo(P(90, a), new Size(90, 90), 0, b - a > Math.PI, SweepDirection.Counterclockwise, true, false);
            }
            var shape = new System.Windows.Shapes.Path { Data = geom, Fill = new SolidColorBrush(i == active ? Color.FromRgb(98, 224, 192) : Color.FromRgb(26, 33, 45)), Stroke = new SolidColorBrush(Color.FromRgb(54, 68, 86)), StrokeThickness = 1 };
            canvas.Children.Add(shape);
            var mid = (a + b) / 2;
            var label = new TextBlock { Text = Catalog.Labels.GetValueOrDefault(formats[i], formats[i].ToUpperInvariant()), FontSize = formats[i].Length > 6 ? 12 : 17, TextWrapping = TextWrapping.Wrap, FontWeight = FontWeights.SemiBold, Foreground = i == active ? new SolidColorBrush(Color.FromRgb(10, 25, 23)) : Brushes.White, Width = 100, TextAlignment = TextAlignment.Center };
            Canvas.SetLeft(label, 180 + 140 * Math.Cos(mid));
            Canvas.SetTop(label, 218 + 140 * Math.Sin(mid));
            canvas.Children.Add(label);
        }
        var center = new TextBlock { Text = files.Length == 0 ? "ARRASTE\nUM ARQUIVO" : formats.Length == 0 ? "Sem conversão\ncompatível" : allFormats.Length > 8 ? $"SOLTE NO FORMATO\nTab · página {page + 1}" : "SOLTE NO\nFORMATO", Foreground = new SolidColorBrush(Color.FromRgb(155, 171, 189)), FontSize = 12, Width = 150, TextAlignment = TextAlignment.Center };
        Canvas.SetLeft(center, 155);
        Canvas.SetTop(center, 212);
        canvas.Children.Add(center);
    }
    private static class Native
    {
        [System.Runtime.InteropServices.DllImport("user32.dll")] internal static extern int GetWindowLong(IntPtr h, int i);
        [System.Runtime.InteropServices.DllImport("user32.dll")] internal static extern int SetWindowLong(IntPtr h, int i, int value);
    }
}
