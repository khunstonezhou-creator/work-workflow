# 个人工作台 - 部署指南

## 快速开始

### 1. 克隆项目

```bash
git clone <repo-url>
cd work-workflow
```

### 2. 配置你的信息

编辑 `config.json`，修改以下内容：

```json
{
  "team": {
    "name": "你的团队名称",
    "members": ["你的名字", "同事名字"],
    "defaultMembers": ["你的名字"]
  },
  "jira": {
    "baseUrl": "https://jira.n.xiaomi.com/browse/",
    "jql": "assignee in (你的名字) AND status in (OPEN, \"In Progress\", Verify)"
  }
}
```

### 3. 配置 MCP 工具

#### 3.1 Jira MCP

在 Claude Desktop 配置文件中添加：

```json
{
  "mcpServers": {
    "mi-jira": {
      "type": "http",
      "url": "https://mcp.jira.cn/mcp/your-jira-mcp-url"
    }
  }
}
```

#### 3.2 飞书 MCP

```json
{
  "mcpServers": {
    "mi-feishu": {
      "type": "http",
      "url": "https://mcp.feishu.cn/mcp/your-feishu-mcp-url"
    }
  }
}
```

### 4. 上传知识库

将你的飞书文档链接整理到 `knowledge-base/docs-index.json`：

```json
{
  "categories": {
    "你的分类1": {
      "icon": "📄",
      "description": "分类描述",
      "docs": [
        {
          "id": "飞书文档ID",
          "title": "文档标题",
          "type": "docx",
          "summary": "文档摘要"
        }
      ]
    }
  }
}
```

或使用 Claude 自动导入：
```
请帮我把这些飞书文档添加到知识库：
https://mi.feishu.cn/docx/xxx
https://mi.feishu.cn/docx/yyy
```

### 5. 启动服务

```bash
# 本地启动
python3 -m http.server 9000

# 或使用 API 服务（支持 SQL 查询）
source data-sql/venv/bin/activate
python3 api_server.py 9000
```

访问 http://localhost:9000

---

## 部署到线上

### 方案一：GitHub Pages（推荐）

1. 将项目推送到 GitHub
2. 在 Settings > Pages 中启用
3. 访问 `https://your-username.github.io/work-workflow/`

### 方案二：Vercel

```bash
npx vercel --prod
```

### 方案三：公司内网服务器

```bash
# 使用 systemd 管理服务
sudo cp work-workflow.service /etc/systemd/system/
sudo systemctl enable work-workflow
sudo systemctl start work-workflow
```

---

## 自动化更新

### macOS LaunchAgent

```bash
cp com.xiaomi.jira-workflow.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.xiaomi.jira-workflow.plist
```

### Linux Cron

```bash
crontab -e
# 添加：每天 09:00 更新
0 9 * * * /path/to/update.sh
```

---

## 目录结构

```
work-workflow/
├── config.json              # 配置文件（修改这个）
├── index.html               # 工作台主页面
├── api_server.py            # API 服务（可选）
├── update.sh                # 每日更新脚本
├── SETUP.md                 # 本文件
├── boards/                  # 数据文件
│   ├── category-data.json   # 分类数据
│   ├── all-issues-data.json # 全部问题
│   ├── monthly-data.json    # 月度发版
│   ├── activity-data.json   # 操作记录
│   ├── kb-pending.json      # 知识库待处理
│   └── data-index.json      # 数据索引
├── knowledge-base/          # 知识库
│   ├── solutions.md         # 解决方案沉淀
│   ├── docs-index.json      # 飞书文档索引
│   └── *.md                 # 其他知识库文件
├── scripts/
│   └── kb-sync.py           # 知识库同步脚本
└── data-sql/                # 数据查询工具（可选）
```

---

## 常见问题

### Q: 如何添加新的问题分类？
编辑 `config.json` 中的 `jira.categories` 数组。

### Q: 如何更新知识库文档索引？
在 Claude 中说：「请帮我把这些飞书文档添加到知识库」然后粘贴链接。

### Q: 如何修改周报格式？
编辑 `index.html` 中的 `generateReport()` 函数。

### Q: 数据更新频率？
默认每天 09:00 自动更新，可在 `update.sh` 中修改。
