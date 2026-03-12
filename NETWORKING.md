# Networking Setup

This document describes how the kitchen assistant inbox server is made accessible over Tailscale from other devices (phone, etc.).

## Overview

The Flask server runs inside WSL2. External devices connect via Tailscale. Because WSL2 is a VM with its own private IP, Windows must forward incoming traffic to WSL2 using `netsh portproxy`.

```
Phone/device → Tailscale → Windows (100.122.64.31) → portproxy → WSL2 (172.x.x.x) → Flask:8743
```

## Components

### Flask Server
- Runs inside WSL2 on port `8743`
- Started via: `nohup .venv/bin/python server.py > server.log 2>&1 &`
- Binds to `0.0.0.0` so it accepts connections forwarded from Windows

### Windows Portproxy
Forwards traffic arriving on Windows to WSL2's internal IP. WSL2's IP can change on reboot, so a startup script handles keeping this up to date.

Current rules (as of setup):
| Windows port | WSL2 port | Purpose |
|---|---|---|
| 22 | 22 | SSH |
| 8743 | 8743 | Kitchen assistant inbox server |

To view current rules:
```powershell
netsh interface portproxy show all
```

To manually update (replace IP with current WSL2 IP from `hostname -I`):
```powershell
netsh interface portproxy delete v4tov4 listenport=8743 listenaddress=0.0.0.0
netsh interface portproxy add v4tov4 listenport=8743 listenaddress=0.0.0.0 connectport=8743 connectaddress=<WSL2_IP>
```

### Windows Firewall
A firewall rule allows inbound traffic on port 8743:
```powershell
netsh advfirewall firewall add rule name="Kitchen Assistant" dir=in action=allow protocol=TCP localport=8743
```

Note: The rule is not IP-restricted. Security relies on the router not forwarding port 8743 from the internet, and Tailscale for remote access.

### Startup Script
`C:\Users\patri\Documents\update-wsl-portproxy.ps1`

Runs at logon via Task Scheduler. It:
1. Starts WSL2 (`wsl -d Ubuntu`)
2. Retries up to 12 times (10 second intervals, ~2 min max) waiting for WSL2 to be ready
3. Grabs WSL2's current IP and updates portproxy rules for ports 22 and 8743

The existing Task Scheduler task (previously just `wsl.exe -d Ubuntu`) was updated to run this script instead via:
- **Program:** `powershell.exe`
- **Arguments:** `-ExecutionPolicy Bypass -File "C:\Users\patri\Documents\update-wsl-portproxy.ps1"`

## Tailscale
- Tailscale runs on Windows (not inside WSL2)
- Windows Tailscale IP: `100.122.64.31`
- Tailscale hostname alias: `family-desktop`
- Access the inbox server at: `http://family-desktop:8743`

## Troubleshooting

**Can't reach the server from another device:**
1. Check Tailscale is connected on both devices
2. Check the server is running: `pgrep -f server.py`
3. Check it's listening: `ss -tlnp | grep 8743`
4. Check portproxy rules are correct in PowerShell: `netsh interface portproxy show all`
5. WSL2 IP may have changed — run the startup script manually in PowerShell as Administrator

**Server running but not responding:**
- Check `server.log` in the project directory for errors
- Restart: `kill $(pgrep -f server.py) && nohup .venv/bin/python server.py > server.log 2>&1 &`

**Portproxy points to wrong IP after reboot:**
- Get current WSL2 IP: `hostname -I`
- Run `C:\Users\patri\Documents\update-wsl-portproxy.ps1` in PowerShell as Administrator
