# Stage 1 — Phish (T1566.001)

**Lure:** `Year-End_Showcase_Invitation_v2.pdf` — a work-looking invitation with one RSVP
hyperlink. No macro, no embedded object; the entire payload of the PDF is a link.

**Link:** `http://192.168.254.100:8080/office_update.exe`

**Flow:**
1. User opens the PDF, clicks the RSVP link
2. `msedge.exe` downloads `office_update.exe` into `C:\Users\honey\Downloads`
   (SIEM: `msedge.exe` connection to `192.168.254.100:8080`, `destination.port: 8080`)
3. User double-clicks the file (Stage 2)

**Detection:** browser download from a plaintext-HTTP internal IP + a user running an
unsigned exe from `Downloads`. The phish itself is only provable by user interview; the
*execution* is provable in SIEM (see stage2).
