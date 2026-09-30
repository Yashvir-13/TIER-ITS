---
name: wsl2-service-setup
description: Set up a Linux service (systemd) inside WSL2 with mirrored networking. Use when installing Ollama, a database, a dev server, or any daemon that binds a port inside WSL2.
---

# WSL2 Service Setup

## Before you bind a port

With `networkingMode=mirrored`, Windows and WSL2 share the port namespace. A Windows process on port N blocks WSL2 from binding to the same port — and `ss`/`lsof` inside WSL2 cannot see the Windows process.

1. **Check Windows side first:** `netstat.exe -ano | findstr.exe "<PORT>"`.
2. **Kill or relocate** the conflicting Windows process before starting the WSL2 service.
3. **Bind to `127.0.0.1`, not `0.0.0.0`** unless cross-host access is explicitly needed. `0.0.0.0` with mirrored networking causes phantom port conflicts.

## Systemd service checklist

1. Verify `systemd=true` in `/etc/wsl.conf` under `[boot]`.
2. Create the service (or let the installer do it).
3. Create a drop-in override at `/etc/systemd/system/<service>.service.d/environment.conf` for env vars. Never edit the main service file directly — the installer will overwrite it.
4. `sudo systemctl daemon-reload && sudo systemctl enable <service> && sudo systemctl restart <service>`.
5. Verify: `sudo systemctl status <service> --no-pager`, then `curl` the endpoint.

## If it fails to start

Read the actual error first — do not guess:

```bash
sudo journalctl -u <service> --no-pager -n 20
```

Common WSL2 causes:

- **"address already in use"** → Windows ghost process holding the port. Diagnose with `netstat.exe -ano | findstr.exe "<PORT>"`. Kill with `taskkill.exe /F /PID <pid>`. The process is often `svchost.exe` hosting a leftover Windows service.
- **"permission denied" on data dir** → The service user can't write to its home. Fix: `sudo mkdir -p <dir> && sudo chown -R <user>:<group> <dir>`.
- **"connection refused" on localhost** → IPv6 resolution issue. `localhost` may resolve to `::1` before `127.0.0.1`. Always use `127.0.0.1` explicitly in `curl` and application config.
- **curl hangs (no response, no error)** → Same IPv6 issue. Use `curl --max-time 5 http://127.0.0.1:<PORT>/`.

## sudo rule

Commands requiring `sudo` cannot run in agent background tasks — the agent has no way to enter the password. Present them as **copy-paste blocks** for the user to run in their own terminal. Group related sudo commands into a single block so the user only authenticates once.
