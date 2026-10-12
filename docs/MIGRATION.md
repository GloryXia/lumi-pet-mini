# 项目整合记录

整合日期：2026-10-12。

原目录 `/Users/xiachao/Documents/Codex/2026-09-28/yi` 保留，新的开发目录为 `/Users/xiachao/Desktop/developer/code/lumi-pet-mini`。

| 原目录 | 新目录 |
| --- | --- |
| work/lumi-chatgpt-app | legacy/chatgpt-mcp-widget |
| work/lumi-actions-v3 | workflows/lumi-actions-v3 |
| work/lumi-actions-v2 | workflows/lumi-actions-v2 |
| work/lumi-pet-run | workflows/lumi-pet-run |
| work/pet-inspect、根目录宿主检查脚本 | reference/host |
| outputs/pets | assets/pets |
| outputs/designs | designs |

逐文件来源和原始 SHA-256 见 `migration.json`。共收纳 496 个源文件；不复制 `node_modules` 与 `.DS_Store`。原应用已移到 legacy/chatgpt-mcp-widget，保留独立依赖与锁文件。原生项目使用 Python，无需 Node 服务。继承报告中的旧机器路径转换为项目相对路径；这些报告仍属于历史审核记录。

初次整合记录（后续原生工程更正见文末）：

- 根目录统一启动、依赖、环境变量示例、Python 依赖和 Git 忽略规则。
- mini 使用最新 v3 图集，支持待机、悬停跳跃、点击挥手，并接受 MCP 动作参数。
- 素材脚本使用项目相对路径；安装器使用用户目录或指定目标，保留完整旧包并支持失败回退。
- 保留原宿主检查材料和历史版本，使用 README 标明用途。

验证结果：

- Node.js 22.22.1 下依赖安装成功；MCP 与页面资源集成测试通过。
- Python 3.14.3 / Pillow 12.2.0 下安装、备份、失败回退、dry-run、身份检查测试通过。
- 合成脚本可从新目录执行；生成的 v3 精灵图与原成品 SHA-256 一致：`cbc4f4d44ce3c4e1036c0b9fa354b20a7e59591b37e7957f9691677f1d89154d`。
- 图集结构、9 类动作、16 个视线方向和保留行检查通过。
- 496 个来源文件都有目标记录，全部图片与 GIF 的原始字节保持一致。
- 本地浏览器中动画显示正常，专注/唤回交互正常，无浏览器错误日志。历史网页运行截图已移至 `legacy/chatgpt-mcp-widget/preview.png`。

尚未验证云端宿主中的画中画、发送对话建议和卡片关闭；这些功能取决于宿主环境。本次没有发布、配置远程 Git 仓库或替换本机已安装宠物。

## 原生工程更正

用户确认目标为 Codex App 设置页的 Mini & Pets 原生接入。网页组件移至 legacy。新增 native 原生包、lumi.py 管理入口、安装到Codex.command、宿主契约检查、版本化安装、ZIP 导出、备份恢复和原生生命周期测试。项目主说明已重写，接入边界和验证方式见 NATIVE-INTEGRATION.md。

## 1.1.0 跑动优化

内置 image_gen 重绘左右方向，并经过一次针对步态、留白和末帧收势的修订。构建逻辑现在按 native/project.json 指向当前素材包和工作流程；新增 v4 源图、提示词、对齐切帧、按原生时长编码的预览与逐像素保留检查。历史版本、转圈及 16 个视线方向均保留。原生 App 二进制未修改。
