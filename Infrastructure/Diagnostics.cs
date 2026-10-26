namespace Conversor;

internal static class Diagnostics
{
    internal static readonly string DirectoryPath = Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Conversor");

    internal static void Write(string kind, string text)
    {
        try
        {
            Directory.CreateDirectory(DirectoryPath);
            var message = $"{DateTimeOffset.Now:O} [{kind}] {text}{Environment.NewLine}";
            File.AppendAllText(Path.Combine(DirectoryPath, "diagnostico.log"), message);
        }
        catch (IOException) { }
        catch (UnauthorizedAccessException) { }
    }
}
