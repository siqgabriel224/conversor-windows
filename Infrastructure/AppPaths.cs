namespace Conversor;

internal static class AppPaths
{
    public static string Root { get; } = FindRoot();
    public static string Data { get; } = Diagnostics.DirectoryPath;
    public static string PreferencesFile => Path.Combine(Data, "configuracoes.json");
    public static string HistoryFile => Path.Combine(Data, "historico.json");
    private static string FindRoot()
    {
        for (var directory = new DirectoryInfo(AppContext.BaseDirectory); directory != null; directory = directory.Parent)
        {
            if (File.Exists(Path.Combine(directory.FullName, "engines.json")) &&
                Directory.Exists(Path.Combine(directory.FullName, "engines")))
                return directory.FullName;
        }
        return AppContext.BaseDirectory;
    }
    public static T Read<T>(string path, Func<T> fallback)
    {
        try
        {
            return JsonSerializer.Deserialize<T>(File.ReadAllText(path)) ?? fallback();
        }
        catch { return fallback(); }
    }
    public static void Save<T>(string path, T data)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(path)!);
        var temp = path + ".tmp";
        File.WriteAllText(temp, JsonSerializer.Serialize(data, new JsonSerializerOptions { WriteIndented = true }));
        File.Move(temp, path, true);
    }
}
