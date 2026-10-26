namespace Conversor;

internal sealed class Preferences
{
    public string OutputDirectory { get; set; } = "";
    public int Quality { get; set; } = 85;
    public bool StartWithWindows { get; set; } = true;
    public bool GestureEnabled { get; set; } = true;
    public string Modifier { get; set; } = "Ctrl";
    public List<WatchRule> WatchRules { get; set; } = [];
    public string DownloadDirectory { get; set; } = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.UserProfile), "Downloads", "Conversor");
}
internal sealed class WatchRule
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string Folder { get; set; } = "";
    public string Output { get; set; } = "";
    public string Target { get; set; } = "pdf";
    public bool Enabled { get; set; } = true;
}
