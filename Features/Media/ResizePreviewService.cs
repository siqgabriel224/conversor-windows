using System.Diagnostics;
using System.Windows.Media.Imaging;

namespace Conversor;

internal sealed class ResizePreviewService(Catalog catalog)
{
    internal async Task<BitmapSource> CreateAsync(string source, ResizeRequest request, CancellationToken cancellation)
    {
        var folder = Path.Combine(Path.GetTempPath(), "Conversor-preview-" + Guid.NewGuid().ToString("N"));
        try
        {
            var start = WorkerProcess.CreateStartInfo(catalog, "resize_media.py");
            using var process = new Process { StartInfo = start };
            process.Start();
            using var scope = new ProcessScope(process);
            using var registration = cancellation.Register(() => TerminateWorker(process));
            var errors = process.StandardError.ReadToEndAsync();
            var events = process.StandardOutput.ReadToEndAsync();

            await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(new
            {
                inputs = new[] { source },
                preview = true,
                outputDirectory = folder,
                engines = catalog.Engines,
                resize = new
                {
                    width = request.Width,
                    height = request.Height,
                    mode = request.Mode,
                    anchor = request.Anchor,
                    imageFormat = request.ImageFormat,
                    videoFormat = request.VideoFormat
                }
            }));
            process.StandardInput.Close();
            await process.WaitForExitAsync();
            var response = await events;
            await errors;
            cancellation.ThrowIfCancellationRequested();

            var output = ReadOutput(response, process.ExitCode);
            return LoadImage(output);
        }
        finally
        {
            try
            {
                if (Directory.Exists(folder))
                    Directory.Delete(folder, recursive: true);
            }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { }
        }
    }

    private static string ReadOutput(string events, int exitCode)
    {
        string? output = null, error = null;
        foreach (var line in events.Split('\n', StringSplitOptions.RemoveEmptyEntries))
        {
            using var document = JsonDocument.Parse(line);
            if (document.RootElement.TryGetProperty("outputs", out var paths))
                output = paths[0].GetString();
            if (document.RootElement.TryGetProperty("error", out var message))
                error = message.GetString();
        }
        if (exitCode != 0 || output is null)
            throw new InvalidOperationException(error ?? "Não foi possível gerar a prévia.");
        return output;
    }

    private static BitmapSource LoadImage(string path)
    {
        // Load the pixels before removing the temporary file.
        var bitmap = new BitmapImage();
        bitmap.BeginInit();
        bitmap.CacheOption = BitmapCacheOption.OnLoad;
        bitmap.DecodePixelWidth = 640;
        bitmap.UriSource = new Uri(path);
        bitmap.EndInit();
        bitmap.Freeze();
        return bitmap;
    }

    private static void TerminateWorker(Process process)
    {
        try
        {
            process.Kill(entireProcessTree: true);
        }
        catch (InvalidOperationException) { }
        catch (System.ComponentModel.Win32Exception) { }
    }
}
