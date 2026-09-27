import http.server
import socketserver
import json
import os

PORT = 8000
LOG_FILE = "events_log.json"

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/logs":
            # Serve events_log.json as JSON array
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            logs = []
            if os.path.exists(LOG_FILE):
                try:
                    with open(LOG_FILE, "r", encoding="utf-8") as f:
                        logs = json.load(f)
                except Exception as e:
                    print(f"Error reading logs: {e}")
                    logs = []
            
            self.wfile.write(json.dumps(logs).encode("utf-8"))
        else:
            # Serve files normally (HTML, CSS, JS)
            super().do_GET()

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
        print(f"🚀 Server running at http://localhost:{PORT}")
        print(f"📊 Dashboard: http://localhost:{PORT}/dashboard.html")
        print(f"📡 Logs endpoint: http://localhost:{PORT}/logs")
        httpd.serve_forever()