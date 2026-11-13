# 本地增强说明（Local Additions）

本 fork 在原仓库 [xhwxt/zcode-token-usage-statusbar](https://github.com/xhwxt/zcode-token-usage-statusbar) 基础上新增了 3 个文件，**未修改任何原仓库文件**（`git diff` 为空），所有定制均为外挂形式，方便随时同步上游。

## 新增文件

### 1. `reinject_statusbar.py` — 状态条重注入驱动

ZCode 自动升级会覆盖 `app.asar`，导致状态条消失。本脚本调用原仓库的 `patch_install.py` 重新注入：

- 仓库路径自动推导（脚本所在目录），运行时数据目录自动指向 `~/.zcode/zcode-token-usage-statusbar`
- ZCode 不在默认安装位置时，改脚本内 `ASAR` 默认值或设环境变量 `ZUSAGE_ASAR`
- 测试模式：`ZUSAGE_DRYRUN=1 python reinject_statusbar.py`

### 2. `reinstall-statusbar.cmd` — 一键恢复入口

双击即可，依次完成两件事：

1. 重注入状态条（调用 `reinject_statusbar.py`）
2. 重打用量保留补丁（调用 `patch_usage_retention.py`，幂等，已打过自动跳过）

**ZCode 每次自动升级后，双击它一次即可全部恢复。** 桌面可为其建快捷方式。

### 3. `patch_usage_retention.py` — 用量统计保留补丁

ZCode 将本地用量三表（`db.sqlite` 中的 `model_usage` / `turn_usage` / `tool_usage`）硬编码为只保留 30 天：每次写入用量后立即执行 `delete from ... where started_at < now-30d`，无任何配置项，30 天前的逐请求用量被静默永久删除（详见 [zai-org/feedback#1299](https://github.com/zai-org/feedback/issues/1299)，截至 2026-11 官方仍未提供配置）。

本补丁修改 ZCode 桌面版运行时 `resources/glm/zcode.cjs` 中剪枝函数的默认截止时间：

```
t.beforeTime??Date.now()-<变量>   →   t.beforeTime??Date.now()-3155760000000
（默认删 30 天前用量）                （默认删 100 年前 = 永不自动清理）
```

- 只影响用量三表的**自动**清理；`beforeTime` 显式传参路径保留，其它行为（model-io 日志轮转、会话保留等）一律不动
- 用量三表体积极小（约 0.2MB/30 天），永久保留无压力
- 自动备份原文件为 `zcode.cjs.orig.bak`；打完补丁用 `node --check` 校验语法，失败自动还原
- 不写死混淆变量名（随版本变化），按结构化模式定位；结构变化时拒绝动手并提示人工复核

> **2026-11-12 更新：ZCode 3.18.2 已官方移除用量三表剪枝**（三表 DELETE 语句全部消失，实测数据库停止清理，#1299 诉求已实现）。
> 从该版本起无需补丁，脚本会自动识别并显示 `official-no-prune`；仅当未来版本重新引入剪枝时才会再次显示 `patchable`。
> 旧版 `zcode.cjs.orig.bak` 备份属于历史版本，`--restore` 会在"当前文件未打补丁"时拒绝执行以防止降级，确认无用后可手动删除。

```bash
python patch_usage_retention.py            # 打补丁（幂等，需重启 ZCode 生效）
python patch_usage_retention.py --check    # 只查看当前状态
python patch_usage_retention.py --restore  # 从备份还原官方默认行为
```

路径适配：ZCode / node 不在默认位置时，改脚本内默认值或设环境变量 `ZCODE_CJS_PATH`、`ZCODE_NODE_PATH`。

## 注意

- 两个补丁目标（`app.asar`、`zcode.cjs`）都在 ZCode 安装目录内，**升级必然覆盖**——重新双击 `reinstall-statusbar.cmd` 即可，原仓库文件永不丢失
- 补丁只改本机文件，用于个人数据保全；如官方后续提供保留期配置项（#1299 的诉求），请 `--restore` 还原并改用官方方案
