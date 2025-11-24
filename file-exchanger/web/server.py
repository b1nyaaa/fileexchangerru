import os
import socket
import json
import mimetypes
import hashlib
import secrets
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse, unquote, parse_qs
import sys

# Папка для хранения данных серверов
SERVERS_FOLDER = Path("servers_data")
SERVERS_FOLDER.mkdir(exist_ok=True)

class Room:
    def __init__(self, room_id, password_hash):
        self.room_id = room_id
        self.password_hash = password_hash
        self.folder = SERVERS_FOLDER / room_id
        self.folder.mkdir(exist_ok=True)
        
    def verify_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest() == self.password_hash
    
    def get_files(self):
        files = []
        for item in self.folder.iterdir():
            if item.is_file() and item.name != '.room_info':
                files.append({
                    "name": item.name,
                    "size": item.stat().st_size,
                    "modified": item.stat().st_mtime
                })
        return files

class FileExchangeHandler(SimpleHTTPRequestHandler):
    rooms = {}  # room_id -> Room
    
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.serve_file("index.html")
        elif self.path == "/api/rooms":
            self.list_rooms()
        elif self.path.startswith("/api/room/") and "/files" in self.path:
            self.list_room_files()
        elif self.path.startswith("/api/room/") and "/download/" in self.path:
            self.download_file()
        else:
            self.serve_file("index.html")
    
    def do_POST(self):
        if self.path == "/api/create-room":
            self.create_room()
        elif self.path == "/api/join-room":
            self.join_room()
        elif self.path.startswith("/api/room/") and "/upload" in self.path:
            self.upload_file()
        else:
            self.send_error(404)
    
    def do_DELETE(self):
        if self.path.startswith("/api/room/") and "/delete/" in self.path:
            self.delete_file()
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Filename, X-Password")
        self.end_headers()
    
    def serve_file(self, filename):
        try:
            filepath = Path(__file__).parent / filename
            if not filepath.exists():
                self.send_error(404, f"File {filename} not found")
                return
                
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(500, str(e))
    
    def create_room(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            password = data.get('password', '')
            if not password or len(password) < 4:
                self.send_json_response({"error": "Пароль должен быть минимум 4 символа"}, 400)
                return
            
            # Генерируем уникальный ID комнаты (6 символов)
            room_id = secrets.token_hex(3).upper()
            while room_id in self.rooms or (SERVERS_FOLDER / room_id).exists():
                room_id = secrets.token_hex(3).upper()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            room = Room(room_id, password_hash)
            
            # Сохраняем информацию о комнате
            room_info = {
                'room_id': room_id,
                'password_hash': password_hash,
                'created': True
            }
            
            with open(room.folder / '.room_info', 'w') as f:
                json.dump(room_info, f)
            
            self.rooms[room_id] = room
            
            self.send_json_response({
                "success": True,
                "room_id": room_id,
                "message": f"Комната создана! ID: {room_id}"
            })
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def join_room(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            room_id = data.get('room_id', '').upper().strip()
            password = data.get('password', '')
            
            if not room_id:
                self.send_json_response({"error": "Введите ID комнаты"}, 400)
                return
            
            # Проверяем существование комнаты
            room_folder = SERVERS_FOLDER / room_id
            if not room_folder.exists():
                self.send_json_response({"error": "Комната не найдена"}, 404)
                return
            
            # Загружаем информацию о комнате
            room_info_file = room_folder / '.room_info'
            if not room_info_file.exists():
                self.send_json_response({"error": "Комната повреждена"}, 500)
                return
            
            with open(room_info_file, 'r') as f:
                room_info = json.load(f)
            
            # Проверяем пароль
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            if password_hash != room_info['password_hash']:
                self.send_json_response({"error": "Неверный пароль"}, 403)
                return
            
            # Загружаем или создаем комнату
            if room_id not in self.rooms:
                self.rooms[room_id] = Room(room_id, room_info['password_hash'])
            
            self.send_json_response({
                "success": True,
                "room_id": room_id,
                "message": "Успешный вход!"
            })
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def list_room_files(self):
        try:
            # Парсим путь: /api/room/{room_id}/files
            parts = self.path.split('/')
            room_id = parts[3] if len(parts) > 3 else None
            
            password = self.headers.get('X-Password', '')
            
            if not room_id or room_id not in self.rooms:
                self.send_json_response({"error": "Комната не найдена"}, 404)
                return
            
            room = self.rooms[room_id]
            if not room.verify_password(password):
                self.send_json_response({"error": "Неверный пароль"}, 403)
                return
            
            files = room.get_files()
            self.send_json_response(files)
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def upload_file(self):
        try:
            # Парсим путь: /api/room/{room_id}/upload
            parts = self.path.split('/')
            room_id = parts[3] if len(parts) > 3 else None
            
            password = self.headers.get('X-Password', '')
            filename = self.headers.get('X-Filename', 'uploaded_file')
            
            if not room_id or room_id not in self.rooms:
                self.send_json_response({"error": "Комната не найдена"}, 404)
                return
            
            room = self.rooms[room_id]
            if not room.verify_password(password):
                self.send_json_response({"error": "Неверный пароль"}, 403)
                return
            
            content_length = int(self.headers['Content-Length'])
            filepath = room.folder / filename
            
            with open(filepath, 'wb') as f:
                f.write(self.rfile.read(content_length))
            
            self.send_json_response({
                "success": True,
                "filename": filename,
                "message": "Файл загружен"
            })
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def download_file(self):
        try:
            # Парсим путь: /api/room/{room_id}/download/{filename}
            parts = self.path.split('/')
            room_id = parts[3] if len(parts) > 3 else None
            filename = unquote(parts[5]) if len(parts) > 5 else None
            
            password = self.headers.get('X-Password', '')
            
            if not room_id or room_id not in self.rooms:
                self.send_error(404, "Комната не найдена")
                return
            
            room = self.rooms[room_id]
            if not room.verify_password(password):
                self.send_error(403, "Неверный пароль")
                return
            
            filepath = room.folder / filename
            if not filepath.exists():
                self.send_error(404, "Файл не найден")
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
    
    def delete_file(self):
        try:
            # Парсим путь: /api/room/{room_id}/delete/{filename}
            parts = self.path.split('/')
            room_id = parts[3] if len(parts) > 3 else None
            filename = unquote(parts[5]) if len(parts) > 5 else None
            
            password = self.headers.get('X-Password', '')
            
            if not room_id or room_id not in self.rooms:
                self.send_json_response({"error": "Комната не найдена"}, 404)
                return
            
            room = self.rooms[room_id]
            if not room.verify_password(password):
                self.send_json_response({"error": "Неверный пароль"}, 403)
                return
            
            filepath = room.folder / filename
            if not filepath.exists():
                self.send_json_response({"error": "Файл не найден"}, 404)
                return
            
            os.remove(filepath)
            
            self.send_json_response({
                "success": True,
                "message": "Файл удален"
            })
            
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def list_rooms(self):
        try:
            rooms_list = []
            for room_id, room in self.rooms.items():
                file_count = len(room.get_files())
                rooms_list.append({
                    "room_id": room_id,
                    "file_count": file_count
                })
            
            self.send_json_response(rooms_list)
        except Exception as e:
            self.send_json_response({"error": str(e)}, 500)
    
    def send_json_response(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def log_message(self, format, *args):
        print(f"[{self.log_date_time_string()}] {format % args}")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == "__main__":
    PORT = 8888
    server_address = ("0.0.0.0", PORT)
    
    # Загружаем существующие комнаты
    for room_folder in SERVERS_FOLDER.iterdir():
        if room_folder.is_dir():
            room_info_file = room_folder / '.room_info'
            if room_info_file.exists():
                with open(room_info_file, 'r') as f:
                    room_info = json.load(f)
                    FileExchangeHandler.rooms[room_info['room_id']] = Room(
                        room_info['room_id'],
                        room_info['password_hash']
                    )
    
    httpd = HTTPServer(server_address, FileExchangeHandler)
    
    local_ip = get_local_ip()
    
    print("\n" + "="*60)
    print("  🌐 FILE EXCHANGER WEB SERVER")
    print("="*60)
    print(f"✓ Server started successfully!")
    print(f"\nAccess from:")
    print(f"  → http://{local_ip}:{PORT}")
    print(f"  → http://localhost:{PORT} (local)")
    print(f"\nActive rooms: {len(FileExchangeHandler.rooms)}")
    print(f"\nPress Ctrl+C to stop")
    print("="*60 + "\n")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n✗ Server stopped")
        sys.exit(0)
