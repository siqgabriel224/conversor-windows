using System.Windows.Threading;

namespace Conversor;

internal sealed class WatchService : IDisposable
{
    private readonly DispatcherTimer timer = new() { Interval = TimeSpan.FromSeconds(2) };
    private readonly Dictionary<string, (long Size, long Modified, int Stable)> pending = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, string> known = new(StringComparer.OrdinalIgnoreCase);
    private readonly List<FileSystemWatcher> watchers = [];
    private readonly Preferences settings;
    private readonly Catalog catalog;
    private readonly ConversionQueue queue;
    internal WatchService(Preferences settings, Catalog catalog, ConversionQueue queue)
    {
        this.settings = settings;
        this.catalog = catalog;
        this.queue = queue;
        timer.Tick += (_, _) => Poll();
        Reload();
        timer.Start();
    }
    internal void Reload()
    {
        foreach (var watcher in watchers)
            watcher.Dispose();
        watchers.Clear();
        pending.Clear();
        foreach (var rule in settings.WatchRules.Where(r => r.Enabled && Directory.Exists(r.Folder)))
        {
            var watch = new FileSystemWatcher(rule.Folder) { IncludeSubdirectories = false, NotifyFilter = NotifyFilters.FileName | NotifyFilters.LastWrite | NotifyFilters.Size };
            void Changed(string path) => Application.Current.Dispatcher.BeginInvoke(() =>
            {
                if (!pending.ContainsKey(path))
                    pending[path] = (-1, -1, 0);
            });
            watch.Created += (_, e) => Changed(e.FullPath);
            watch.Changed += (_, e) => Changed(e.FullPath);
            watch.Renamed += (_, e) => Changed(e.FullPath);
            watch.Error += (_, _) => Diagnostics.Write("watch", "O monitoramento perdeu eventos; desative e reative a regra.");
            watch.EnableRaisingEvents = true;
            watchers.Add(watch);
        }
    }
    private void Poll()
    {
        foreach (var path in pending.Keys.ToArray())
        {
            try
            {
                var info = new FileInfo(path);
                if (!info.Exists)
                {
                    pending.Remove(path);
                    continue;
                }
                if ((info.Attributes & FileAttributes.Temporary) != 0 || path.EndsWith(".part", StringComparison.OrdinalIgnoreCase) || path.EndsWith(".tmp", StringComparison.OrdinalIgnoreCase))
                    continue;
                var stamp = $"{info.Length}:{info.LastWriteTimeUtc.Ticks}";
                if (known.GetValueOrDefault(path) == stamp)
                {
                    pending.Remove(path);
                    continue;
                }
                var previous = pending[path];
                var stable = previous.Size == info.Length && previous.Modified == info.LastWriteTimeUtc.Ticks ? previous.Stable + 1 : 0;
                pending[path] = (info.Length, info.LastWriteTimeUtc.Ticks, stable);
                if (stable < 3)
                    continue;
                using (var access = File.Open(path, FileMode.Open, FileAccess.Read, FileShare.Read))
                {
                }
                var rule = settings.WatchRules.FirstOrDefault(r => r.Enabled && Path.GetDirectoryName(path)!.Equals(r.Folder, StringComparison.OrdinalIgnoreCase));
                pending.Remove(path);
                known[path] = stamp;
                if (rule == null)
                    continue;
                if (!catalog.Options(path).Any(o => o.Id == rule.Target))
                {
                    Diagnostics.Write("watch", $"Formato de entrada incompatível com {rule.Target}: {Path.GetExtension(path)}");
                    continue;
                }
                queue.Enqueue([path], rule.Target, new Preferences { OutputDirectory = rule.Output, Quality = settings.Quality }, origin: "monitoramento");
            }
            catch (IOException) { }
            catch (UnauthorizedAccessException) { pending.Remove(path); }
        }
    }
    public void Dispose()
    {
        timer.Stop();
        foreach (var watcher in watchers)
            watcher.Dispose();
    }
}
