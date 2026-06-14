# 🚀 个人工作台 - AI 辅助 Jira 问题管理与知识库

> 让 AI 承担"信息检索、分类判断、方案推荐"等重复性工作，人专注于"决策、沟通、验证"。

![工作台截图](screenshot.png)

## ✨ 功能特性

- 📋 **Jira 智能处理** — 自动分类 18 类问题、推荐解决方案、生成周报
- 📚 **知识库管理** — 170+ 篇飞书文档索引、实时搜索、自动同步
- 📊 **数据看板** — 问题分类、月度发版、全量筛选
- 📝 **周报自动生成** — 极简版一键复制、详细版含操作时间线
- 🔗 **外部平台接入** — 数据分析、设计方案、需求管理

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────┐
│                    个人工作台 (index.html)             │
├──────────┬──────────┬──────────┬──────────┬──────────┤
│ 📚 知识库 │ 📋 Jira  │ 📝 文档  │ 📊 需求  │ ⚙️ 其他  │
├──────────┴──────────┴──────────┴──────────┴──────────┤
│                    数据层 (JSON)                      │
├──────────┬──────────┬──────────┬─────────────────────┤
│ Jira API │ 飞书 MCP │ 数据工场 │  本地知识库          │
└──────────┴──────────┴──────────┴─────────────────────┘
```

## 🚀 快速开始

### 1. 配置

编辑 `config.json`：

```json
{
  "team": {
    "name": "你的团队",
    "members": ["你的名字"]
  },
  "jira": {
    "jql": "assignee in (你的名字) AND status in (OPEN, \"In Progress\", Verify)"
  }
}
```

### 2. 配置 MCP

在 Claude Desktop 中配置 Jira 和飞书 MCP。

### 3. 启动

```bash
python3 -m http.server 9000
```

访问 http://localhost:9000

详细步骤见 [SETUP.md](SETUP.md)

## 📁 目录结构

```
work-workflow/
├── config.json           # 用户配置
├── index.html            # 工作台页面
├── update.sh             # 每日更新脚本
├── boards/               # Jira 数据
├── knowledge-base/       # 知识库
│   ├── solutions.md      # 解决方案沉淀
│   └── docs-index.json   # 飞书文档索引
└── scripts/              # 工具脚本
```

## 📖 使用指南

### Jira 处理
1. 点击左侧「📋 Jira 处理」
2. 查看自动分类的问题列表
3. 点击「建议」获取 AI 推荐的处理方案
4. 一键复制周报

### 知识库
1. 点击左侧「📚 知识库」
2. 搜索关键词或 Jira 编号
3. 浏览 24 个分类的文档索引
4. 点击标题跳转飞书原文

### 添加知识库文档
在 Claude 中说：
```
请帮我把这些飞书文档添加到知识库：
https://mi.feishu.cn/docx/xxx
https://mi.feishu.cn/docx/yyy
```

## 🚀 部署方式

### Git 部署（推荐）

```bash
# 1. 克隆项目
git clone <repo-url>
cd work-workflow

# 2. 一键部署
bash deploy.sh

# 3. 启动服务
cd /opt/work-workflow
python3 auth_server.py 9000
```

### 访问控制

| 角色 | 权限 |
|------|------|
| 管理员 | 登录、使用工作台、管理用户（审批/拒绝） |
| 普通用户 | 登录、使用工作台（需管理员审批） |
| 未注册 | 只能访问登录/注册页面 |

**管理员账号**: `admin` / `admin123`（首次部署后请修改密码）

**用户注册流程**:
1. 用户访问工作台，点击「注册」
2. 输入用户名和密码，提交注册
3. 管理员在 `/admin` 后台审批通过
4. 用户登录即可使用

**管理员后台**: `http://your-server:9000/admin`

### 其他部署方式

- **GitHub Pages**: push 后自动部署（需配置 GitHub Actions）
- **Vercel**: `npx vercel --prod`
- **systemd**: 使用 `work-workflow.service` 配置系统服务

详细步骤见 [SETUP.md](SETUP.md)

## 🔧 技术栈

- **前端**: 纯 HTML/CSS/JS，无框架依赖
- **认证**: Python HTTP 服务器 + 会话管理
- **数据**: JSON 文件，通过 MCP 工具更新
- **自动化**: macOS LaunchAgent / Linux Cron

## 📄 License

MIT
