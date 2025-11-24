import os
import socket
import threading
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import mimetypes
from urllib.parse import urlparse, unquote
import shutil
import sys

UPLOAD_FOLDER = Path("shared_files")
UPLOAD_FOLDER.mkdir(exist_ok=True)

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

class FileExchangeHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/files":
            self.list_files()
        elif self.path == "/api/server-info":
            self.server_info()
        elif self.path.startswith("/api/download/"):
            self.download_file()
        else:
            self.serve_index()
    
    def do_POST(self):
        if self.path == "/api/upload":
            self.upload_file()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        if self.path.startswith("/api/delete/"):
            self.delete_file()
        else:
            self.send_error(404)
    
    def list_files(self):
        try:
            files = []
            for item in UPLOAD_FOLDER.iterdir():
                if item.is_file():
                    files.append({
                        "name": item.name,
                        "size": item.stat().st_size,
                        "modified": item.stat().st_mtime
                    })
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(files).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def server_info(self):
        try:
            local_ip = get_local_ip()
            info = {
                "local_ip": local_ip,
                "port": 8888,
                "status": "online"
            }
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps(info).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def download_file(self):
        try:
            filename = unquote(self.path.split("/api/download/")[1])
            filepath = UPLOAD_FOLDER / filename
            
            if not filepath.exists() or not filepath.is_file():
                self.send_error(404, "File not found")
                return
            
            self.send_response(200)
            self.send_header("Content-type", mimetypes.guess_type(filepath)[0] or "application/octet-stream")
            self.send_header("Content-Length", filepath.stat().st_size)
            self.send_header("Content-Disposition", f'attachment; filename="{filepath.name}"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(500, str(e))
    
    def upload_file(self):
        try:
            content_length = int(self.headers['Content-Length'])
            filename = self.headers.get('X-Filename', 'uploaded_file')
            
            filepath = UPLOAD_FOLDER / filename
            
            with open(filepath, 'wb') as f:
                f.write(self.rfile.read(content_length))
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success", "filename": filename}).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def delete_file(self):
        try:
            filename = unquote(self.path.split("/api/delete/")[1])
            filepath = UPLOAD_FOLDER / filename
            
            if not filepath.exists():
                self.send_error(404, "File not found")
                return
            
            os.remove(filepath)
            
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_index(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        with open("index.html", 'rb') as f:
            self.wfile.write(f.read())
    
    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Filename")
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

if __name__ == "__main__":
    PORT = 8888
    server_address = ("0.0.0.0", PORT)
    httpd = HTTPServer(server_address, FileExchangeHandler)
    
    local_ip = get_local_ip()
    
    print("\n" + "="*50)
    print("  📁 FILE EXCHANGER SERVER")
    print("="*50)
    print(f"✓ Server started successfully!")
    print(f"\nAccess from other computers:")
    print(f"  → http://{local_ip}:{PORT}")
    print(f"  → http://localhost:{PORT} (local access)")
    print(f"\nShared files folder: {UPLOAD_FOLDER.absolute()}")
    print(f"\nPress Ctrl+C to stop the server")
    print("="*50 + "\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✗ Server stopped")
        sys.exit(0)
