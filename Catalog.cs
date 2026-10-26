namespace Conversor;

internal sealed class Catalog
{
    internal static readonly Dictionary<string, string[]> Inputs = new()
    {
        ["imagem"] = ["png", "jpg", "jpeg", "webp", "bmp", "tif", "tiff", "gif", "heic"],
        ["pdf"] = ["pdf"],
        ["texto"] = ["doc", "docx", "odt", "rtf", "txt"],
        ["planilha"] = ["xls", "xlsx", "ods", "csv", "tsv"],
        ["slides"] = ["ppt", "pptx", "odp"],
        ["video"] = ["mp4", "mov", "mkv", "webm", "avi", "wmv"],
        ["audio"] = ["mp3", "wav", "flac", "aac", "m4a", "ogg", "opus"],
        ["livro"] = ["epub", "mobi", "azw3"],
        ["arquivo"] = ["zip", "7z", "rar", "tar", "gz"],
        ["fonte"] = ["ttf", "otf", "woff", "woff2"],
        ["cad"] = ["dxf", "dwg"]
    };
    private readonly Dictionary<string, string> engines = new();
    internal Catalog()
    {
        try
        {
            using var json = JsonDocument.Parse(File.ReadAllText(Path.Combine(AppPaths.Root, "engines.json")));
            foreach (var item in json.RootElement.EnumerateObject())
            {
                if (!item.Value.TryGetProperty("path", out var componentPath))
                    continue;
                var path = Path.GetFullPath(Path.Combine(AppPaths.Root, componentPath.GetString()!));
                if (File.Exists(path))
                    engines[item.Name] = path;
            }
        }
        catch (Exception e) { Diagnostics.Write("engines", e.Message); }
        var oda = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.ProgramFiles), "ODA");
        if (!engines.ContainsKey("oda") && Directory.Exists(oda))
        {
            var exe = Directory.EnumerateFiles(oda, "ODAFileConverter.exe", SearchOption.AllDirectories).FirstOrDefault();
            if (exe != null)
                engines["oda"] = exe;
        }
    }
    internal IReadOnlyDictionary<string, string> Engines => engines;
    internal string Engine(string id) => engines.TryGetValue(id, out var path) ? path : throw new InvalidOperationException($"Componente ausente: {id}. Execute a preparação dos motores.");
    internal static string Category(string path)
    {
        var ext = Path.GetExtension(path).TrimStart('.').ToLowerInvariant();
        return Inputs.FirstOrDefault(kv => kv.Value.Contains(ext)).Key ?? "outro";
    }
    internal List<ConversionOption> Options(string file)
    {
        var category = Category(file);
        var list = new List<ConversionOption>();
        void Add(string engine, params string[] targets)
        {
            if (!engines.ContainsKey(engine) || !engines.ContainsKey("python"))
                return;
            foreach (var target in targets)
                list.Add(new(target, target.ToUpperInvariant(), engine, category));
        }
        switch (category)
        {
            case "imagem":
                Add("magick", "png", "jpg", "webp", "bmp", "tiff", "gif", "pdf");
                break;
            case "pdf":
                Add("python", "png", "jpg", "pdf-split", "pdf-extract");
                Add("ghostscript", "pdf-compress");
                break;
            case "texto":
                Add("libreoffice", "pdf", "docx", "odt", "txt");
                break;
            case "planilha":
                Add("libreoffice", "pdf", "xlsx", "ods", "csv", "tsv");
                break;
            case "slides":
                Add("libreoffice", "pdf", "pptx", "odp");
                break;
            case "video":
                Add("ffmpeg", "mp4", "mov", "mkv", "webm", "mp3", "wav", "flac", "aac", "ogg");
                break;
            case "audio":
                Add("ffmpeg", "mp3", "wav", "flac", "aac", "ogg", "m4a");
                break;
            case "livro":
                Add("calibre", "epub", "mobi", "azw3", "pdf", "txt");
                break;
            case "arquivo":
                Add("sevenzip", "extract", "zip", "7z");
                break;
            case "fonte":
                Add("python", "woff", "woff2", "sfnt");
                break;
            case "cad":
                if (Path.GetExtension(file).Equals(".dxf", StringComparison.OrdinalIgnoreCase))
                    Add("python", "pdf", "svg", "png");
                if (engines.ContainsKey("oda"))
                    Add("oda", Path.GetExtension(file).Equals(".dwg", StringComparison.OrdinalIgnoreCase) ? "dxf" : "dwg");
                break;
        }
        if (engines.ContainsKey("sevenzip") && engines.ContainsKey("python") && File.Exists(file))
        {
            if (!list.Any(x => x.Id == "zip"))
                list.Add(new("zip", "ZIP", "sevenzip", category));
            if (!list.Any(x => x.Id == "7z"))
                list.Add(new("7z", "7Z", "sevenzip", category));
        }
        return list.Where(o => o.Id != Path.GetExtension(file).TrimStart('.').ToLowerInvariant()).Select(o => o with { Label = Labels.GetValueOrDefault(o.Id, o.Label) }).ToList();
    }
    internal List<ConversionOption> Common(string[] files)
    {
        if (files.Length == 0)
            return [];
        var first = Options(files[0]);
        return first.Where(o => files.Skip(1).All(f => Options(f).Any(t => t.Id == o.Id))).ToList();
    }
    internal static readonly Dictionary<string, string> Labels = new() { ["pdf-split"] = "Separar páginas", ["pdf-extract"] = "Extrair páginas", ["pdf-compress"] = "Comprimir PDF", ["pdf-merge"] = "Juntar PDFs", ["extract"] = "Extrair arquivos", ["sfnt"] = "Restaurar TTF / OTF" };
    internal string[] RingFormats(string[] files) => Common(files).Where(o => o.Id != "pdf-extract").Select(o => o.Id).ToArray();
}
