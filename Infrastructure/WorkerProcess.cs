using System.Diagnostics;
using System.Text;

namespace Conversor;

internal static class WorkerProcess
{
    internal static ProcessStartInfo CreateStartInfo(Catalog catalog, string script)
    {
        var start = new ProcessStartInfo(catalog.Engine("python"))
        {
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardInput = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true,
            StandardInputEncoding = new UTF8Encoding(false),
            StandardOutputEncoding = Encoding.UTF8,
            StandardErrorEncoding = Encoding.UTF8
        };
        start.ArgumentList.Add("-u");
        start.ArgumentList.Add(Path.Combine(AppPaths.Root, "worker", script));
        start.Environment["PYTHONIOENCODING"] = "utf-8";
        start.Environment["DENO_DIR"] = Path.Combine(AppPaths.Data, "deno-cache");
        start.Environment["DENO_NO_UPDATE_CHECK"] = "1";
        return start;
    }
}
