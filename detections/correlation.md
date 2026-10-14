# Correlation Rules — closing the detection gap

**The honest finding of the lab:** nothing was hidden. Every stage was logged. What the
attacker *did* do was **separate the ports** (8080 serve / 4443 C2 / 4444 data) so that no
single event looks like the whole picture. The fix is therefore **correlation**, not hunting
for a hidden artifact.

These EQL sequences tie the individual events into an alert. Adapt `host.name`, the attacker
IP, and the ports to your environment.

---

## 1. Implant download → C2 callback (execute chain)

A process pulls a file from an internal HTTP port, then shortly after a disguised binary
connects out to the same host on the C2 port.

```
sequence by host.id
[
  process where host.name == "honeypot"
    and user.name == "NT AUTHORITY\\SYSTEM"
    and process.name == "powershell.exe"
    and process.command_line like* "%DownloadFile%192.168.254.100%"
]
[
  network where host.name == "honeypot"
    and process.name == "office_update.exe"
    and destination.ip == "192.168.254.100"
    and destination.port == 4443
    and network.direction == "egress"
]
within 1h
```

---

## 2. Persistence planted → later auto-start (the "it comes back" chain)

Task-scheduler tooling + Run-key registry write by SYSTEM, then the hidden implant
executes again **without any user in the parent chain** (i.e. after a reboot/login).

```
sequence by host.id
[
  registry where host.name == "honeypot"
    and user.name == "NT AUTHORITY\\SYSTEM"
    and (registry.key like* "%Schedule\\TaskCache%" or registry.key like* "%CurrentVersion\\Run%")
    and registry.value == "WinUpdateSvc"
]
[
  process where host.name == "honeypot"
    and process.name == "wu_service.exe"
    and process.parent.name != "cmd.exe"
]
within 24h
```

> `process.parent.name != "cmd.exe"` is the trick: during the live attack the implant is
> launched from our shell (`cmd.exe`); after a reboot it's launched by
> `services.exe`/`svchost.exe`. The *same binary with a different parent* = persistence fired.

---

## 3. PowerShell Web-Client upload (exfil)

Signed-system-tool PowerShell using `Net.WebClient` to upload, followed by network egress
to the attacker IP on the **non-C2** port.

```
sequence by host.id
[
  process where host.name == "honeypot"
    and process.name == "powershell.exe"
    and process.command_line like* "%UploadFile%"
]
[
  network where host.name == "honeypot"
    and destination.ip == "192.168.254.100"
    and destination.port == 4444
    and network.direction == "egress"
]
within 5m
```

---

## 4. Generic: unsigned "office"-named binary phoning home (the meta-rule)

This is the rule that would have caught the beacon *without knowing the name ahead of time*:

```
sequence by host.id
[
  process where host.os.type == "windows"
    and process.code_signature.exists == false
    and process.name like* "%office%"
    and process.executable like* "\\Downloads\\"
]
[
  network where network.direction == "egress"
    and destination.port in (4443, 4444, 1337, 444)
]
within 10m
```

Four independent flags — **unsigned**, **office-named**, **runs from Downloads**, **egress
to a classic C2 port** — is a near-zero-false-positive detection.

---

## What was NOT caught (and why)

| Gap | Reason | Fix |
|---|---|---|
| Task Scheduler Operational EID **402** (task created) | Channel not in the log intake for the honeypot | Add `Microsoft-Windows-TaskScheduler/Operational` to the intake; the endpoint agent already covered it via TaskCache registry writes |
| Native "process created" (Security EID 4688) command detail | Intake shipped the event without full command line in some datasets | Enable `process_command_line` auditing (Group Policy) if not already on |
| Single-event exfil | `UploadFile` alone looks like normal PowerShell | The sequence above (process → network to same IP) closes it |

## The one-line takeaway

> **Separation of ports doesn't hide an attack — it just splits it across events.**
> A SOC that correlates process + network + registry per host catches it in minutes.
> The purple-team win is that the *rules now exist*.
