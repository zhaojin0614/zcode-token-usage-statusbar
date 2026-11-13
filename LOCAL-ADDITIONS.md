# 本地增强说明（Local Additions）

本 fork 在原仓库 [xhwxt/zcode-token-usage-statusbar](https://github.com/xhwxt/zcode-token-usage-statusbar) 基础上新增了 2 个文件，**未修改任何原仓库文件**（`git diff` 为空），所有定制均为外挂形式，方便随时同步上游。

## 新增文件

### 1. `reinject_statusbar.py` — 状态条重注入驱动

ZCode 自动升级会覆盖 `app.asar`，导致状态条消失（原项目 README 同样说明：升级后需重跑 install）。本脚本调用原仓库的 `patch_install.py` 重新注入：

- 仓库路径自动推导（脚本所在目录），运行时数据目录自动指向 `~/.zcode/zcode-token-usage-statusbar`
- ZCode 不在默认安装位置时，改脚本内 `ASAR` 默认值或设环境变量 `ZUSAGE_ASAR`
- 测试模式：`ZUSAGE_DRYRUN=1 python reinject_statusbar.py`

### 2. `reinstall-statusbar.cmd` — 一键恢复入口

双击即可重新注入状态条（调用 `reinject_statusbar.py`）。**ZCode 每次自动升级后，双击它一次即可恢复。** 桌面可为其建快捷方式。

## 历史记录：用量保留补丁（已退役）

2026-11 上旬曾在本 fork 中加入 `patch_usage_retention.py`，用于绕过 ZCode 旧版对本地用量三表（`model_usage` / `turn_usage` / `tool_usage`）的 30 天硬编码剪枝（[zai-org/feedback#1299](https://github.com/zai-org/feedback/issues/1299)）。

**2026-11-12 发布的 ZCode 3.18.2 已官方移除该剪枝**（三表 DELETE 语句全部消失，实测数据库停止清理），补丁脚本因此退役并删除。若未来版本重新引入剪枝，可从 git 历史取回脚本：

```bash
git log --all --oneline -- patch_usage_retention.py   # 找到含该文件的提交
git checkout <commit> -- patch_usage_retention.py     # 取回（后续提交 97a07fe 为最终版）
```

## 注意

- 注入目标 `app.asar` 在 ZCode 安装目录内，**升级必然覆盖**——重新双击 `reinstall-statusbar.cmd` 即可，原仓库文件永不丢失