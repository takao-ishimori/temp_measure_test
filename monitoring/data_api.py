import http.server
import json
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "database", "dht22_data.db")


class Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/recent":
            self._json_response(self._query_db(
                "SELECT id, timestamp, temperature_c, humidity_pct "
                "FROM dht22_readings ORDER BY id DESC LIMIT 50"
            ))
        elif self.path == "/api/all":
            self._json_response(self._query_db(
                "SELECT id, timestamp, temperature_c, humidity_pct "
                "FROM dht22_readings ORDER BY id"
            ))
        elif self.path == "/api/stats":
            self._json_response(self._query_db(
                "SELECT COUNT(*), AVG(temperature_c), MAX(temperature_c),"
                "MIN(temperature_c), AVG(humidity_pct), MAX(humidity_pct),"
                "MIN(humidity_pct) FROM dht22_readings"
            ))
        elif self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        else:
            self.send_response(404)
            self.end_headers()

    def _query_db(self, sql):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def _json_response(self, data):
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
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
    print(f"データAPI起動中: http://localhost:{port}")
    print("エンドポイント:")
    print(f"  http://localhost:{port}/api/recent  (最新50件)")
    print(f"  http://localhost:{port}/api/all     (全件)")
    print(f"  http://localhost:{port}/api/stats   (統計)")
    print(f"  http://localhost:{port}/health")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()
        print("停止しました")


if __name__ == "__main__":
    main()
