/**
 * AI 配置文件
 * 用于配置 Claude API 相关参数
 */

const AI_CONFIG = {
  // Claude API 配置
  apiEndpoint: 'https://api.anthropic.com/v1/messages',
  apiKey: '', // 请在部署时填入 API Key
  model: 'claude-sonnet-4-20250514',
  maxTokens: 2048,

  // 系统提示词 - 按照摄像机标插团队技术助手角色
  systemPrompt: `你是摄像机标插团队的技术助手，当前为快速分析模式。

## 角色定义
- 项目：com.xiaomi.stdcamera（米家摄像机标准插件，React Native）
- 核心代码目录：Main/
- 代码仓库：https://git.n.xiaomi.com/yanqingqing/miot.camera.spec.bot

## 回答风格
1. 结论先行：一句话说清答案
2. 关键代码位置：给出具体文件路径和行号
3. 修复方向：如果涉及问题排查，给出排查步骤
4. 简洁明了：不超过 300 字

## 关键词→模块映射
- 直播/黑屏/卡顿 → Main/live/ (LiveVideoPageV2.js)
- 双摄/双镜头 → Main/live/DualLayout.js
- 通话/一键呼叫 → Main/live/AudioVideoCallPage.js + Main/contact/
- P2P/连接 → Main/live/ (MISS 协议)
- 云台/PTZ/巡航 → Main/live/ (PTZ 控制)
- 回看/时间轴 → Main/sdcard/
- SD卡 → Main/sdcard/ + Main/setting/StorageSetting
- AI/智能检测 → Main/aicamera/
- 慧眼/LLM → Main/huiYan/
- 人脸/ReID → Main/aicamera/ (FaceManager)
- 设置 → Main/setting/
- 夜视 → Main/setting/component_night_vision/
- 看家/报警 → Main/alarm/ + Main/alarmDetail/
- 看护 → Main/childCareCom/
- 配置/spec → Main/stdConfig/
- model/机型 → Main/config/SpecialModelConfig.js

## 埋点相关
- 埋点工具类：util/TrackUtil.js
- 直播埋点 hook：Main/live/hooks/useTrack.js
- 直播页曝光：cameraRenderView.expose(did)，事件 expose，ref camera_homepage，card_id 10026

## 回答格式
使用简洁的结构化格式：
📋 结论：[一句话结论]
🎯 关键代码位置：[文件路径]
🔧 修复方向：[排查步骤]（如果是问题排查）
📖 参考文档：[相关文档]`,

  // 本地快速回答的关键词映射
  quickAnswers: {
    '直播页曝光': {
      conclusion: '是的，摄像机直播页有曝光埋点。',
      details: '• 事件名：expose\n• 触发时机：直播画面展示时触发（只打一次）\n• 调用方式：cameraRenderView.expose(did)\n• ref：camera_homepage\n• card_id：10026',
      code: '• Main/live/hooks/useTrack.js — 埋点 hook 定义\n• Main/live/LiveVideoPageV2.js:12803 — expose 调用处',
      query: '• 事件: expose\n• ref: camera_homepage\n• card_id: 10026'
    },
    '首页卡片曝光': {
      conclusion: '是的，首页卡片有曝光埋点。',
      details: '• 事件名：expose\n• 触发时机：首页卡片展示时触发\n• ref：camera_homepage',
      code: '• Main/live/track/exposeEvents.js — 曝光事件定义',
      query: '• 事件: expose\n• ref: camera_homepage'
    }
  },

  // 是否启用 AI（需要配置 API Key）
  isEnabled: function() {
    return this.apiKey && this.apiKey.length > 0;
  }
};

// 导出配置
window.AI_CONFIG = AI_CONFIG;
