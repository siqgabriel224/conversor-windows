namespace Conversor;

public partial class MainWindow
{
    private MediaInspectionService? mediaInspector;
    private MediaInspection? inspectedMedia;
    private CancellationTokenSource? analysisCancellation;

    private void InitializeDownloads()
    {
        mediaInspector = new MediaInspectionService(catalog);
        DownloadOutputDirectory.Text = settings.DownloadDirectory;
        DownloadMode.ItemsSource = new[] { "Vídeo com áudio", "Somente áudio" };
        DownloadMode.SelectedIndex = 0;
        Closed += (_, _) => analysisCancellation?.Cancel();
    }

    private void DownloadLinkChanged(object sender, TextChangedEventArgs e) => InvalidateMediaInspection();
    private void DownloadPlaylistChanged(object sender, RoutedEventArgs e) => InvalidateMediaInspection();

    private void InvalidateMediaInspection()
    {
        if (mediaInspector is null)
            return;
        analysisCancellation?.Cancel();
        inspectedMedia = null;
        DownloadButton.IsEnabled = false;
        DownloadMediaTitle.Text = "Consulte o link para continuar";
        DownloadMediaDetails.Text = "A qualidade será consultada na plataforma antes de baixar.";
    }

    private async void AnalyzeDownloadLink(object sender, RoutedEventArgs e)
    {
        if (mediaInspector is null)
            return;
        using var cancellation = new CancellationTokenSource();
        analysisCancellation = cancellation;
        AnalyzeDownloadButton.IsEnabled = false;
        DownloadButton.IsEnabled = false;
        CancelAnalysisButton.Visibility = Visibility.Visible;
        DownloadMediaTitle.Text = "Consultando o link…";
        DownloadMediaDetails.Text = "A plataforma pode levar alguns segundos para responder.";
        try
        {
            var metadata = await mediaInspector.InspectAsync(
                DownloadUrl.Text.Trim(), DownloadPlaylist.IsChecked == true, cancellation.Token);
            inspectedMedia = metadata;
            DownloadMediaTitle.Text = metadata.Title;
            var duration = metadata.Duration > 0
                ? TimeSpan.FromSeconds(metadata.Duration).ToString(@"hh\:mm\:ss") : "duração não informada";
            DownloadMediaDetails.Text = metadata.IsPlaylist
                ? $"{metadata.Platform} · {metadata.PlaylistCount} item(ns) identificado(s) · {metadata.Uploader}"
                : $"{metadata.Platform} · {duration} · {metadata.Uploader}";
            RefreshDownloadQuality();
            DownloadButton.IsEnabled = true;
            StatusText.Text = "Link consultado. Escolha o formato e a qualidade.";
        }
        catch (OperationCanceledException)
        {
            DownloadMediaTitle.Text = "Consulta cancelada";
            DownloadMediaDetails.Text = "Você pode consultar outro link.";
        }
        catch (Exception error)
        {
            inspectedMedia = null;
            DownloadMediaTitle.Text = "Não foi possível consultar o link";
            DownloadMediaDetails.Text = error.Message;
            StatusText.Text = error.Message;
        }
        finally
        {
            if (ReferenceEquals(analysisCancellation, cancellation))
                analysisCancellation = null;
            AnalyzeDownloadButton.IsEnabled = true;
            CancelAnalysisButton.Visibility = Visibility.Collapsed;
        }
    }

    private void CancelDownloadAnalysis(object sender, RoutedEventArgs e) => analysisCancellation?.Cancel();

    private void DownloadModeChanged(object sender, SelectionChangedEventArgs e)
    {
        if (mediaInspector is null)
            return;
        DownloadFormat.ItemsSource = DownloadMode.SelectedIndex == 1
            ? new[] { "MP3", "M4A", "WAV", "FLAC" } : new[] { "MP4", "MKV" };
        DownloadFormat.SelectedIndex = 0;
        RefreshDownloadQuality();
    }

    private void DownloadFormatChanged(object sender, SelectionChangedEventArgs e) => RefreshDownloadQuality();

    private void RefreshDownloadQuality()
    {
        if (mediaInspector is null)
            return;
        if (DownloadMode.SelectedIndex == 1)
        {
            var lossless = DownloadFormat.SelectedItem as string is "WAV" or "FLAC";
            DownloadQuality.ItemsSource = lossless
                ? new[] { new MediaQuality(0, "Sem perdas adicionais na conversão") }
                : new[] { 320, 256, 192, 128, 96 }.Select(bitrate => new MediaQuality(bitrate, $"{bitrate} kbps")).ToArray();
            DownloadQuality.SelectedIndex = lossless ? 0 : 2;
            DownloadQualityHint.Text = "A qualidade final também depende do áudio oferecido pela plataforma.";
        }
        else
        {
            var options = new List<MediaQuality> { new(0, "Melhor qualidade disponível") };
            if (inspectedMedia is not null)
                options.AddRange(inspectedMedia.Heights.Select(height => new MediaQuality(height, $"Até {height}p")));
            DownloadQuality.ItemsSource = options;
            DownloadQuality.SelectedIndex = 0;
            DownloadQualityHint.Text = inspectedMedia?.IsPlaylist == true
                ? "As opções vêm do primeiro item. Os demais usam a melhor qualidade até o limite escolhido."
                : "O limite vale para as resoluções oferecidas pelo vídeo.";
        }
    }

    private void ChooseDownloadDirectory(object sender, RoutedEventArgs e)
    {
        if (ChooseFolder() is { } folder)
            DownloadOutputDirectory.Text = folder;
    }

    private void QueueMediaDownload(object sender, RoutedEventArgs e)
    {
        if (inspectedMedia is null)
            return;
        try
        {
            var output = Path.GetFullPath(DownloadOutputDirectory.Text.Trim());
            if (File.Exists(output))
                throw new InvalidOperationException("Escolha uma pasta para salvar os downloads.");
            var audio = DownloadMode.SelectedIndex == 1;
            var quality = (DownloadQuality.SelectedItem as MediaQuality)?.Value ?? 0;
            queue.EnqueueDownload(new MediaDownloadRequest
            {
                Url = inspectedMedia.Url,
                Title = inspectedMedia.Title,
                Mode = audio ? "audio" : "video",
                Format = (DownloadFormat.SelectedItem as string ?? "MP4").ToLowerInvariant(),
                MaxHeight = audio ? 0 : quality,
                AudioBitrate = audio && quality > 0 ? quality : 192,
                IncludePlaylist = DownloadPlaylist.IsChecked == true,
                OutputDirectory = output
            });
            settings.DownloadDirectory = output;
            AppPaths.Save(AppPaths.PreferencesFile, settings);
            ShowHistory();
            StatusText.Text = "Download adicionado à fila.";
        }
        catch (Exception error) { StatusText.Text = error.Message; }
    }
}
