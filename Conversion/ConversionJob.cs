using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace Conversor;

internal sealed record ConversionOption(string Id, string Label, string Engine, string Category)
{
    public override string ToString() => Label;
}
internal sealed class ConversionJob : INotifyPropertyChanged
{
    public string Id { get; set; } = Guid.NewGuid().ToString("N");
    public string[] Inputs { get; set; } = [];
    public string Target { get; set; } = "";
    public string Label { get; set; } = "";
    public string OutputDirectory { get; set; } = "";
    public int Quality { get; set; } = 85;
    public string Pages { get; set; } = "";
    public int Width
    {
        get; set;
    }
    public string Origin { get; set; } = "janela";
    public DateTimeOffset Created { get; set; } = DateTimeOffset.Now;
    public MediaDownloadRequest? Download
    {
        get; set;
    }
    public ResizeRequest? Resize
    {
        get; set;
    }
    public string Name => Download is not null
        ? (string.IsNullOrWhiteSpace(Download.Title) ? Download.Url : Download.Title)
        : Inputs.Length == 1 ? Path.GetFileName(Inputs[0]) : $"{Inputs.Length} arquivos";
    private string state = "Na fila", detail = "Aguardando processamento";
    private double progress;
    public string State
    {
        get => state; set
        {
            state = value;
            Changed();
            Changed(nameof(IsBusy));
        }
    }
    public string Detail
    {
        get => detail; set
        {
            detail = value;
            Changed();
        }
    }
    public double Progress
    {
        get => progress; set
        {
            progress = value;
            Changed();
        }
    }
    public string[] Outputs { get; set; } = [];
    [System.Text.Json.Serialization.JsonIgnore] public bool IsBusy => State is "Na fila" or "Convertendo" or "Baixando";
    [System.Text.Json.Serialization.JsonIgnore] public CancellationTokenSource Cancellation { get; } = new();
    public event PropertyChangedEventHandler? PropertyChanged;
    private void Changed([CallerMemberName] string? name = null) => PropertyChanged?.Invoke(this, new(name));
}
