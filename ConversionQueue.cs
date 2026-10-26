using System.Collections.ObjectModel;
using System.Diagnostics;
using System.Threading.Channels;
using System.Windows.Threading;

namespace Conversor;

/// <summary>Serializes work from the window, radial menu, CLI and watchers.</summary>
internal sealed class ConversionQueue
{
    private readonly Channel<ConversionJob> pending = Channel.CreateUnbounded<ConversionJob>();
    private readonly Catalog catalog;
    private readonly Dispatcher dispatcher;
    private readonly List<ConversionJob> records;

    internal ObservableCollection<ConversionJob> Jobs { get; } = [];
    internal event Action<ConversionJob>? Finished;

    internal ConversionQueue(Catalog catalog)
    {
        this.catalog = catalog;
        dispatcher = Application.Current.Dispatcher;
        records = AppPaths.Read(AppPaths.HistoryFile, () => new List<ConversionJob>());
        foreach (var record in records.TakeLast(200).Reverse())
        {
            if (record.IsBusy)
            {
                record.State = "Interrompido";
                record.Detail = "O aplicativo foi encerrado antes de concluir.";
            }
            Jobs.Add(record);
        }
        _ = Task.Run(ProcessPendingAsync);
    }

    internal List<ConversionJob> Enqueue(string[] files, string target, Preferences settings,
        string pages = "", int width = 0, string origin = "janela")
    {
        var added = new List<ConversionJob>();
        if (files.Length == 0)
            return added;
        IEnumerable<string[]> groups = target is "pdf-merge" or "zip" or "7z"
            ? new[] { files } : files.Select(file => new[] { file });
        foreach (var inputs in groups)
        {
            var job = new ConversionJob
            {
                Inputs = inputs,
                Target = target,
                Label = Catalog.Labels.GetValueOrDefault(target, target.ToUpperInvariant()),
                OutputDirectory = settings.OutputDirectory,
                Quality = settings.Quality,
                Pages = pages,
                Width = width,
                Origin = origin
            };
            Add(job);
            added.Add(job);
        }
        return added;
    }

    internal void EnqueueDownload(MediaDownloadRequest request)
    {
        var quality = request.Mode == "audio" ? "áudio"
            : request.MaxHeight > 0 ? $"até {request.MaxHeight}p" : "melhor qualidade";
        Add(new ConversionJob
        {
            Download = request,
            Target = request.Format,
            Origin = "download",
            OutputDirectory = request.OutputDirectory,
            Label = $"Download · {request.Format.ToUpperInvariant()} · {quality}" +
                    (request.IncludePlaylist ? " · playlist" : "")
        });
    }

    private void Add(ConversionJob job)
    {
        Jobs.Insert(0, job);
        records.Add(job);
        Persist();
        pending.Writer.TryWrite(job);
    }

    internal void EnqueueResize(string[] files, ResizeRequest request, string outputDirectory, int quality)
    {
        foreach (var file in files)
            Add(new ConversionJob
            {
                Inputs = [file],
                Resize = request,
                Origin = "redimensionador",
                Target = ResizeRequest.Videos.Contains(Path.GetExtension(file)) ? request.VideoFormat : request.ImageFormat,
                Label = $"Redimensionar · {request.Width} × {request.Height} · {(request.Mode == "cover" ? "recorte" : "faixas")}",
                OutputDirectory = outputDirectory,
                Quality = quality
            });
    }

    private void Persist()
    {
        try
        {
            AppPaths.Save(AppPaths.HistoryFile, records.TakeLast(500).ToList());
        }
        catch (Exception error) { Diagnostics.Write("history", error.Message); }
    }

    private async Task ProcessPendingAsync()
    {
        await foreach (var job in pending.Reader.ReadAllAsync())
        {
            if (job.Cancellation.IsCancellationRequested)
            {
                await UpdateAsync(() => Complete(job, "Cancelado", "Cancelado antes de iniciar"));
                continue;
            }
            await UpdateAsync(() =>
            {
                job.State = job.Download is null ? "Convertendo" : "Baixando";
                job.Progress = 0;
                job.Detail = job.Download is null ? "Preparando conversão local…" : "Consultando a plataforma…";
            });
            try
            {
                await ExecuteWorkerAsync(job);
            }
            catch (OperationCanceledException)
            {
                await UpdateAsync(() =>
                {
                    job.State = "Cancelado";
                    job.Detail = job.Outputs.Length > 0
                        ? $"Cancelado. {job.Outputs.Length} item(ns) já salvo(s) foram preservados."
                        : "Operação cancelada";
                });
            }
            catch (Exception error)
            {
                await UpdateAsync(() =>
                {
                    job.State = job.Cancellation.IsCancellationRequested ? "Cancelado" : "Falhou";
                    job.Detail = error.Message;
                });
                Diagnostics.Write("worker", error.Message);
            }
            await UpdateAsync(() => { Persist(); Finished?.Invoke(job); });
        }
    }

