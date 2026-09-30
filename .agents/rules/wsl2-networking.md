# WSL2 Mirrored Networking

This project runs inside WSL2 with `networkingMode=mirrored`.

- **Bind to `127.0.0.1`, never `0.0.0.0`**, for any service (Ollama, dev servers, databases). With mirrored networking, `0.0.0.0` causes port conflicts with Windows processes.
- **Before binding a port**, check the Windows side: `netstat.exe -ano | findstr.exe "<PORT>"`.
- **`ss`/`lsof` cannot see Windows processes.** If a port appears "free" in WSL2 but binding fails, the conflict is on the Windows side.
- **IPv6 can cause hangs.** If `curl http://localhost:<PORT>/` hangs but `curl http://127.0.0.1:<PORT>/` works, it's an IPv6 resolution issue. Always use `127.0.0.1` explicitly.
