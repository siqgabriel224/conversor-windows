using System.Collections.ObjectModel;
using System.Globalization;
using Microsoft.Win32;

namespace Conversor;

public partial class MainWindow
{
    private readonly ObservableCollection<string> resizeFiles = [];
    private CancellationTokenSource? resizePreviewCancellation;
    private ResizePreviewService? resizePreviewService;
    private static readonly string[] ResizeAnchors = ["northwest", "north", "northeast", "west", "center", "east", "southwest", "south", "southeast"];
    private sealed record SizePreset(string Label, int Width, int Height, string Ratio);
    private static readonly SizePreset[] ResizePresets =
    [
        new("TikTok / Shorts · 9:16 · 1080 × 1920", 1080, 1920, "9:16"),
        new("YouTube · 16:9 · 1920 × 1080", 1920, 1080, "16:9"),
        new("Quadrado · 1:1 · 1080 × 1080", 1080, 1080, "1:1"),
        new("Retrato · 4:5 · 1080 × 1350", 1080, 1350, "4:5"),
        new("Clássico · 4:3 · 1440 × 1080", 1440, 1080, "4:3")
    ];

    private void InitializeResize()
    {
        resizePreviewService = new ResizePreviewService(catalog);
        ResizeFiles.ItemsSource = resizeFiles;
        ResizePreset.ItemsSource = ResizePresets.Select(preset => preset.Label).Append("Personalizado").ToArray();
        ResizePreset.SelectedIndex = 0;
        ResizeFit.ItemsSource = new[] { "Preencher e recortar bordas", "Manter tudo com faixas pretas" };
        ResizeFit.SelectedIndex = 0;
        ResizeAnchor.ItemsSource = new[] { "Superior esquerda", "Superior centro", "Superior direita", "Centro esquerda", "Centro", "Centro direita", "Inferior esquerda", "Inferior centro", "Inferior direita" };
        ResizeAnchor.SelectedIndex = 4;
        ResizeImageFormat.ItemsSource = new[] { "PNG", "JPG", "WEBP" };
        ResizeImageFormat.SelectedIndex = 0;
        ResizeVideoFormat.ItemsSource = new[] { "MP4", "MKV", "WEBM" };
        ResizeVideoFormat.SelectedIndex = 0;
        ResizeOutput.Text = settings.OutputDirectory;
        resizeFiles.CollectionChanged += (_, _) => InvalidateResizePreview();
        Closed += (_, _) => resizePreviewCancellation?.Cancel();
    }

    private void AddResizePaths(IEnumerable<string> paths)
    {
        var rejected = 0;
        foreach (var path in paths)
        {
            if (!File.Exists(path) || !ResizeRequest.Supports(path))
            {
                rejected++;
                continue;
            }
            var full = Path.GetFullPath(path);
            if (!resizeFiles.Contains(full))
                resizeFiles.Add(full);
        }
        if (resizeFiles.Count > 0 && ResizeFiles.SelectedIndex < 0)
            ResizeFiles.SelectedIndex = 0;
        StatusText.Text = $"{resizeFiles.Count} arquivo(s) para redimensionar." + (rejected > 0 ? $" {rejected} item(ns) incompatível(is) ignorado(s)." : "");
    }

    private void AddResizeFiles(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog { Multiselect = true, Title = "Adicionar imagens e vídeos para redimensionar", Filter = "Imagens e vídeos|*.png;*.jpg;*.jpeg;*.webp;*.bmp;*.tif;*.tiff;*.heic;*.heif;*.avif;*.gif;*.mp4;*.mov;*.mkv;*.webm;*.avi;*.m4v;*.mpg;*.mpeg;*.mts;*.m2ts;*.ts|Todos os arquivos|*.*" };
        if (dialog.ShowDialog(this) == true)
            AddResizePaths(dialog.FileNames);
    }

    private void RemoveResizeFiles(object sender, RoutedEventArgs e)
    {
        foreach (var path in ResizeFiles.SelectedItems.Cast<string>().ToArray())
            resizeFiles.Remove(path);
    }

    private void UseConversionSelection(object sender, RoutedEventArgs e) => AddResizePaths(files);

    private void ResizePresetChanged(object sender, SelectionChangedEventArgs e)
    {
        if (ResizeWidth is null || ResizePreset.SelectedIndex is < 0 or > 4)
            return;
        var preset = ResizePresets[ResizePreset.SelectedIndex];
        ResizeWidth.Text = preset.Width.ToString();
        ResizeHeight.Text = preset.Height.ToString();
        ResizeRatio.Text = preset.Ratio;
    }

