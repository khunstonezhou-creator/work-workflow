#!/usr/bin/env python3
"""
工作台认证服务
- 登录页面
- 用户管理（管理员审批）
- 会话控制
"""

import os
import sys
import json
import hashlib
import secrets
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from datetime import datetime

BASE_DIR = Path(__file__).parent
USERS_FILE = BASE_DIR / "users.json"
SESSIONS = {}  # token -> {user, login_time, last_active}

# 管理员账号
ADMIN_USER = "admin"
ADMIN_PASS_HASH = hashlib.sha256("miworkcamera".encode()).hexdigest()


def load_users():
    """加载用户列表"""
    if USERS_FILE.exists():
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"admin": {"password_hash": ADMIN_PASS_HASH, "status": "approved", "role": "admin", "created": datetime.now().isoformat()}}


def save_users(users):
    """保存用户列表"""
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def create_session(user):
    """创建会话"""
    token = secrets.token_hex(32)
    SESSIONS[token] = {
        "user": user,
        "login_time": datetime.now().isoformat(),
        "last_active": time.time()
    }
    return token


def check_session(token):
    """检查会话是否有效"""
    if token and token in SESSIONS:
        session = SESSIONS[token]
        # 会话有效期 24 小时
        if time.time() - session["last_active"] < 86400:
            session["last_active"] = time.time()
            return session["user"]
        else:
            del SESSIONS[token]
    return None


