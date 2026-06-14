#!/usr/bin/env python3
"""
工作台 API 服务
- 静态文件服务（原有功能）
- POST /api/query — 执行 SQL 查询并返回结果
"""

import os
import sys
import json
import time
import csv
import io
import logging
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

# 添加 data-sql scripts 到 path
DATA_SQL_DIR = Path(__file__).parent.parent / "data-sql" / "scripts"
sys.path.insert(0, str(DATA_SQL_DIR))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

# 加载 .env
try:
    from dotenv import load_dotenv
    load_dotenv(DATA_SQL_DIR / ".env")
except ImportError:
    pass


class WorkbenchHandler(SimpleHTTPRequestHandler):
    """静态文件 + API 处理器"""

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/query":
            self._handle_query()
        else:
            self.send_error(404, "Not Found")

    def _handle_query(self):
        try:
            content_len = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_len))
            sql = body.get("sql", "").strip()
            if not sql:
                self._json_response(400, {"error": "SQL 不能为空"})
                return

            logger.info(f"执行 SQL: {sql[:120]}...")

            # Preflight 检查
            try:
                from preflight import preflight_check
                issues = preflight_check(sql)
                errors = [i for i in issues if i["level"] == "error"]
                if errors:
                    msgs = "; ".join(i["message"] for i in errors)
                    self._json_response(400, {"error": f"SQL 预检失败: {msgs}", "issues": issues})
                    return
                warnings = [i for i in issues if i["level"] == "warn"]
            except Exception:
                warnings = []

            # 执行 SQL
            from run_sql import DataWorks
            token_id = os.environ.get("DATAWORKS_TOKEN_ID")
            if not token_id:
                self._json_response(500, {"error": "DATAWORKS_TOKEN_ID 未配置"})
                return

            dw = DataWorks(token_id=token_id)
            start = time.time()
            result = dw.execute_sql(sql)
            elapsed = round(time.time() - start, 2)

            # 解析结果
            if result.startswith("Error:") or result.startswith("SQL Execution Failed"):
                self._json_response(200, {
                    "ok": False,
                    "error": result,
                    "elapsed": elapsed,
                    "warnings": warnings
                })
            elif result.startswith("Result:"):
                # 大结果集已保存为 CSV
                self._json_response(200, {
                    "ok": True,
                    "message": result,
                    "elapsed": elapsed,
                    "warnings": warnings
                })
            elif result.startswith("SQL executed successfully"):
                self._json_response(200, {
                    "ok": True,
                    "message": result,
                    "elapsed": elapsed,
                    "warnings": warnings
                })
            else:
                # 表格结果 — 解析为 columns + rows
                lines = result.strip().split("\n")
                if len(lines) >= 1:
                    # pandas to_string 格式：第一行是列名，空格分隔
                    # 用更可靠的方式：直接从 run_sql 拿 DataFrame
                    self._json_response(200, {
                        "ok": True,
                        "raw": result,
                        "elapsed": elapsed,
                        "warnings": warnings
                    })
                else:
                    self._json_response(200, {
                        "ok": True,
                        "message": "查询成功，无结果",
                        "elapsed": elapsed
                    })

        except Exception as e:
            logger.exception("查询执行异常")
            self._json_response(500, {"error": str(e)})

    def _json_response(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        # 静默静态文件日志，只记 API
        if "/api/" in (args[0] if args else ""):
            logger.info(fmt % args)


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9000
    directory = str(Path(__file__).parent)
    os.chdir(directory)
    server = HTTPServer(("", port), WorkbenchHandler)
    logger.info(f"工作台服务启动: http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("服务已停止")
        server.server_close()


if __name__ == "__main__":
    main()