    private void ApplyResizeRatio(object sender, RoutedEventArgs e)
    {
        var parts = ResizeRatio.Text.Trim().Replace('/', ':').Split(':');
        if (parts.Length != 2 || !double.TryParse(parts[0].Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var a) ||
            !double.TryParse(parts[1].Replace(',', '.'), NumberStyles.Float, CultureInfo.InvariantCulture, out var b) ||
            !double.IsFinite(a) || !double.IsFinite(b) || a <= 0 || b <= 0 ||
            !int.TryParse(ResizeWidth.Text, out var width) || width is < 16 or > 7680)
        {
            StatusText.Text = "Digite uma proporção como 9:16, 16:9 ou 3:2 e uma largura válida.";
            return;
        }
        var height = width * b / a;
        if (!double.IsFinite(height) || height < 16 || height > 7680)
        {
            StatusText.Text = "A proporção gera uma altura fora do limite de 16 a 7680 pixels.";
            return;
        }
        ResizePreset.SelectedIndex = ResizePresets.Length;
        ResizeHeight.Text = ((int)Math.Round(height / 2, MidpointRounding.AwayFromZero) * 2).ToString();
        StatusText.Text = "Altura calculada pela largura; arredondada para número par, compatível com vídeos.";
    }

    private ResizeRequest ReadResizeRequest()
    {
        if (!int.TryParse(ResizeWidth.Text, out var width) || !int.TryParse(ResizeHeight.Text, out var height) ||
            width is < 16 or > 7680 || height is < 16 or > 7680 || (long)width * height > 33_177_600)
            throw new InvalidOperationException("Use medidas de 16 a 7680 pixels, com no máximo 33 milhões de pixels.");
        if (resizeFiles.Any(path => ResizeRequest.Videos.Contains(Path.GetExtension(path))) && (width % 2 != 0 || height % 2 != 0))
            throw new InvalidOperationException("Para vídeos, largura e altura precisam ser números pares.");
        return new ResizeRequest
        {
            Width = width,
            Height = height,
            Mode = ResizeFit.SelectedIndex == 1 ? "contain" : "cover",
            Anchor = ResizeAnchors[Math.Max(0, ResizeAnchor.SelectedIndex)],
            ImageFormat = (ResizeImageFormat.SelectedItem as string ?? "PNG").ToLowerInvariant(),
            VideoFormat = (ResizeVideoFormat.SelectedItem as string ?? "MP4").ToLowerInvariant()
        };
    }

    private void ResizeOptionChanged(object sender, RoutedEventArgs e) => InvalidateResizePreview();
    private void ResizeSelectionChanged(object sender, SelectionChangedEventArgs e) => InvalidateResizePreview();
    private void InvalidateResizePreview()
    {
        resizePreviewCancellation?.Cancel();
        if (ResizePreview is null)
            return;
        ResizePreview.Source = null;
        ResizePreviewInfo.Text = "Selecione um arquivo e clique em Atualizar prévia. Vídeos mostram o primeiro quadro; GIF/TIFF usam a primeira imagem.";
    }

    private async void PreviewResize(object sender, RoutedEventArgs e)
    {
        if (ResizeFiles.SelectedItem is not string source)
        {
            StatusText.Text = "Selecione um arquivo para visualizar.";
            return;
        }
        resizePreviewCancellation?.Cancel();
        using var cancellation = new CancellationTokenSource();
        resizePreviewCancellation = cancellation;
        PreviewResizeButton.IsEnabled = false;
        try
        {
            var request = ReadResizeRequest();
            ResizePreviewInfo.Text = "Gerando prévia do enquadramento…";
            ResizePreview.Source = await resizePreviewService!.CreateAsync(source, request, cancellation.Token);
            ResizePreviewInfo.Text = $"{Path.GetFileName(source)} · saída {request.Width} × {request.Height} px. A prévia representa o enquadramento; o vídeo mantém toda a duração.";
        }
        catch (OperationCanceledException) { }
        catch (Exception error) { if (!cancellation.IsCancellationRequested) ResizePreviewInfo.Text = error.Message; }
        finally
        {
            if (ReferenceEquals(resizePreviewCancellation, cancellation))
            {
                resizePreviewCancellation = null;
                PreviewResizeButton.IsEnabled = true;
            }

        }
    }

    private void ChooseResizeDirectory(object sender, RoutedEventArgs e)
    {
        if (ChooseFolder() is { } folder)
            ResizeOutput.Text = folder;
    }

    private void QueueResize(object sender, RoutedEventArgs e)
    {
        try
        {
            if (resizeFiles.Count == 0)
                throw new InvalidOperationException("Adicione imagens ou vídeos para redimensionar.");
            var request = ReadResizeRequest();
            var output = string.IsNullOrWhiteSpace(ResizeOutput.Text) ? "" : Path.GetFullPath(ResizeOutput.Text.Trim());
            if (File.Exists(output))
                throw new InvalidOperationException("Escolha uma pasta válida para salvar as cópias.");
            queue.EnqueueResize(resizeFiles.ToArray(), request, output, settings.Quality);
            ShowHistory();
            StatusText.Text = $"{resizeFiles.Count} redimensionamento(s) adicionado(s) à fila.";
        }
        catch (Exception error) { StatusText.Text = error.Message; }
    }
}
