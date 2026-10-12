# 原生 Mini & Pets 接入

目标由用户确认：接入现有 Codex App 的原生 Mini & Pets，安装到用户截图中的 My pets 列表。2026-10-12 起，项目主线改为原生宠物扩展包。

## 接入契约

本机宿主路径 `/Applications/ChatGPT.app`，Bundle ID `com.openai.codex`，版本 `26.1007.30912`。宿主二进制被只读检查，没有替换、注入或修改。

加载器从 `CODEX_HOME/pets` 扫描子目录，解析 `pet.json` 并读取本目录中的精灵图。目录名形成 `custom:<目录名>`；v2 图集要求 1536 × 2288。具体检查位置为已安装 `app.asar` 的 `.vite/build/src-BJv5Mk7n.js`，由 `doctor` 动态查找，不依赖固定构建文件名。

这项检查只能证明本机加载器的本地包接受契约，不能代替宿主 UI 中的刷新、选择或在线迁移验证。公开操作流程参考 [官方 Pets 文档](https://learn.chatgpt.com/docs/pets)。

## 工程范围

项目负责源素材、提示词、制作记录、原生包、安装器、导出、结构/像素校验与恢复。Mini 窗口、聊天、语音、任务活动、拖拽、大小和快捷键由已安装宿主负责。自定义宠物包没有执行脚本的入口，不把历史网页应用注册为原生 Mini。

主原生包为 `native/lumi-project`，显示名 **露米 Lumi · 项目版**。安装目录包含素材指纹，以便与既有露米条目及宿主可能缓存/迁移的版本区分。项目不会改动账户或云端迁移映射。

本次重新建立的是完整的原生宠物维护与部署工程，角色图像沿用已审核 v3，不宣称重新生成了视觉内容。

## 使用与验证

```sh
python3 lumi.py doctor
python3 lumi.py install
python3 lumi.py status
python3 lumi.py export
```

首次安装新项目版本后，在 **Mini & Pets** 的 **My pets** 点击刷新并选择 **露米 Lumi · 项目版**。

自动化工具拒绝操作 `com.openai.codex` 原生窗口，因此本次不进行程序化设置点击。用户提供的截图确认了宿主界面与旧 Lumi 条目；新条目的最终选择需要用户在同一设置页完成。
