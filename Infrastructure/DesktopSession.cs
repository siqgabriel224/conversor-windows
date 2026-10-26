using System.ComponentModel;
using System.Windows.Forms;
using Microsoft.Win32;
using Application = System.Windows.Application;
using MessageBox = System.Windows.MessageBox;

namespace Conversor;

/// <summary>Owns the desktop services for the lifetime of the tray application.</summary>
internal sealed class DesktopSession : IDisposable
{
    private readonly Application application;
    private readonly Preferences settings;
    private readonly Catalog catalog;
    private readonly ConversionQueue queue;
    private readonly MainWindow window;
    private readonly RadialWindow radialMenu;
    private readonly GestureService gesture;
    private readonly WatchService watchers;
    private readonly NotifyIcon tray;
    private readonly ContextMenuStrip trayMenu = new();
    private readonly CancellationTokenSource serverStop = new();
    private bool isExiting;

    internal DesktopSession(Application application)
    {
        this.application = application;
        settings = AppPaths.Read(AppPaths.PreferencesFile, () => new Preferences());
        catalog = new Catalog();
        queue = new ConversionQueue(catalog);
        radialMenu = new RadialWindow { GetFormats = catalog.RingFormats };
        gesture = new GestureService(radialMenu);
        watchers = new WatchService(settings, catalog, queue);
        window = new MainWindow(catalog, queue, settings, ApplySettings);
        tray = new NotifyIcon
        {
            Text = "Conversor · arquivos e mídia",
            Icon = LoadIcon(),
            Visible = true,
            ContextMenuStrip = trayMenu
        };

        trayMenu.Items.Add("Abrir Conversor", null, (_, _) => RevealWindow());
        trayMenu.Items.Add("Histórico e fila", null, (_, _) => window.ShowHistory());
        trayMenu.Items.Add(new ToolStripSeparator());
        trayMenu.Items.Add("Sair", null, (_, _) => RequestExit());
        tray.DoubleClick += (_, _) => RevealWindow();
        window.Closing += HideWindowOnClose;
        radialMenu.ConvertRequested += EnqueueFromRadialMenu;
        queue.Finished += NotifyFinishedJob;
    }

    internal void Start(bool inBackground)
    {
        _ = Protocol.Serve(queue, catalog, settings, RevealWindow, serverStop.Token);
        try
        {
            ApplySettings();
            AppPaths.Save(AppPaths.PreferencesFile, settings);
        }
        catch (Exception error) { Diagnostics.Write("config", error.Message); }

        if (!inBackground)
            RevealWindow();
    }

    private void ApplySettings()
    {
        gesture.Enabled = settings.GestureEnabled;
        gesture.Modifier = settings.Modifier switch
        {
            "Alt" => 0x12,
            "Shift" => 0x10,
            _ => 0x11
        };
        watchers.Reload();

        using var startup = Registry.CurrentUser.CreateSubKey(
            @"Software\Microsoft\Windows\CurrentVersion\Run");
        if (settings.StartWithWindows)
            startup.SetValue("Conversor", $"\"{Environment.ProcessPath}\" --background");
        else
            startup.DeleteValue("Conversor", throwOnMissingValue: false);
    }

    private void RevealWindow()
    {
        window.Show();
        window.WindowState = WindowState.Normal;
        window.Activate();
    }

    private void HideWindowOnClose(object? sender, CancelEventArgs closing)
    {
        // Only the tray's Exit command shuts down the process.
        if (isExiting)
            return;
        closing.Cancel = true;
        window.Hide();
    }

    private void RequestExit()
    {
        if (queue.Jobs.Any(job => job.IsBusy))
        {
            var answer = MessageBox.Show("Há tarefas em andamento. Cancelar e sair?",
                "Conversor", MessageBoxButton.YesNo);
            if (answer != MessageBoxResult.Yes)
                return;
        }

        isExiting = true;
        queue.CancelAll();
        tray.Visible = false;
        radialMenu.Close();
        window.Close();
        application.Shutdown();
    }

    private void EnqueueFromRadialMenu(string[] paths, string target)
    {
        queue.Enqueue(paths, target, settings, origin: "menu circular");
        tray.ShowBalloonTip(1800, "Conversor",
            $"{paths.Length} arquivo(s) adicionado(s) à fila", ToolTipIcon.Info);
    }

    private void NotifyFinishedJob(ConversionJob job)
    {
        if (window.IsVisible)
            return;
        var icon = job.State == "Falhou" ? ToolTipIcon.Warning : ToolTipIcon.Info;
        tray.ShowBalloonTip(2200, "Conversor", $"{job.Name}: {job.State}", icon);
    }

    private static System.Drawing.Icon LoadIcon()
    {
        var path = Path.Combine(AppPaths.Root, "assets", "conversor.ico");
        return File.Exists(path)
            ? new System.Drawing.Icon(path)
            : System.Drawing.SystemIcons.Application;
    }

    public void Dispose()
    {
        serverStop.Cancel();
        queue.CancelAll();
        gesture.Dispose();
        watchers.Dispose();
        tray.Visible = false;
        tray.Dispose();
        trayMenu.Dispose();
        serverStop.Dispose();
    }
}