class AuthHandler(SimpleHTTPRequestHandler):
    """带认证的 HTTP 处理器"""

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        # 登录页面
        if path == "/login" or path == "/login.html":
            self._serve_login_page()
            return

        # 登出
        if path == "/logout":
            token = self._get_token()
            if token in SESSIONS:
                del SESSIONS[token]
            self.send_response(302)
            self.send_header("Location", "/login")
            self.end_headers()
            return

        # 管理员页面
        if path == "/admin":
            if not self._is_admin():
                self.send_response(302)
                self.send_header("Location", "/login")
                self.end_headers()
                return
            self._serve_admin_page()
            return

        # API: 登录
        if path == "/api/login":
            self._handle_login()
            return

        # API: 获取当前用户信息
        if path == "/api/me":
            token = self._get_token()
            user = check_session(token)
            if not user:
                self._json_response(401, {"error": "Unauthorized"})
                return
            users = load_users()
            user_data = users.get(user, {})
            self._json_response(200, {"user": user, "role": user_data.get("role", "viewer")})
            return

        # API: 获取用户列表（管理员）
        if path == "/api/users":
            if not self._is_admin():
                self._json_response(403, {"error": "Forbidden"})
                return
            self._json_response(200, load_users())
            return

        # API: 审批用户（管理员）
        if path == "/api/approve":
            if not self._is_admin():
                self._json_response(403, {"error": "Forbidden"})
                return
            self._handle_approve()
            return

        # API: 拒绝用户（管理员）
        if path == "/api/reject":
            if not self._is_admin():
                self._json_response(403, {"error": "Forbidden"})
                return
            self._handle_reject()
            return

        # 静态文件 - 需要登录
        if not self._is_authenticated():
            # 允许访问登录页面和静态资源
            if path.startswith("/login") or path.endswith((".css", ".js", ".png", ".ico")):
                super().do_GET()
                return
            self.send_response(302)
            self.send_header("Location", "/login")
            self.end_headers()
            return

        super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/login":
            self._handle_login()
            return

        if path == "/api/register":
            self._handle_register()
            return

        if not self._is_authenticated():
            self._json_response(401, {"error": "Unauthorized"})
            return

        if path == "/api/approve":
            if not self._is_admin():
                self._json_response(403, {"error": "Forbidden"})
                return
            self._handle_approve()
            return

        if path == "/api/reject":
            if not self._is_admin():
                self._json_response(403, {"error": "Forbidden"})
                return
            self._handle_reject()
            return

        self._json_response(404, {"error": "Not found"})

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def _get_token(self):
        """从 cookie 或 header 获取 token"""
        # 从 cookie 获取
        cookie = self.headers.get("Cookie", "")
        for item in cookie.split(";"):
            if item.strip().startswith("token="):
                return item.strip().split("=")[1]
        # 从 header 获取
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None

    def _is_authenticated(self):
        """检查是否已登录"""
        token = self._get_token()
        return check_session(token) is not None

    def _is_admin(self):
        """检查是否是管理员"""
        token = self._get_token()
        user = check_session(token)
        if not user:
            return False
        users = load_users()
        return users.get(user, {}).get("role") == "admin"

    def _handle_login(self):
        """处理登录请求"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len))
        username = body.get("username", "").strip()
        password = body.get("password", "")

        if not username or not password:
            self._json_response(400, {"error": "请输入用户名和密码"})
            return

        users = load_users()
        user_data = users.get(username)

        if not user_data:
            self._json_response(401, {"error": "用户不存在"})
            return

        if user_data["status"] == "pending":
            self._json_response(403, {"error": "账号待审批，请等待管理员批准"})
            return

        if user_data["status"] == "rejected":
            self._json_response(403, {"error": "账号已被拒绝"})
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if password_hash != user_data["password_hash"]:
            self._json_response(401, {"error": "密码错误"})
            return

        token = create_session(username)
        self._json_response(200, {
            "ok": True,
            "token": token,
            "user": username,
            "role": user_data.get("role", "viewer")
        })

    def _handle_register(self):
        """处理注册请求"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len))
        username = body.get("username", "").strip()
        password = body.get("password", "")

        if not username or not password:
            self._json_response(400, {"error": "请输入用户名和密码"})
            return

        if len(username) < 2:
            self._json_response(400, {"error": "用户名至少2个字符"})
            return

        if len(password) < 6:
            self._json_response(400, {"error": "密码至少6个字符"})
            return

        users = load_users()
        if username in users:
            self._json_response(409, {"error": "用户名已存在"})
            return

        users[username] = {
            "password_hash": hashlib.sha256(password.encode()).hexdigest(),
            "status": "pending",
            "role": "viewer",
            "created": datetime.now().isoformat()
        }
        save_users(users)

        self._json_response(200, {"ok": True, "message": "注册成功，等待管理员审批"})

    def _handle_approve(self):
        """审批用户 / 修改角色"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len))
        username = body.get("username", "")
        role = body.get("role", "viewer")

        users = load_users()
        if username not in users:
            self._json_response(404, {"error": "用户不存在"})
            return

        users[username]["status"] = "approved"
        users[username]["role"] = role if role in ["admin", "viewer"] else "viewer"
        save_users(users)
        self._json_response(200, {"ok": True, "message": f"已批准 {username}，角色: {role}"})

    def _handle_reject(self):
        """拒绝用户"""
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len))
        username = body.get("username", "")

        users = load_users()
        if username not in users:
            self._json_response(404, {"error": "用户不存在"})
            return

        users[username]["status"] = "rejected"
        save_users(users)
        self._json_response(200, {"ok": True, "message": f"已拒绝 {username}"})

    def _json_response(self, code, data):
        """返回 JSON 响应"""
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_login_page(self):
        """提供登录页面"""
        html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>工作台 - 登录</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh;display:flex;align-items:center;justify-content:center}
.login-box{background:white;border-radius:16px;padding:40px;width:380px;box-shadow:0 20px 60px rgba(0,0,0,0.3)}
h1{text-align:center;font-size:24px;margin-bottom:8px;color:#333}
p.sub{text-align:center;font-size:13px;color:#999;margin-bottom:24px}
.tabs{display:flex;margin-bottom:20px;border-bottom:2px solid #eee}
.tab{flex:1;padding:10px;text-align:center;cursor:pointer;font-size:14px;color:#999;border-bottom:2px solid transparent;margin-bottom:-2px}
.tab.active{color:#667eea;border-bottom-color:#667eea}
.form{display:none}.form.active{display:block}
input{width:100%;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;font-size:14px;margin-bottom:12px;outline:none}
input:focus{border-color:#667eea}
button{width:100%;padding:12px;background:#667eea;color:white;border:none;border-radius:8px;font-size:14px;cursor:pointer;font-weight:600}
button:hover{background:#5a6fd6}
.msg{text-align:center;font-size:12px;margin-top:12px;min-height:18px}
.msg.err{color:#c62828}
.msg.ok{color:#2e7d32}
</style>
</head>
<body>
<div class="login-box">
  <h1>🚀 个人工作台</h1>
  <p class="sub">AI 辅助 Jira 问题管理与知识库</p>
  <div class="tabs">
    <div class="tab active" onclick="switchTab('login')">登录</div>
    <div class="tab" onclick="switchTab('register')">注册</div>
  </div>
  <div class="form active" id="login-form">
    <input id="login-user" placeholder="用户名" autocomplete="username">
    <input id="login-pass" type="password" placeholder="密码" autocomplete="current-password">
    <button onclick="doLogin()">登 录</button>
    <div class="msg" id="login-msg"></div>
  </div>
  <div class="form" id="register-form">
    <input id="reg-user" placeholder="用户名（至少2字符）" autocomplete="username">
    <input id="reg-pass" type="password" placeholder="密码（至少6字符）" autocomplete="new-password">
    <button onclick="doRegister()">注 册</button>
    <div class="msg" id="reg-msg"></div>
  </div>
</div>
<script>
function switchTab(t){
  document.querySelectorAll('.tab').forEach((el,i)=>{el.classList.toggle('active',i===(t==='login'?0:1))});
  document.getElementById('login-form').classList.toggle('active',t==='login');
  document.getElementById('register-form').classList.toggle('active',t==='register');
}
async function doLogin(){
  const user=document.getElementById('login-user').value.trim();
  const pass=document.getElementById('login-pass').value;
  const msg=document.getElementById('login-msg');
  if(!user||!pass){msg.className='msg err';msg.textContent='请输入用户名和密码';return;}
  try{
    const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user,password:pass})});
    const d=await r.json();
    if(d.ok){
      document.cookie='token='+d.token+';path=/;max-age=86400';
      document.cookie='role='+d.role+';path=/;max-age=86400';
      document.cookie='user='+d.user+';path=/;max-age=86400';
      window.location.href='/';
    }
    else{msg.className='msg err';msg.textContent=d.error;}
  }catch(e){msg.className='msg err';msg.textContent='网络错误';}
}
async function doRegister(){
  const user=document.getElementById('reg-user').value.trim();
  const pass=document.getElementById('reg-pass').value;
  const msg=document.getElementById('reg-msg');
  if(!user||!pass){msg.className='msg err';msg.textContent='请输入用户名和密码';return;}
  try{
    const r=await fetch('/api/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user,password:pass})});
    const d=await r.json();
    if(d.ok){msg.className='msg ok';msg.textContent=d.message;}
    else{msg.className='msg err';msg.textContent=d.error;}
  }catch(e){msg.className='msg err';msg.textContent='网络错误';}
}
document.addEventListener('keydown',e=>{if(e.key==='Enter'){if(document.getElementById('login-form').classList.contains('active'))doLogin();else doRegister();}});
</script>
</body>
</html>'''
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_admin_page(self):
        """提供管理员页面"""
        html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>工作台 - 管理后台</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,sans-serif;background:#f0f2f5;padding:20px}
h1{font-size:20px;margin-bottom:20px}
.card{background:white;border-radius:8px;padding:20px;margin-bottom:16px;box-shadow:0 1px 3px rgba(0,0,0,0.08)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#f5f5f5;padding:10px;text-align:left;font-weight:600}
td{padding:10px;border-bottom:1px solid #eee}
.badge{padding:3px 8px;border-radius:10px;font-size:11px;font-weight:600}
.badge.pending{background:#fff3e0;color:#e65100}
.badge.approved{background:#e8f5e9;color:#2e7d32}
.badge.rejected{background:#ffebee;color:#c62828}
.badge.admin{background:#e3f2fd;color:#1565c0}
.badge.viewer{background:#f5f5f5;color:#616161}
.btn{padding:4px 12px;border:none;border-radius:4px;font-size:11px;cursor:pointer;margin-right:4px}
.btn-approve{background:#4caf50;color:white}
.btn-reject{background:#f44336;color:white}
.btn-role{background:#667eea;color:white}
select{padding:4px 8px;border:1px solid #e0e0e0;border-radius:4px;font-size:12px}
a{color:#667eea;text-decoration:none}
.info{background:#e3f2fd;padding:12px 16px;border-radius:6px;font-size:12px;color:#1565c0;margin-bottom:16px}
</style>
</head>
<body>
<h1>👥 用户管理 <a href="/" style="font-size:13px;margin-left:16px">← 返回工作台</a></h1>
<div class="info">
  <strong>权限说明：</strong><br>
  • <strong>管理员 (admin)</strong> — 可配置 MCP、修改页面内容、导入知识库、管理用户<br>
  • <strong>查看者 (viewer)</strong> — 只能浏览工作台内容，无法修改
</div>
<div class="card">
  <table>
    <thead><tr><th>用户名</th><th>状态</th><th>角色</th><th>注册时间</th><th>操作</th></tr></thead>
    <tbody id="users-list"></tbody>
  </table>
</div>
<script>
const ROLES={admin:'管理员 (完全权限)',viewer:'查看者 (只读)'};
async function loadUsers(){
  const r=await fetch('/api/users');
  const users=await r.json();
  const tbody=document.getElementById('users-list');
  tbody.innerHTML=Object.entries(users).map(([name,u])=>{
    const isAdmin=u.role==='admin';
    const isPending=u.status==='pending';
    return `<tr>
      <td><strong>${name}</strong></td>
      <td><span class="badge ${u.status}">${isPending?'待审批':u.status==='approved'?'已批准':'已拒绝'}</span></td>
      <td><span class="badge ${u.role}">${ROLES[u.role]||u.role}</span></td>
      <td>${(u.created||'').substring(0,16)}</td>
      <td>
        ${!isAdmin?`
          ${isPending?`
            <select id="role-${name}" style="margin-right:8px">
              <option value="viewer">查看者</option>
              <option value="admin">管理员</option>
            </select>
            <button class="btn btn-approve" onclick="approve('${name}')">批准</button>
          `:u.status==='approved'?`
            <button class="btn btn-role" onclick="toggleRole('${name}','${u.role}')">${isAdmin?'降为查看者':'升为管理员'}</button>
          `:''}
          ${u.status!=='rejected'?`<button class="btn btn-reject" onclick="reject('${name}')">拒绝</button>`:''}
        `:'<span style="color:#999;font-size:11px">超级管理员</span>'}
      </td>
    </tr>`;
  }).join('');
}
async function approve(user){
  const sel=document.getElementById('role-'+user);
  const role=sel?sel.value:'viewer';
  await fetch('/api/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user,role:role})});
  loadUsers();
}
async function reject(user){
  if(!confirm('确定拒绝 '+user+'？'))return;
  await fetch('/api/reject',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user})});
  loadUsers();
}
async function toggleRole(user,current){
  const newRole=current==='admin'?'viewer':'admin';
  await fetch('/api/approve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({username:user,role:newRole})});
  loadUsers();
}
loadUsers();
</script>
</body>
</html>'''
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        """只记录 API 请求"""
        if "/api/" in (args[0] if args else ""):
            super().log_message(fmt, *args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    os.chdir(BASE_DIR)

    # 初始化用户文件
    if not USERS_FILE.exists():
        save_users(load_users())
        print(f"已创建用户配置文件: {USERS_FILE}")
        print(f"默认管理员: admin / admin123")

    server = HTTPServer(("", port), AuthHandler)
    print(f"工作台服务启动: http://localhost:{port}")
    print(f"管理员后台: http://localhost:{port}/admin")
    print(f"登录页面: http://localhost:{port}/login")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