    private async Task ExecuteWorkerAsync(ConversionJob job)
    {
        var script = job.Resize is not null ? "resize_media.py" : job.Download is null ? "convert.py" : "media_download.py";
        var start = WorkerProcess.CreateStartInfo(catalog, script);
        using var process = new Process { StartInfo = start };
        process.Start();
        using var scope = new ProcessScope(process);
        var marker = Path.Combine(AppPaths.Data, "cancel-" + job.Id);
        using var registration = job.Cancellation.Token.Register(() =>
        {
            try
            {
                File.WriteAllText(marker, "");
            }
            catch (Exception error) when (error is IOException or UnauthorizedAccessException)
            {
                Diagnostics.Write("cancel", "Não foi possível gravar o pedido de cancelamento.");
            }
            _ = KillUnresponsiveWorkerAsync(process);
        });
        try
        {
            var errorTask = process.StandardError.ReadToEndAsync();
            await process.StandardInput.WriteLineAsync(CreateRequest(job, marker));
            process.StandardInput.Close();
            string? failure = null, warning = null;
            while (await process.StandardOutput.ReadLineAsync() is { } line)
            {
                try
                {
                    using var document = JsonDocument.Parse(line);
                    var root = document.RootElement;
                    if (root.TryGetProperty("progress", out var progress))
                    {
                        var value = progress.GetDouble();
                        var message = root.TryGetProperty("message", out var detail)
                            ? detail.GetString() ?? "Processando…" : "Processando…";
                        await UpdateAsync(() =>
                        {
                            job.Progress = Math.Max(job.Progress, Math.Clamp(value, 0, 100));
                            job.Detail = message;
                        });
                    }
                    if (root.TryGetProperty("outputs", out var outputs))
                    {
                        var paths = outputs.EnumerateArray().Select(item => item.GetString()!).ToArray();
                        await UpdateAsync(() => job.Outputs = paths);
                    }
                    if (root.TryGetProperty("error", out var error))
                        failure = error.GetString();
                    if (root.TryGetProperty("warning", out var notice))
                        warning = notice.GetString();
                }
                catch (JsonException) { Diagnostics.Write("worker", "Evento inválido recebido do componente."); }
            }
            await process.WaitForExitAsync();
            var stderr = await errorTask;
            job.Cancellation.Token.ThrowIfCancellationRequested();
            if (process.ExitCode != 0 || job.Outputs.Length == 0)
                throw new InvalidOperationException(failure ?? "O componente não gerou uma saída válida. " +
                    stderr[^Math.Min(stderr.Length, 400)..]);
            await UpdateAsync(() =>
            {
                job.Progress = 100;
                job.State = string.IsNullOrWhiteSpace(warning) ? "Concluído" : "Concluído com avisos";
                job.Detail = !string.IsNullOrWhiteSpace(warning) ? warning
                    : job.Outputs.Length == 1 ? job.Outputs[0]
                    : $"{job.Outputs.Length} resultados · {Path.GetDirectoryName(job.Outputs[0])}";
            });
        }
        finally { try { File.Delete(marker); } catch (IOException) { } }
    }

    private string CreateRequest(ConversionJob job, string marker)
    {
        if (job.Download is { } download)
            return JsonSerializer.Serialize(new
            {
                operation = "download",
                url = download.Url,
                mode = download.Mode,
                format = download.Format,
                maxHeight = download.MaxHeight,
                audioBitrate = download.AudioBitrate,
                includePlaylist = download.IncludePlaylist,
                outputDirectory = download.OutputDirectory,
                cancellationFile = marker,
                engines = catalog.Engines
            });
        return JsonSerializer.Serialize(new
        {
            inputs = job.Inputs,
            target = job.Target,
            outputDirectory = job.OutputDirectory,
            quality = job.Quality,
            pages = job.Pages,
            width = job.Width,
            resize = job.Resize is null ? null : new
            {
                width = job.Resize.Width,
                height = job.Resize.Height,
                mode = job.Resize.Mode,
                anchor = job.Resize.Anchor,
                imageFormat = job.Resize.ImageFormat,
                videoFormat = job.Resize.VideoFormat
            },
            cancellationFile = marker,
            engines = catalog.Engines
        });
    }

    private Task UpdateAsync(Action update) => dispatcher.InvokeAsync(update).Task;

    private void Complete(ConversionJob job, string state, string detail)
    {
        job.State = state;
        job.Detail = detail;
        Persist();
        Finished?.Invoke(job);
    }

    private static async Task KillUnresponsiveWorkerAsync(Process process)
    {
        await Task.Delay(TimeSpan.FromSeconds(5));
        try
        {
            if (!process.HasExited)
                process.Kill(entireProcessTree: true);
        }
        catch (Exception error) when (error is InvalidOperationException or System.ComponentModel.Win32Exception) { }
    }

    internal void CancelAll()
    {
        foreach (var job in Jobs.Where(job => job.IsBusy))
            job.Cancellation.Cancel();
    }

    internal void ClearCompleted()
    {
        foreach (var job in Jobs.Where(job => !job.IsBusy).ToArray())
        {
            Jobs.Remove(job);
            records.Remove(job);
        }
        Persist();
    }
}
