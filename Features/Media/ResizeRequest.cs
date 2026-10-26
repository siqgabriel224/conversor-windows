namespace Conversor;

internal sealed record ResizeRequest
{
    public int Width { get; init; } = 1080;
    public int Height { get; init; } = 1920;
    public string Mode { get; init; } = "cover";
    public string Anchor { get; init; } = "center";
    public string ImageFormat { get; init; } = "png";
    public string VideoFormat { get; init; } = "mp4";

    internal static readonly HashSet<string> Images = new(StringComparer.OrdinalIgnoreCase)
        { ".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tif", ".tiff", ".heic", ".heif", ".avif", ".gif" };
    internal static readonly HashSet<string> Videos = new(StringComparer.OrdinalIgnoreCase)
        { ".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v", ".mpg", ".mpeg", ".mts", ".m2ts", ".ts" };
    internal static bool Supports(string path) => Images.Contains(Path.GetExtension(path)) || Videos.Contains(Path.GetExtension(path));
}
