# 露米 Lumi · Codex App 原生 Pet / Mini 项目

这个项目维护能够安装到 Codex App **Settings → Mini & Pets → My pets** 的原生自定义宠物包。安装后选择 **露米 Lumi · 项目版**，由现有 App 的 Mini 浮窗展示并驱动动画。

主入口是 `lumi.py`，网页/MCP 组件已经收纳到 `legacy/`，不参与原生安装。

## 安装到你截图中的列表

需要 Python 3.10+ 和 Pillow；原生接入已在本机 `com.openai.codex` 版本 `26.1007.30912` 的加载器上检查。

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 lumi.py doctor
python3 lumi.py install
```

也可以双击根目录 **安装到Codex.command**。它优先使用项目的 Python 虚拟环境。

安装之后：

1. 打开 **Settings → Mini & Pets**。
2. 点击 **My pets** 右侧的刷新图标。
3. 选择 **露米 Lumi · 项目版**。原来的 **露米 Lumi** 会保留。
4. 用 **Show Mini** 或 **Option+Space** 显示/聚焦原生 Mini；已有 Mini 可继续使用。

安装目标默认为 `${CODEX_HOME:-~/.codex}/pets/lumi-project-<版本指纹>`。版本指纹来自精灵图 SHA-256，新素材会创建新版本条目；相同素材重复安装会直接返回已安装。

本项目安装器只写入自定义宠物目录。刷新和选择通过宿主设置完成；安装器不会替用户更改宿主的账户选择、缓存或应用二进制。

## Mini 与 Pet 的关系

| 部分 | 负责方 |
| --- | --- |
| 角色素材、9 类动作、16 个视线方向 | 本项目 |
| 原生包构建、安装、验证、导出、恢复 | 本项目 |
| 桌面浮窗、Quick Chat、语音、活动列表、状态驱动 | Codex App 宿主 |
| Mini 的无宠物模式、拖拽、大小、快捷键 | Codex App 宿主设置 |

这是接入现有 App 的原生宠物扩展工程。Mini 的宿主功能直接复用 App；本项目没有实现另一套聊天窗口。官方操作说明见 [Pets](https://learn.chatgpt.com/docs/pets)，本机包格式与版本检查见 [native/README.md](native/README.md)。

## 开发与发布

```sh
# 校验当前素材与已有视觉审核
python3 tools/validate_pet.py

# 从 v2 图集和当前跳跃帧重新合成 v3
python3 workflows/lumi-actions-v3/compose_package.py

# 同步并验证原生包
python3 tools/build_native.py

# 导出可搬运的原生宠物 ZIP 包
python3 lumi.py export

# 查看宿主和安装状态
python3 lumi.py doctor
python3 lumi.py status
```

当前图集是 1536 × 2288 RGBA WebP，包含 9 类动作和 16 个视线方向。视觉素材沿用原有 v3 成品。修改图集后应重新完成视觉 QA，更新审核记录，再构建原生包；校验会拒绝未经审核的图集。

导出的 ZIP 包位于 `dist/`，含版本目录与 `pet.json`、`spritesheet.webp`。ZIP 是搬运包，不能假设宿主设置支持直接导入 ZIP：解压到目标机器 `CODEX_HOME/pets`，或在该机器运行本项目安装器。

## 备份、回退与卸载

```sh
# 只查看将要安装的位置
python3 lumi.py install --dry-run

# 指定另一套 Codex 用户目录
python3 lumi.py install --pets-root /path/to/codex/pets

# 重新部署当前版本，保留旧目录完整备份
python3 lumi.py install --force

# 将当前项目版本移到可恢复的备份目录
python3 lumi.py uninstall

# 用命令输出中的备份路径恢复
python3 lumi.py restore /path/to/pets/.lumi-backups/BACKUP_NAME
```

备份保存在目标宠物目录的 `.lumi-backups/`，带独立恢复记录和文件指纹。恢复会核验备份完整性。安装与卸载都只处理当前项目版本，保留之前的 `lumi` 以及其他版本。

宿主可能缓存或迁移已选宠物；如果选择后仍显示旧素材，请刷新并确认选中的是本次安装的项目版本。项目不操作宿主的云端迁移映射。

## 目录

```text
lumi.py                       原生部署与管理 CLI
安装到Codex.command            macOS 安装入口
native/lumi-project/          可安装原生包
native/project.json           项目与宿主配置
assets/pets/                  初版、v2、v3 成品与历史预览
workflows/                    源图、提示词、切帧、合成、历史 QA
tools/                       构建、校验、安装与恢复工具
tests/                       原生包与部署生命周期测试
docs/                        迁移记录和原生接入说明
reference/host/              历史宿主检查材料
legacy/chatgpt-mcp-widget/    之前的网页/MCP 实验，独立运行
designs/                     历史设计稿
```

## 检查

```sh
python3 -m unittest discover -s tests -p 'test_*.py'
python3 lumi.py doctor
```

测试覆盖原生包发现契约、安装幂等性、旧版保留、导出、备份、恢复、失败回退和损坏备份拒绝。宿主读取格式经本机静态代码检查；刷新后实际选择新条目属于 App 内步骤。

Git 已初始化，原工程完整收纳并保留来源清单。原始目录仍保留作为备份。无需运行 Node 服务即可安装到原生 Mini & Pets。
