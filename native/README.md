# Codex App 原生包

`lumi-project/` 是可被现有 App 发现的自定义宠物包，目录中只需要 `pet.json` 和 `spritesheet.webp`。

本项目读取已安装的 `com.openai.codex` 宿主加载器确认：宿主扫描 `CODEX_HOME/pets` 下的子目录，使用目录名形成 `custom:<目录名>`，读取 `pet.json` 中的显示名与精灵图路径。`spriteVersionNumber: 2` 对应 1536 × 2288 的图集。

安装工具使用 `lumi-project-<精灵图SHA256前12位>` 作为目录名。因此相同素材重复安装保持相同条目，素材变化会形成新条目，便于与旧版和宿主中已经缓存/迁移的条目区分。包内 `id` 是项目标识；宿主实际选择 ID 取决于安装目录名。

`project.json` 是本项目的构建配置，不交给宿主读取。精灵图二进制保持与原 v3 素材一致；这次重建的是工程和原生部署流程，并没有重新生成角色。

Mini 浮窗、聊天输入、语音、任务状态、拖拽和快捷键由现有 App 实现。本地宠物包用于给这些原生功能提供角色图集，不提供可执行 JavaScript，也不通过网页/MCP 组件接入。

官方使用流程参考：[Pets](https://learn.chatgpt.com/docs/pets)。具体本地图集格式来自本机安装版本的只读代码检查，不应视作公开、永久稳定的扩展 API；App 升级后可重新运行 `python3 lumi.py doctor` 检查。
