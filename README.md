# 露米 Lumi · Pet / Mini

将露米的原生宠物素材、动画制作流程、mini 陪伴应用和历史设计整合到一个独立 Git 项目。项目包含可在本地运行的 Node 服务和浏览器页面，以及 MCP 工具接口。

## 启动

需要 Node.js 22+。Python 3.10+ 和 Pillow 用于素材处理、校验和安装。

```sh
npm ci
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
npm start
```

浏览器打开 <http://127.0.0.1:8787/preview>。页面加载最新 v3 动画，默认挥手后待机；悬停精灵会转圈跳，点击精灵会挥手。专注按钮切换安静模式。

MCP 地址为 `http://127.0.0.1:8787/mcp`。`show_lumi` 支持：

- `mode`：`companion`、`focus`、`comfort`。
- `message`：最多 100 个字符。
- `action`：`idle`、`running-right`、`running-left`、`waving`、`jumping`、`failed`、`waiting`、`running`、`review`。

画中画、对话建议和关闭卡片调用宿主提供的能力。本地预览能检查动画和模式切换；完整宿主交互需要兼容的 MCP App 宿主。本次整合没有创建公网部署或注册云端应用，也未进行云端宿主验证。

可复制 `.env.example` 为 `.env` 修改监听地址与端口。默认只监听本机。

## 目录

```text
apps/mini/                    mini 应用：Node / MCP 服务与页面
assets/pets/lumi-actions-v3/   当前成品：pet.json、精灵图、预览、回退素材
assets/pets/lumi-actions-v2/   上一版素材，供合成与保留性检查
assets/pets/lumi/              初版成品与历史安装入口
workflows/lumi-actions-v3/    当前切帧、合成脚本、源图、动作帧与 QA
workflows/lumi-actions-v2/    上一版制作记录
workflows/lumi-pet-run/       初版制作记录，含 16 个视线方向
tools/                        可移植校验与原生安装工具
reference/host/               原宿主的检查材料，非本项目运行代码
designs/                     历史设计稿
tests/                       服务接口与安装回退测试
docs/                        迁移清单与验证说明
```

所有依赖统一在项目根目录安装和锁定；`apps/mini` 是 npm workspace。历史源图、提示词、动作帧和 QA 都纳入 Git。`node_modules`、Python 虚拟环境、个人环境变量不纳入 Git。

## 素材制作与校验

```sh
npm run pet:validate
npm run pet:build
npm run pet:validate
```

`pet:build` 将 `workflows/lumi-actions-v3/frames/jumping/` 合入 v2 图集，只替换跳跃行。9 类动作和 16 个视线方向已经包含在成品里。`pet:extract` 从现有 `decoded/jumping.png` 重新切出跳跃帧，运行前应保留修改记录。

校验包含尺寸、透明通道、9 类动作帧、16 个视线方向以及上一版保留行；还会核对视觉审核记录中的 SHA-256。修改图集后需要重新做视觉审核并更新 `workflows/lumi-actions-v3/qa/package-check.json`，不能只把校验标记改为通过。

项目提供已有素材的处理流程；重新生成 AI 源图需要另行使用图像生成工具，提示词已经保留。

## 安装原生 Pet

先只检查安装目标：

```sh
npm run pet:install -- --dry-run
```

确认后安装：

```sh
npm run pet:install
```

默认目标为 `${CODEX_HOME:-~/.codex}/pets/lumi`，也可以用 `--dest /path/to/lumi` 指定其他目标。更新已有 Lumi 时会将整个旧目录备份到目标父目录的 `.lumi-backups/`，替换失败会恢复旧目录。备份目录对应当前安装环境，不在项目 Git 中。

本次项目整合没有执行真实宠物安装。历史成品目录里的旧安装入口保留作记录，日常使用根目录的 `pet:install`。

## 验证

```sh
npm test
npm run pet:validate
```

测试覆盖 MCP 初始化、工具调用与参数校验、HTML 资源读取，以及安装、备份、失败回退、dry-run 和拒绝覆盖其他宠物。已有素材的视觉审核见 `workflows/lumi-actions-v3/qa/`。迁移和本次验证说明见 [docs/MIGRATION.md](docs/MIGRATION.md)。
