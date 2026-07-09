import http.server
import json
import sqlite3
import os
import urllib.parse

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "dht22_data.db")
HTML_PATH = os.path.join(os.path.dirname(__file__), "dashboard.html")
SYS_PATH = os.path.join(os.path.dirname(__file__), "system_stats.json")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        if path == "/dashboard" or path == "/":
            self._serve_html()
        elif path == "/api/recent":
            self._json_response(self._query_db(
                "SELECT id, timestamp, temperature_c, humidity_pct "
                "FROM dht22_readings ORDER BY id DESC LIMIT 200"
            ))
        elif path == "/api/stats":
            self._json_response(self._query_db(
                "SELECT COUNT(*) as count, "
                "ROUND(AVG(temperature_c),2) as avg_temp, "
                "ROUND(MAX(temperature_c),2) as max_temp, "
                "ROUND(MIN(temperature_c),2) as min_temp, "
                "ROUND(AVG(humidity_pct),2) as avg_hum, "
                "ROUND(MAX(humidity_pct),2) as max_hum, "
                "ROUND(MIN(humidity_pct),2) as min_hum "
                "FROM dht22_readings"
            ))
        elif path == "/api/system":
            try:
                with open(SYS_PATH, "r") as f:
                    data = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                data = {"cpu": 0, "memory": 0, "disk": 0,
                        "cpu_temp": 0, "loadavg": 0, "uptime": "0h 0m"}
            self._json_response(data)
        elif path == "/api/data":
            fr = params.get("from", [""])[0]
            to = params.get("to", [""])[0]
            if fr and to:
                self._json_response(self._query_db(
                    "SELECT id, timestamp, temperature_c, humidity_pct "
                    "FROM dht22_readings "
                    "WHERE timestamp >= ? AND timestamp <= ? "
                    "ORDER BY id", (fr, to)
                ))
            else:
                self._json_response({"error": "from/to required"})
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/delete":
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len))
            fr = body.get("from", "")
            to = body.get("to", "")
            if fr and to:
                conn = sqlite3.connect(DB_PATH)
                conn.execute(
                    "DELETE FROM dht22_readings WHERE timestamp >= ? AND timestamp <= ?",
                    (fr, to)
                )
                deleted = conn.total_changes
                conn.commit()
                conn.close()
                self._json_response({"deleted": deleted})
            else:
                self._json_response({"error": "from/to required"})
        else:
            self.send_response(404)
            self.end_headers()

    def _serve_html(self):
        with open(HTML_PATH, "r", encoding="utf-8") as f:
            html = f.read()
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _query_db(self, sql, params=()):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _json_response(self, data):
        if isinstance(data, list):
            for row in data:
                for k, v in row.items():
                    if isinstance(v, float):
                        row[k] = round(v, 1)
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def main():
    port = 8080
    server = http.server.HTTPServer(("0.0.0.0", port), Handler)
    print(f"ダッシュボード起動: http://localhost:{port}/dashboard")
    print("Ctrl+C で停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print("停止しました")


if __name__ == "__main__":
    main()
