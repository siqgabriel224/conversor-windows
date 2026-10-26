using System.Runtime.InteropServices;
using System.Diagnostics;

namespace Conversor;
// Closing this Windows job also terminates conversion-engine grandchildren.
internal sealed class ProcessScope : IDisposable
{
    private IntPtr handle;
    [StructLayout(LayoutKind.Sequential)]
    private struct Basic
    {
        public long PerProcess, PerJob; public uint Flags; public UIntPtr Min, Max; public uint Processes; public UIntPtr Affinity; public uint Priority, Scheduling;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct Io
    {
        public ulong ReadOps, WriteOps, OtherOps, ReadBytes, WriteBytes, OtherBytes;
    }
    [StructLayout(LayoutKind.Sequential)]
    private struct Extended
    {
        public Basic Basic; public Io Io; public UIntPtr ProcessMemory, JobMemory, PeakProcess, PeakJob;
    }
    [DllImport("kernel32.dll", SetLastError = true)] private static extern IntPtr CreateJobObject(IntPtr attributes, string? name);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool SetInformationJobObject(IntPtr job, int info, ref Extended limits, uint length);
    [DllImport("kernel32.dll", SetLastError = true)] private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    internal ProcessScope(Process process)
    {
        handle = CreateJobObject(IntPtr.Zero, null);
        var limits = new Extended { Basic = new Basic { Flags = 0x2000 } };
        if (handle == IntPtr.Zero || !SetInformationJobObject(handle, 9, ref limits, (uint)Marshal.SizeOf<Extended>()) || !AssignProcessToJobObject(handle, process.Handle))
        {
            Diagnostics.Write("job", "Falha ao isolar os processos de conversão");
            Dispose();
        }
    }
    public void Dispose()
    {
        if (handle != IntPtr.Zero)
        {
            CloseHandle(handle);
            handle = IntPtr.Zero;
        }
    }
}
