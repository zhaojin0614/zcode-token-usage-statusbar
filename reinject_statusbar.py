# -*- coding: utf-8 -*-
"""ZCode Token 状态条重装驱动。

用途: ZCode 自动升级覆盖 app.asar 导致状态条消失后, 重新注入。
用法: 双击同目录的 reinstall-statusbar.cmd (桌面快捷方式也指向它), 或命令行运行:
     python reinject_statusbar.py
环境变量 ZUSAGE_DRYRUN=1 时只打印将执行的动作, 不实际注入(测试用)。
路径适配: ZCode 未装在默认位置时, 修改下方 ASAR 默认值或设环境变量 ZUSAGE_ASAR。
"""
import os
import sys
from pathlib import Path

# 目标 asar: 默认 D 盘安装位置, 换机器请改这里或设环境变量 ZUSAGE_ASAR
ASAR = Path(os.environ.get(
    "ZUSAGE_ASAR",
    r"D:\APPS\ZCode\resources\app.asar",
))
# 仓库目录 = 本脚本所在目录(自动推导); 运行时数据目录 = ~/.zcode/zcode-token-usage-statusbar
PLUGIN = Path(__file__).parent.resolve()
DATA = Path.home() / ".zcode" / "zcode-token-usage-statusbar"

if os.environ.get("ZUSAGE_DRYRUN"):
    print("[dry-run] 将执行: set_runtime(%s); set_target(%s); install()" % (DATA, ASAR))
    print("[dry-run] 实际安装会: 重打包 asar -> 尝试原子替换(运行中被占用则生成 .tmp 并弹监控窗口)")
    sys.exit(0)

sys.path.insert(0, str(PLUGIN))
os.chdir(PLUGIN)

# 说明: patch_install.py 独立运行时 Windows 默认路径硬编码为作者机器的
# D:\ZCode\resources\app.asar, 且不解析 --asar 参数;
# 必须像 install.py 那样调用 set_runtime()+set_target() 显式改指目标, 再执行 install()。
import patch_install as P  # noqa: E402

P.set_runtime(DATA)   # 运行时目录 -> 数据目录副本(loader/注入行随动)
P.set_target(ASAR)    # 目标 asar -> 本机真实安装位置
ok = P.install(finalize=False)
print()
print("install() 返回:", ok,
      "(True=已注入完成, 重启 ZCode 即可; False=已生成待替换文件, 完全退出 ZCode 后由监控窗口自动收尾)")
