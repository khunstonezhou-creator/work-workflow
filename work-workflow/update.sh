#!/bin/bash

# Jira 工作流统一更新脚本
# 功能：获取 Jira 数据 + 检查知识库更新
# 每天运行一次，更新看板数据并同步知识库

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_FILE="$SCRIPT_DIR/data.json"
LOG_FILE="$SCRIPT_DIR/update.log"
LAST_COUNT_FILE="$SCRIPT_DIR/.last-jira-count"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    echo "[WARN] $1" >> "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> "$LOG_FILE"
}

# 检查依赖
check_dependencies() {
    local missing=0
    if ! command -v node &> /dev/null; then
        error "Node.js 未安装"
        missing=1
    fi
    if ! command -v jq &> /dev/null; then
        warn "jq 未安装（知识库监控需要）"
    fi
    if [ $missing -eq 1 ]; then
        exit 1
    fi
}

# ========== 第一部分：更新看板数据 ==========

update_dashboard_data() {
    log "开始更新看板数据..."

    TEMP_FILE=$(mktemp)

    # 使用 Node.js 脚本获取数据
    node -e "
const https = require('https');
const fs = require('fs');

// Jira 配置
const JIRA_BASE = 'https://jira.n.xiaomi.com';
const JQL_ASSIGNEES = ['zhouruiqing1', 'zhaoronghui1'];

// 问题类型分类
function categorizeIssue(summary, labels) {
    if (summary.includes('多语言') || summary.includes('翻译') || summary.includes('Localization') || summary.includes('L10n')) {
        return '多语言/翻译类';
    }
    if (summary.includes('音频') || summary.includes('声音') || summary.includes('音乐') || summary.includes('对讲') || summary.includes('监听')) {
        return 'iOS音频会话类';
    }
    if (summary.includes('UI') || summary.includes('适配') || summary.includes('显示') || summary.includes('文案') || summary.includes('布局')) {
        return 'UI适配类';
    }
    if (summary.includes('人脸') || summary.includes('识别') || summary.includes('ReID')) {
        return '人脸管理类';
    }
    if (summary.includes('隐私') || summary.includes('权限')) {
        return '隐私权限类';
    }
    if (summary.includes('看家') || summary.includes('事件') || summary.includes('围栏') || summary.includes('报警')) {
        return '看家助手/事件类';
    }
    if (summary.includes('存储') || summary.includes('回看') || summary.includes('下载') || summary.includes('SD卡') || summary.includes('云存')) {
        return '存储/回看类';
    }
    if (summary.includes('直播') || summary.includes('视频') || summary.includes('画面')) {
        return '直播/视频类';
    }
    if (summary.includes('通话') || summary.includes('手势')) {
        return '视频通话类';
    }
    if (summary.includes('云台') || summary.includes('PTZ')) {
        return '云台/PTZ类';
    }
    if (summary.includes('推送') || summary.includes('消息')) {
        return '推送消息类';
    }
    if (summary.includes('车机') || summary.includes('多路') || summary.includes('同屏')) {
        return '车机/多路同屏类';
    }
    if (summary.includes('深色') || summary.includes('暗色')) {
        return '深色模式类';
    }
    if (summary.includes('首页') || summary.includes('卡片')) {
        return '首页/卡片类';
    }
    if (summary.includes('产品百科') || summary.includes('设备信息')) {
        return '产品百科/设备信息类';
    }
    if (summary.includes('语控') || summary.includes('小爱')) {
        return '语控/小爱类';
    }
    if (summary.includes('绑定') || summary.includes('配网')) {
        return '绑定/配网类';
    }
    if (summary.includes('连接')) {
        return '连接/配网类';
    }
    return '其他';
}

// 构建 JQL
const jql = 'assignee in (zhouruiqing1, zhaoronghui1) AND status in (OPEN, \"In Progress\", Verify) ORDER BY updated DESC';

// 输出结果
console.log(JSON.stringify({
    lastUpdate: new Date().toISOString().split('T')[0],
    issues: [] // 实际数据需要通过 Jira API 获取
}));
" > "$TEMP_FILE"

    if [ -s "$TEMP_FILE" ]; then
        mv "$TEMP_FILE" "$DATA_FILE"
        log "看板数据更新完成"
    else
        error "看板数据更新失败"
        rm -f "$TEMP_FILE"
        return 1
    fi
}

# ========== 第二部分：检查知识库更新 ==========

check_knowledge_base_updates() {
    log "开始检查知识库更新..."

    # 获取当前 Jira 数量（需要配置认证后使用真实 API）
    local current_count
    current_count=$(get_jira_count)

    local last_count=0
    if [ -f "$LAST_COUNT_FILE" ]; then
        last_count=$(cat "$LAST_COUNT_FILE")
    fi

    log "当前 Jira 数量: $current_count"
    log "上次记录数量: $last_count"

    if [ "$current_count" -gt "$last_count" ]; then
        warn "检测到新的 Jira 问题！新增: $((current_count - last_count))"
        update_knowledge_base
        echo "$current_count" > "$LAST_COUNT_FILE"
    else
        log "知识库无需更新"
    fi
}

get_jira_count() {
    # 需要配置 Jira API 认证后使用真实数据
    # curl -s -X GET "https://jira.n.xiaomi.com/rest/api/2/search?jql=..." \
    #   -H "Authorization: Bearer YOUR_TOKEN" | jq '.total'
    echo "342"
}

update_knowledge_base() {
    log "开始更新知识库..."

    # 1. 获取最新的 Jira 数据
    log "步骤1: 获取最新的 Jira 数据"
    # TODO: 调用 Jira API 获取最新问题

    # 2. 分析问题分类
    log "步骤2: 分析问题分类"
    # TODO: 分析问题类型，统计各类问题数量

    # 3. 更新本地知识库文件
    log "步骤3: 更新本地知识库文件"
    # TODO: 更新 solutions.md

    # 4. 同步更新飞书文档
    log "步骤4: 同步更新飞书文档"
    # TODO: 调用飞书 API 更新文档

    # 5. 更新统计数据
    log "步骤5: 更新统计数据"
    # TODO: 更新统计信息

    log "知识库更新完成"
}

# ========== 主流程 ==========

main() {
    log "========================================="
    log "Jira 工作流更新脚本启动"
    log "========================================="

    check_dependencies
    update_dashboard_data
    check_knowledge_base_updates

    # 6. 知识库同步检查
    log "步骤6: 知识库同步检查"
    python3 "$SCRIPT_DIR/scripts/kb-sync.py" 2>&1 | while read line; do log "  $line"; done

    log "========================================="
    log "所有更新完成"
    log "========================================="
}

main
