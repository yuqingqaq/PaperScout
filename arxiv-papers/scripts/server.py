#!/usr/bin/env python3
"""
带 API 的 HTTP 服务器
支持前端直接更新知识库
"""
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse

# 添加项目根目录到 path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, PROJECT_DIR)

from src.storage import KnowledgeBaseManager
from src.utils import setup_logging

# 初始化日志
setup_logging(console=True)

KB_PATH = os.path.join(PROJECT_DIR, 'references', 'knowledge_base.md')
KB_DATA_PATH = os.path.join(PROJECT_DIR, 'output', 'kb_data.json')
SUGGESTIONS_PATH = os.path.join(PROJECT_DIR, 'references', 'kb_suggestions.json')
CONFIG_PATH = os.path.join(PROJECT_DIR, 'config.json')
OUTPUT_DIR = os.path.join(PROJECT_DIR, 'output')


class APIHandler(SimpleHTTPRequestHandler):
    """支持 API 的 HTTP 请求处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=OUTPUT_DIR, **kwargs)
    
    def do_POST(self):
        """处理 POST 请求"""
        parsed = urlparse(self.path)
        
        if parsed.path == '/api/approve-suggestion':
            self.handle_approve_suggestion()
        elif parsed.path == '/api/reject-suggestion':
            self.handle_reject_suggestion()
        elif parsed.path == '/api/run-daily':
            self.handle_run_daily()
        else:
            self.send_error(404, 'API not found')
    
    def handle_approve_suggestion(self):
        """处理采纳建议请求"""
        try:
            # 读取请求体
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            suggestion_id = data.get('id')
            if not suggestion_id:
                self.send_json_response({'success': False, 'error': '缺少建议 ID'})
                return
            
            kb_manager = KnowledgeBaseManager(KB_PATH, SUGGESTIONS_PATH)
            success = kb_manager.approve_suggestion(int(suggestion_id))

            if success:
                kb_manager.export_to_json(KB_DATA_PATH)
                self.send_json_response({'success': True, 'message': '已采纳并更新知识库'})
            else:
                self.send_json_response({'success': False, 'error': '应用建议失败或建议不存在'})
                
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def handle_reject_suggestion(self):
        """处理拒绝建议请求"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            suggestion_id = data.get('id')
            reason = data.get('reason', '')
            
            kb_manager = KnowledgeBaseManager(KB_PATH, SUGGESTIONS_PATH)
            success = kb_manager.reject_suggestion(int(suggestion_id), reason)

            if success:
                kb_manager.export_to_json(KB_DATA_PATH)
                self.send_json_response({'success': True, 'message': '已拒绝'})
            else:
                self.send_json_response({'success': False, 'error': '建议不存在'})
            
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})

    def handle_run_daily(self):
        """触发每日推荐流程（更新 papers.json 与 kb_data.json）"""
        try:
            from src.main import ArxivPapersAgent

            agent = ArxivPapersAgent(config_path=CONFIG_PATH, use_hybrid=True)
            recommended = agent.daily_recommendation()

            kb_manager = KnowledgeBaseManager(KB_PATH, SUGGESTIONS_PATH)
            kb_manager.export_to_json(KB_DATA_PATH)

            self.send_json_response({
                'success': True,
                'added_papers': len(recommended)
            })
        except Exception as e:
            self.send_json_response({'success': False, 'error': str(e)})
    
    def send_json_response(self, data: dict):
        """发送 JSON 响应"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
    
    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server(port: int = 8889):
    """启动服务器"""
    # 启动时同步 kb_data.json
    print("📚 同步知识库数据...")
    try:
        kb_manager = KnowledgeBaseManager(KB_PATH, SUGGESTIONS_PATH)
        kb_manager.export_to_json(KB_DATA_PATH)
        print("✓ kb_data.json 已更新")
    except Exception as e:
        print(f"⚠️  同步知识库失败: {e}")

    server_address = ('', port)
    httpd = HTTPServer(server_address, APIHandler)
    print(f"🚀 服务器启动在 http://localhost:{port}")
    print(f"📄 访问: http://localhost:{port}/papers.html")
    print("🔧 API: POST /api/approve-suggestion, /api/reject-suggestion, /api/run-daily")
    print("按 Ctrl+C 停止")
    httpd.serve_forever()


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8889
    run_server(port)
