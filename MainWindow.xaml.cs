using System.Collections.ObjectModel;
using System.Diagnostics;
using Microsoft.Win32;

namespace Conversor;

public partial class MainWindow : Window
{
    private readonly ObservableCollection<string> files = [];
    private readonly Catalog catalog;
    private readonly ConversionQueue queue;
    private readonly Preferences settings;
    private readonly Action settingsChanged;
    private static readonly (string Title, string Subtitle)[] NavigationPages =
    [
        ("Converter arquivos", "Arraste, escolha o formato e pronto. Os originais ficam preservados."),
        ("Histórico e fila", "Acompanhe cada arquivo e abra os resultados."),
        ("Automações", "Converta novos arquivos automaticamente, enquanto o Conversor estiver aberto."),
        ("Configurações", "Ajuste o Conversor para o seu dia a dia."),
        ("Baixar vídeos", "Vídeo, áudio e playlists de YouTube, Instagram e TikTok."),
        ("Redimensionar", "Imagens e vídeos no tamanho certo. A duração e os originais ficam preservados.")
    ];
    internal MainWindow(Catalog catalog, ConversionQueue queue, Preferences settings, Action settingsChanged)
    {
        this.catalog = catalog;
        this.queue = queue;
        this.settings = settings;
        this.settingsChanged = settingsChanged;
        InitializeComponent();
        InputFiles.ItemsSource = files;
        JobList.ItemsSource = queue.Jobs;
        OutputDirectory.Text = settings.OutputDirectory;
        Quality.Value = settings.Quality;
        AutoStart.IsChecked = settings.StartWithWindows;
        EnableGesture.IsChecked = settings.GestureEnabled;
        ModifierKey.ItemsSource = new[] { "Ctrl", "Alt", "Shift" };
        ModifierKey.SelectedItem = settings.Modifier;
        WatchTarget.ItemsSource = new[] { "pdf", "png", "jpg", "webp", "mp3", "mp4", "epub", "zip", "7z", "woff2" };
        WatchTarget.SelectedIndex = 0;
        var componentIds = new[]
        {
            "magick", "ffmpeg", "libreoffice", "ghostscript", "python", "sevenzip",
            "pandoc", "calibre", "oda", "ytdlp", "deno"
        };
        EngineStatus.Text = string.Join("\n", componentIds.Select(id =>
            $"{(catalog.Engines.ContainsKey(id) ? "● Disponível" : "○ Ausente")}  ·  {id}"));
        files.CollectionChanged += (_, _) => RefreshFormats();
        RefreshWatches();
        RefreshFormats();
        InitializeDownloads();
        InitializeResize();
        queue.Finished += job => { RecentSummary.Text = $"{job.Name} · {job.State}"; StatusText.Text = RecentSummary.Text; };
    }
    private void RefreshFormats()
    {
        var target = (TargetFormat.SelectedItem as ConversionOption)?.Id;
        TargetFormat.ItemsSource = catalog.Common(files.ToArray());
        TargetFormat.SelectedValue = target;
        if (TargetFormat.SelectedIndex < 0 && TargetFormat.Items.Count > 0)
            TargetFormat.SelectedIndex = 0;
        SelectionInfo.Text = $"{files.Count} arquivo(s) · os formatos exibidos servem para toda a seleção";
        ConvertButton.IsEnabled = files.Count > 0 && TargetFormat.Items.Count > 0;
    }
    internal void AddPaths(IEnumerable<string> paths)
    {
        foreach (var path in paths)
        {
            if (File.Exists(path) && !files.Contains(Path.GetFullPath(path)))
                files.Add(Path.GetFullPath(path));
        }
        Pages.SelectedIndex = 0;
    }
    private void Files_DragOver(object sender, DragEventArgs e)
    {
        e.Effects = e.Data.GetDataPresent(DataFormats.FileDrop) ? DragDropEffects.Copy : DragDropEffects.None;
        e.Handled = true;
    }
    private void Files_Drop(object sender, DragEventArgs e)
    {
        if (e.Data.GetDataPresent(DataFormats.FileDrop))
        {
            var dropped = (string[])e.Data.GetData(DataFormats.FileDrop);
            if (Pages.SelectedIndex == 5)
                AddResizePaths(dropped);
            else
                AddPaths(dropped);
        }
        e.Handled = true;
    }
    private void AddFiles(object sender, RoutedEventArgs e)
    {
        var dialog = new OpenFileDialog { Multiselect = true, Title = "Adicionar arquivos para converter" };
        if (dialog.ShowDialog(this) == true)
            AddPaths(dialog.FileNames);
    }
    private void RemoveFile(object sender, RoutedEventArgs e)
    {
        foreach (var path in InputFiles.SelectedItems.Cast<string>().ToArray())
            files.Remove(path);
    }
    private void ClearFiles(object sender, RoutedEventArgs e) => files.Clear();
    private void MoveUp(object sender, RoutedEventArgs e)
    {
        var i = InputFiles.SelectedIndex;
        if (i > 0)
        {
            files.Move(i, i - 1);
            InputFiles.SelectedIndex = i - 1;
        }
    }
    private void MoveDown(object sender, RoutedEventArgs e)
    {
        var i = InputFiles.SelectedIndex;
        if (i >= 0 && i < files.Count - 1)
        {
            files.Move(i, i + 1);
            InputFiles.SelectedIndex = i + 1;
        }
    }
    private void ConvertFiles(object sender, RoutedEventArgs e)
    {
        if (TargetFormat.SelectedItem is ConversionOption option)
            QueueSelection(option.Id);
    }
    private void MergePdf(object sender, RoutedEventArgs e)
    {
        if (files.Count < 2 || files.Any(f => !Path.GetExtension(f).Equals(".pdf", StringComparison.OrdinalIgnoreCase)))
        {
            StatusText.Text = "Adicione pelo menos dois PDFs. Use ↑ e ↓ para escolher a ordem.";
            return;
        }
        QueueSelection("pdf-merge");
    }
    private void QueueSelection(string target)
    {
        if (!int.TryParse(ImageWidth.Text, out var width) || width < 0 || width > 16000)
        {
            StatusText.Text = "Largura inválida. Use 0 para manter o tamanho ou um valor até 16000.";
            return;
        }
        queue.Enqueue(files.ToArray(), target, settings, PdfPages.Text, width);
        ShowHistory();
        StatusText.Text = "Conversões adicionadas à fila";
    }
    internal void ShowHistory()
    {
        Pages.SelectedIndex = 1;
        PageTitle.Text = "Histórico e fila";
        PageSubtitle.Text = "Acompanhe cada arquivo e abra os resultados.";
        Show();
        WindowState = WindowState.Normal;
        Activate();
    }
    private void Navigate(object sender, RoutedEventArgs e)
    {
        Pages.SelectedIndex = int.Parse((string)((Button)sender).Tag);
        var page = NavigationPages[Pages.SelectedIndex];
        PageTitle.Text = page.Title;
        PageSubtitle.Text = page.Subtitle;
    }
    private void OpenResult(object sender, RoutedEventArgs e)
    {
        if (JobList.SelectedItem is ConversionJob job && job.Outputs.Length > 0)
            Open(job.Outputs[0]);
    }
    private void OpenFolder(object sender, RoutedEventArgs e)
    {
        if (JobList.SelectedItem is ConversionJob job && job.Outputs.Length > 0)
        {
            var output = job.Outputs[0];
            Open(Directory.Exists(output) ? output : Path.GetDirectoryName(output)!);
        }
    }
    internal static void Open(string path)
    {
        try
        {
            Process.Start(new ProcessStartInfo(path) { UseShellExecute = true });
        }
        catch (Exception e) { MessageBox.Show(e.Message, "Conversor"); }
    }
    private void CancelSelected(object sender, RoutedEventArgs e)
    {
        if (JobList.SelectedItem is ConversionJob job && job.IsBusy)
            job.Cancellation.Cancel();
    }
    private void ClearHistory(object sender, RoutedEventArgs e) => queue.ClearCompleted();
    private string? ChooseFolder()
    {
        var dialog = new OpenFolderDialog { Title = "Escolher pasta" };
        return dialog.ShowDialog(this) == true ? dialog.FolderName : null;
    }
    private void ChooseOutput(object sender, RoutedEventArgs e)
    {
        var folder = ChooseFolder();
        if (folder != null)
            OutputDirectory.Text = folder;
    }
    private void ChooseWatchInput(object sender, RoutedEventArgs e)
    {
        var folder = ChooseFolder();
        if (folder != null)
            WatchInput.Text = folder;
    }
    private void ChooseWatchOutput(object sender, RoutedEventArgs e)
    {
        var folder = ChooseFolder();
        if (folder != null)
            WatchOutput.Text = folder;
    }
    private void SaveSettings(object sender, RoutedEventArgs e)
    {
        try
        {
            if (OutputDirectory.Text.Length > 0 && !Directory.Exists(OutputDirectory.Text))
                throw new InvalidOperationException("Escolha uma pasta de saída existente.");
            settings.OutputDirectory = OutputDirectory.Text.Trim();
            settings.Quality = (int)Quality.Value;
            settings.StartWithWindows = AutoStart.IsChecked == true;
            settings.GestureEnabled = EnableGesture.IsChecked == true;
            settings.Modifier = ModifierKey.SelectedItem as string ?? "Ctrl";
            AppPaths.Save(AppPaths.PreferencesFile, settings);
            settingsChanged();
            StatusText.Text = "Preferências salvas";
        }
        catch (Exception error) { StatusText.Text = error.Message; }
    }
    private void RefreshWatches() => WatchList.ItemsSource = settings.WatchRules.Select(r => $"{r.Folder}  →  {r.Target.ToUpperInvariant()}  →  {r.Output}").ToArray();
    private void AddWatch(object sender, RoutedEventArgs e)
    {
        try
        {
            var input = Path.GetFullPath(WatchInput.Text);
            var output = Path.GetFullPath(WatchOutput.Text);
            if (!Directory.Exists(input) || !Directory.Exists(output))
                throw new InvalidOperationException("Escolha pastas de entrada e saída existentes.");
            if (IsWithinFolder(output, input) || settings.WatchRules.Any(rule =>
                IsWithinFolder(output, rule.Folder) || IsWithinFolder(rule.Output, input)))
                throw new InvalidOperationException("A saída precisa ficar fora de todas as pastas monitoradas para evitar ciclos.");
            if (settings.WatchRules.Any(r => r.Folder.Equals(input, StringComparison.OrdinalIgnoreCase)))
                throw new InvalidOperationException("Essa pasta já está sendo monitorada.");
            settings.WatchRules.Add(new()
            {
                Folder = input,
                Output = output,
                Target = WatchTarget.SelectedItem as string ?? "pdf"
            });
            AppPaths.Save(AppPaths.PreferencesFile, settings);
            RefreshWatches();
            settingsChanged();
            StatusText.Text = "Monitoramento ativo para novos arquivos";
        }
        catch (Exception error) { StatusText.Text = error.Message; }
    }
    private void RemoveWatch(object sender, RoutedEventArgs e)
    {
        var i = WatchList.SelectedIndex;
        if (i < 0)
            return;
        settings.WatchRules.RemoveAt(i);
        AppPaths.Save(AppPaths.PreferencesFile, settings);
        RefreshWatches();
        settingsChanged();
    }

    private static bool IsWithinFolder(string child, string parent)
    {
        var folder = parent.TrimEnd('\\');
        return child.TrimEnd('\\').Equals(folder, StringComparison.OrdinalIgnoreCase)
            || child.StartsWith(folder + '\\', StringComparison.OrdinalIgnoreCase);
    }
}
