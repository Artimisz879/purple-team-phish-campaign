# Stage 3 — Privilege Escalation (T1548 / T1055)

The beacon initially ran as `honey` at **Medium** integrity — `honey` is a *filtered* local
admin (in `BUILTIN\Administrators` "deny only"), so it couldn't write `HKLM` or plant
SYSTEM persistence.

**Path taken:**
1. From the meterpreter shell:
   ```
   powershell -nop -c "Start-Process C:\Users\honey\Downloads\office_update.exe -Verb RunAs"
   ```
2. `-Verb RunAs` triggers the **UAC prompt** on the victim screen — a human clicks **Yes**
   (in the lab, that's the operator; in a real attack it's the social-engineering moment).
3. Second beacon spawns at **High** integrity → dials `:4443` → new session.
4. `migrate` into a SYSTEM `svchost.exe` (PPID 736 = `services.exe`) → `getuid` =
   `NT AUTHORITY\SYSTEM`.

**Proof in SIEM:**
- PS 4104 scriptblock: `Start-Process C:\Users\honey\Downloads\office_update.exe -Verb RunAs`
  (KQL: `powershell.file.script_block_text: "Verb RunAs"`)
- `whoami /all` output: `Mandatory Label\Medium Mandatory Level` → `High` → `SYSTEM`
- Process tree: `svchost.exe(16352, SYSTEM) → cmd.exe(10264, SYSTEM) → [all stage 4 tools]`

**Note:** a classic exploit (e.g. a named-pipe/EFSRPC potato) was attempted first and flaked
on this build; the UAC route succeeded. UAC "Yes" is a legitimate privesc vector — the
prompt is the human weakness.
