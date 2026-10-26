using System.Diagnostics;

namespace Conversor;

/// <summary>Runs URL inspection away from the UI and from the conversion queue.</summary>
internal sealed class MediaInspectionService(Catalog catalog)
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNameCaseInsensitive = true
    };

    internal async Task<MediaInspection> InspectAsync(
        string url, bool includePlaylist, CancellationToken cancellationToken)
    {
        if (!catalog.Engines.ContainsKey("ytdlp") || !catalog.Engines.ContainsKey("deno"))
            throw new InvalidOperationException("Os componentes de download não estão instalados. Prepare yt-dlp e Deno.");

        var startInfo = WorkerProcess.CreateStartInfo(catalog, "media_download.py");

        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        timeout.CancelAfter(TimeSpan.FromMinutes(2));
        using var process = new Process { StartInfo = startInfo };
        process.Start();
        using var scope = new ProcessScope(process);
        using var registration = timeout.Token.Register(() =>
        {
            try
            {
                if (!process.HasExited)
                    process.Kill(entireProcessTree: true);
            }
            catch (Exception error) when (error is InvalidOperationException or System.ComponentModel.Win32Exception) { }
        });

        var errorTask = process.StandardError.ReadToEndAsync();
        await process.StandardInput.WriteLineAsync(JsonSerializer.Serialize(new
        {
            operation = "inspect",
            url,
            includePlaylist,
            engines = catalog.Engines
        }));
        process.StandardInput.Close();

        MediaInspection? metadata = null;
        string? error = null;
        while (await process.StandardOutput.ReadLineAsync() is { } line)
        {
            using var document = JsonDocument.Parse(line);
            if (document.RootElement.TryGetProperty("metadata", out var value))
                metadata = value.Deserialize<MediaInspection>(JsonOptions);
            if (document.RootElement.TryGetProperty("error", out var failure))
                error = failure.GetString();
        }
        await process.WaitForExitAsync();
        await errorTask;
        cancellationToken.ThrowIfCancellationRequested();
        if (timeout.IsCancellationRequested)
            throw new TimeoutException("A plataforma demorou para responder. Tente consultar o link novamente.");
        if (process.ExitCode != 0 || metadata is null)
            throw new InvalidOperationException(error ?? "Não foi possível consultar o link.");
        return metadata;
    }
}
