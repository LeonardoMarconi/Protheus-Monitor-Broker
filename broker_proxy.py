import http.server
import socketserver
import urllib.request
import urllib.parse
import ssl
import json
import re
import os
import mimetypes
import socket

PROXY_PORT = [Defina a porta aqui]

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
    # Evita que uma thread trave para sempre se o cliente não fechar a conexão
    timeout = 20
    # Reduz ruído de log quando o cliente encerra a conexão abruptamente
    protocol_version = "HTTP/1.1"

    def _set_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(204)
        self._set_cors_headers()
        self.end_headers()

    def _safe_write(self, body):
        """Escreve a resposta protegendo contra cliente que já desconectou."""
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, socket.timeout):
            # Cliente fechou a aba ou perdeu a rede no meio da resposta — ignora, não derruba o servidor
            pass

    def _send_json(self, status, payload_bytes):
        try:
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload_bytes)))
            self._set_cors_headers()
            self.end_headers()
            self._safe_write(payload_bytes)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, socket.timeout):
            pass

    def _send_file(self, filepath):
        try:
            if not os.path.isfile(filepath):
                self.send_response(404)
                self._set_cors_headers()
                self.end_headers()
                self._safe_write(b"Arquivo nao encontrado: " + filepath.encode("utf-8"))
                return
            ctype = mimetypes.guess_type(filepath)[0] or "application/octet-stream"
            with open(filepath, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(body)))
            self._set_cors_headers()
            self.end_headers()
            self._safe_write(body)
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, socket.timeout):
            pass

    def do_GET(self):
        try:
            self._handle_get()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, socket.timeout):
            # Cliente encerrou a conexão no meio da requisição — comum com abas fechadas/rede instável
            pass
        except Exception as e:
            # Qualquer outro erro inesperado: loga e responde 500, mas NUNCA deixa a thread propagar
            # a exceção para o servidor (o que derrubaria o processo inteiro no modelo antigo).
            print(f"[proxy] ERRO inesperado tratando {self.path}: {e}")
            try:
                self._send_json(500, json.dumps({"error": "erro interno no proxy", "detail": str(e)}).encode("utf-8"))
            except Exception:
                pass

    def _handle_get(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path.rstrip("/")
        qs = urllib.parse.parse_qs(parsed.query)

        # --- Rotas de API do broker ---
        route_map = {"/userinfo": "totvs_broker_query/userinfo", "/brokerinfo": "totvs_broker_query"}
        if path in route_map:
            target_param = qs.get("target", [None])[0]
            if not target_param:
                self._send_json(400, b'{"error":"parametro target ausente, ex: ?target=192.168.xxx.xxx:xxxx"}')
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

    def handle_one_request(self):
        try:
            super().handle_one_request()
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, socket.timeout):
            self.close_connection = True


class ThreadingHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    """Servidor HTTP multi-thread: cada requisição roda numa thread própria,
    então múltiplos usuários acessando ao mesmo tempo não ficam bloqueando
    uns aos outros (era essa a causa da instabilidade com o servidor antigo)."""
    daemon_threads = True          # threads não impedem o processo de encerrar (Ctrl+C limpo)
    allow_reuse_address = True     # evita erro "endereço em uso" ao reiniciar rapidamente
    request_queue_size = 128       # fila de conexões pendentes maior, para picos de acesso simultâneo


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PROXY_PORT), ProxyHandler)
    print(f"Servidor multi-thread rodando em http://0.0.0.0:{PROXY_PORT}/")
    print(f"  Painel:      http://localhost:{PROXY_PORT}/")
    print(f"  API userinfo:   GET /userinfo?target=IP:PORTA")
    print(f"  API brokerinfo: GET /brokerinfo?target=IP:PORTA")
    print(f"  Servindo HTML de: {HTML_FILE}")
    print("Pressione Ctrl+C para parar.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nEncerrando servidor...")
        server.shutdown()
