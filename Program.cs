namespace Conversor;

public static class Program
{
    [STAThread]
    public static int Main(string[] args)
    {
        using var mutex = new Mutex(true, Protocol.InstanceName, out var isFirstInstance);
        if (!isFirstInstance)
        {
            Protocol.Activate();
            return 0;
        }

        var application = new Application { ShutdownMode = ShutdownMode.OnExplicitShutdown };
        application.DispatcherUnhandledException += (_, error) =>
        {
            Diagnostics.Write("error", error.Exception.ToString());
            MessageBox.Show(error.Exception.Message, "Conversor");
            error.Handled = true;
        };

        using var session = new DesktopSession(application);
        session.Start(inBackground: args.Contains("--background"));
        return application.Run();
    }
}
