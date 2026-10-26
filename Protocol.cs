using System.IO.Pipes;
using System.Diagnostics;
using System.Text;

namespace Conversor;

public static class Protocol
{
    private static string UserId
    {
        get
        {
            var profile = Environment.GetFolderPath(Environment.SpecialFolder.UserProfile);
            var hash = System.Security.Cryptography.SHA256.HashData(Encoding.UTF8.GetBytes(profile));
            return Convert.ToHexString(hash)[..16];
        }
    }
    internal static string InstanceName => "Local\\Conversor-" + UserId;
    private static string PipeName => "Conversor-" + UserId;
    internal static void Activate()
    {
        try
        {
            using var pipe = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut);
            pipe.Connect(3000);
            using var writer = new StreamWriter(pipe, leaveOpen: true) { AutoFlush = true };
            writer.WriteLine("{\"command\":\"activate\"}");
        }
        catch { }
    }
    internal static async Task Serve(ConversionQueue queue, Catalog catalog, Preferences settings, Action activate, CancellationToken token)
    {
        while (!token.IsCancellationRequested)
        {
            var pipe = new NamedPipeServerStream(PipeName, PipeDirection.InOut, 8, PipeTransmissionMode.Byte, PipeOptions.Asynchronous | PipeOptions.CurrentUserOnly);
            try
            {
                await pipe.WaitForConnectionAsync(token);
                _ = Handle(pipe, queue, catalog, settings, activate, token);
            }
            catch (OperationCanceledException) { pipe.Dispose(); break; }
            catch (Exception e) { pipe.Dispose(); Diagnostics.Write("ipc", e.Message); await Task.Delay(1000, token); }
        }
    }
    private static async Task Handle(NamedPipeServerStream pipe, ConversionQueue queue, Catalog catalog, Preferences settings, Action activate, CancellationToken token)
    {
        using (pipe)
        using (var reader = new StreamReader(pipe, Encoding.UTF8, leaveOpen: true))
        using (var writer = new StreamWriter(pipe, new UTF8Encoding(false), leaveOpen: true) { AutoFlush = true })
        {
            Action<ConversionJob>? completed = null;
            try
            {
                var line = await reader.ReadLineAsync(token);
                if (line == null || line.Length > 1000000)
                    return;
                using var json = JsonDocument.Parse(line);
                var root = json.RootElement;
                if (root.GetProperty("command").GetString() == "activate")
                {
                    await System.Windows.Application.Current.Dispatcher.InvokeAsync(activate);
                    return;
                }
                var files = root.GetProperty("inputs").EnumerateArray().Select(e => Path.GetFullPath(e.GetString()!)).ToArray();
                var target = root.GetProperty("target").GetString()!;
                if (files.Length == 0 || files.Any(f => !File.Exists(f)))
                    throw new InvalidOperationException("Arquivo de entrada inexistente.");
                if (target == "pdf-merge")
                {
                    if (files.Any(f => Catalog.Category(f) != "pdf") || files.Length < 2)
                        throw new InvalidOperationException("Juntar exige dois ou mais PDFs.");
                }
                else if (!catalog.Common(files).Any(o => o.Id == target))
                    throw new InvalidOperationException("Formato de saída incompatível com a seleção.");
                var preferences = new Preferences
                {
                    OutputDirectory = root.TryGetProperty("output", out var output) && !string.IsNullOrWhiteSpace(output.GetString())
                        ? output.GetString()! : settings.OutputDirectory,
                    Quality = root.TryGetProperty("quality", out var quality)
                        ? quality.GetInt32() : settings.Quality
                };
                var pages = root.TryGetProperty("pages", out var pg) ? pg.GetString() ?? "" : "";
                var width = root.TryGetProperty("width", out var wd) ? wd.GetInt32() : 0;
                var done = new TaskCompletionSource<ConversionJob[]>(TaskCreationOptions.RunContinuationsAsynchronously);
                await Application.Current.Dispatcher.InvokeAsync(() =>
                {
                    var jobs = queue.Enqueue(files, target, preferences, pages, width, "linha de comando");
                    completed = _ =>
                    {
                        if (jobs.All(job => !job.IsBusy))
                            done.TrySetResult(jobs.ToArray());
                    };
                    queue.Finished += completed;
                });
                var result = await done.Task.WaitAsync(token);
                await writer.WriteLineAsync(JsonSerializer.Serialize(new
                {
                    success = result.All(j => j.State == "Concluído"),
                    jobs = result.Select(j => new { state = j.State, detail = j.Detail, outputs = j.Outputs })
                }));
            }
            catch (Exception error) { try { await writer.WriteLineAsync(JsonSerializer.Serialize(new { success = false, error = error.Message })); } catch { } }
            finally { if (completed != null) await System.Windows.Application.Current.Dispatcher.InvokeAsync(() => queue.Finished -= completed); }
        }
    }
    public static int RunCli(string[] args)
    {
        try
        {
            if (args.Length == 0 || args[0] is "help" or "--help")
            {
                Console.WriteLine("Conversor — conversão local\nUso: conversor convert arquivo.png --to webp [-o pasta] [--quality 85] [--width 1200] [--pages 1-3]\nUse vários arquivos ou curingas. O processo aguarda os resultados e retorna 0 em sucesso, 1 em falha.");
                return 0;
            }
            if (args[0] != "convert")
                throw new ArgumentException("Comando inválido. Use conversor help.");
            var files = new List<string>();
            var target = "";
            var output = "";
            var quality = 85;
            var width = 0;
            var pages = "";
            for (var i = 1; i < args.Length; i++)
            {
                string Value()
                {
                    if (++i >= args.Length)
                        throw new ArgumentException("Falta o valor da opção.");
                    return args[i];
                }
                switch (args[i])
                {
                    case "--to":
                        target = Value();
                        break;
                    case "-o":
                    case "--output":
                        output = Path.GetFullPath(Value());
                        break;
                    case "--quality":
                        quality = int.Parse(Value());
                        break;
                    case "--width":
                        width = int.Parse(Value());
                        break;
                    case "--pages":
                        pages = Value();
                        break;
                    default:
                        var path = Path.GetFullPath(args[i]);
                        if (path.Contains('*') || path.Contains('?'))
                            files.AddRange(Directory.GetFiles(Path.GetDirectoryName(path)!, Path.GetFileName(path)));
                        else
                            files.Add(path);
                        break;
                }
            }
            if (files.Count == 0 || target.Length == 0)
                throw new ArgumentException("Informe os arquivos e --to formato.");
            if (quality is < 1 or > 100 || width is < 0 or > 16000)
                throw new ArgumentException("Qualidade: 1–100; largura: 0–16000.");
            using var pipe = new NamedPipeClientStream(".", PipeName, PipeDirection.InOut);
            try
            {
                pipe.Connect(1000);
            }
            catch (TimeoutException)
            {
                StartDesktopInBackground();
                pipe.Connect(15000);
            }
            using var writer = new StreamWriter(pipe, new UTF8Encoding(false), leaveOpen: true) { AutoFlush = true };
            using var reader = new StreamReader(pipe, Encoding.UTF8, leaveOpen: true);
            writer.WriteLine(JsonSerializer.Serialize(new
            {
                command = "convert",
                inputs = files.Distinct().ToArray(),
                target,
                output,
                quality,
                width,
                pages
            }));
            var line = reader.ReadLine() ?? throw new IOException("O Conversor encerrou antes de responder.");
            Console.WriteLine(line);
            using var result = JsonDocument.Parse(line);
            return result.RootElement.GetProperty("success").GetBoolean() ? 0 : 1;
        }
        catch (Exception e) { Console.Error.WriteLine(e.Message); return 1; }
    }

    private static void StartDesktopInBackground()
    {
        var executable = Path.Combine(AppContext.BaseDirectory, "Conversor.exe");
        if (!File.Exists(executable))
            executable = Path.Combine(AppPaths.Root, "bin", "Release", "net10.0-windows", "Conversor.exe");
        Process.Start(new ProcessStartInfo(executable, "--background") { UseShellExecute = true });
    }
}
