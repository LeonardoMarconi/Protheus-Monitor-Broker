import http.server
import urllib.request
import urllib.parse
import ssl
import json
import re
import os
import mimetypes

PROXY_PORT = [Defina a porta do Proxy aqui]

# Pasta onde este script está + nome do arquivo HTML a servir na raiz
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_FILE = os.path.join(BASE_DIR, "broker_userinfo.html")

# Só permite repassar para IPs de rede privada (RFC1918) — trava básica de segurança
ALLOWED_HOST_RE = re.compile(
    r"^(10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"localhost)$"
)

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def _send_json(self, status, payload_bytes):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(payload_bytes)

    def _send_file(self, filepath):
        if not os.path.isfile(filepath):
            self.send_response(404)
            self._set_cors_headers()
            self.end_headers()
            self.wfile.write(b"Arquivo nao encontrado: " + filepath.encode("utf-8"))
            return
        ctype = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
        with open(filepath, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self._set_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = urllib.parse.parse_qs(parsed.query)

        # --- Rotas de API do broker ---
        route_map = {"/userinfo": "totvs_broker_query/userinfo", "/brokerinfo": "totvs_broker_query"}
        if path in route_map:
            target_param = qs.get("target", [None])[0]
            if not target_param:
                self._send_json(400, b'{"error":"parametro target ausente, ex: ?target=IP:PORTA"}')
                return
            host_part = target_param.split(":")[0]
            if not ALLOWED_HOST_RE.match(host_part):
                self._send_json(403, b'{"error":"host nao permitido, apenas IPs de rede privada"}')
                return
            broker_url = f"https://{target_param}/{route_map[path]}"
            try:
                req = urllib.request.Request(broker_url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                    data = resp.read()
                self._send_json(200, data)
            except Exception as e:
                self._send_json(502, json.dumps({"error": str(e), "target": broker_url}).encode("utf-8"))
            return

        # --- Serve a própria página do painel ---
        if path == "" or path == "/index.html":
            self._send_file(HTML_FILE)
            return

        # --- Qualquer outro arquivo estático na mesma pasta (opcional) ---
        safe_path = os.path.normpath(os.path.join(BASE_DIR, path.lstrip("/")))
        if safe_path.startswith(BASE_DIR) and os.path.isfile(safe_path):
            self._send_file(safe_path)
            return

        self._send_json(404, b'{"error":"rota nao encontrada"}')

    def log_message(self, format, *args):
        print("[proxy] " + (format % args))


if __name__ == "__main__":
    server = http.server.HTTPServer(("0.0.0.0", PROXY_PORT), ProxyHandler)
    print(f"Servidor rodando em http://0.0.0.0:{PROXY_PORT}/")
    print(f"  Painel:      http://localhost:{PROXY_PORT}/")
    print(f"  API userinfo:   GET /userinfo?target=IP:PORTA")
    print(f"  API brokerinfo: GET /brokerinfo?target=IP:PORTA")
    print(f"  Servindo HTML de: {HTML_FILE}")
    print("Pressione Ctrl+C para parar.")
    server.serve_forever()
