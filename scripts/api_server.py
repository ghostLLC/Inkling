"""
API 服务器 (Legacy) - 旧版 stdlib HTTP 服务器

⚠️ 此文件为历史遗留，新项目请使用 FastAPI 版本：
    cd D:\\Inkling
    python -m backend.main

用法: python scripts/api_server.py
"""
import os
import sys
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# 添加项目根目录到 sys.path
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, _project_root)

from ai_engine.core import SessionManager, create_provider

# 配置
API_KEY = os.environ.get("OPENAI_API_KEY", "")
BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.environ.get("OPENAI_MODEL", "deepseek-chat")

# 初始化 Provider
if API_KEY:
    try:
        provider = create_provider("openai-compatible", api_key=API_KEY, model=MODEL, base_url=BASE_URL)
        print(f"✅ API 服务器已连接: {BASE_URL}")
    except Exception as e:
        print(f"⚠️ API 连接失败: {e}，使用 MockProvider")
        provider = create_provider("mock")
else:
    print("⚠️ 未配置 API Key，使用 MockProvider")
    provider = create_provider("mock")

manager = SessionManager(provider)


class APIHandler(BaseHTTPRequestHandler):
    """简单的 REST API 处理器"""
    
    def _set_headers(self, content_type="application/json"):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
    
    def do_OPTIONS(self):
        self._set_headers()
    
    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        if path == "/health":
            self._set_headers()
            self.wfile.write(json.dumps({"status": "ok", "provider": provider.name}).encode())
        elif path == "/":
            # 返回静态 HTML
            html_path = os.path.join(os.path.dirname(__file__), "static", "demo.html")
            if os.path.exists(html_path):
                self._set_headers("text/html")
                with open(html_path, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode())
            else:
                self._set_headers()
                self.wfile.write(json.dumps({"error": "demo.html not found"}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
        except json.JSONDecodeError:
            self._set_headers()
            self.wfile.write(json.dumps({"error": "Invalid JSON"}).encode())
            return
        
        if path == "/api/create_session":
            topic = data.get("topic", "")
            session_id = manager.create_session(topic)
            self._set_headers()
            self.wfile.write(json.dumps({
                "session_id": session_id,
                "topic": topic,
                "status": "created"
            }).encode())
        
        elif path == "/api/chat":
            session_id = data.get("session_id", "")
            message = data.get("message", "")
            
            if not session_id or not message:
                self._set_headers()
                self.wfile.write(json.dumps({"error": "Missing session_id or message"}).encode())
                return
            
            result = manager.process(session_id, message)
            self._set_headers()
            self.wfile.write(json.dumps(result).encode())
        
        elif path == "/api/session_info":
            session_id = data.get("session_id", "")
            info = manager.get_session_info(session_id)
            self._set_headers()
            self.wfile.write(json.dumps(info or {"error": "Session not found"}).encode())
        
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # 简化日志输出
        print(f"[{self.log_date_time_string()}] {args[0]}")


def run_server(port=8080):
    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    print(f"\n🚀 API 服务器启动: http://localhost:{port}")
    print(f"📖 打开浏览器访问: http://localhost:{port}")
    print(f"🔌 API 端点: POST /api/create_session, POST /api/chat")
    print(f"\n按 Ctrl+C 停止服务器\n")
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    run_server(port)
