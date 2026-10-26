namespace Conversor;

internal sealed class MediaDownloadRequest
{
    public string Url { get; set; } = "";
    public string Title { get; set; } = "";
    public string Mode { get; set; } = "video";
    public string Format { get; set; } = "mp4";
    public int MaxHeight
    {
        get; set;
    }
    public int AudioBitrate { get; set; } = 192;
    public bool IncludePlaylist
    {
        get; set;
    }
    public string OutputDirectory { get; set; } = "";
}

internal sealed class MediaInspection
{
    public string Url { get; set; } = "";
    public string Title { get; set; } = "";
    public string Platform { get; set; } = "";
    public string Uploader { get; set; } = "";
    public double Duration
    {
        get; set;
    }
    public bool IsPlaylist
    {
        get; set;
    }
    public int PlaylistCount
    {
        get; set;
    }
    public int[] Heights { get; set; } = [];
}

internal sealed record MediaQuality(int Value, string Label)
{
    public override string ToString() => Label;
}
