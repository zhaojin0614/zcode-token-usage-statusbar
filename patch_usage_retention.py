# -*- coding: utf-8 -*-
"""ZCode 用量统计保留期补丁（usage retention patch）。

背景: ZCode 把 ~/.zcode/cli/db/db.sqlite 的 usage 三表(model_usage/turn_usage/tool_usage)
硬编码为只保留 30 天——每次写入用量后立即执行 delete from ... where started_at < now-30d,
用户无法配置或关闭, 30 天前的逐请求用量被静默永久删除(参见 zai-org/feedback#1299)。

本补丁把剪枝默认截止时间从 "now-30天" 改为 "now-100年":
  - 剪枝函数仍保留 beforeTime 显式传参能力(官方若有"手动清理用量"功能不受影响);
  - 用量三表从此不再被自动清理, 其它行为(session/part 保留、model-io 轮转等)一律不动;
  - 用量三表极小(实测 30 天约 0.2MB), 长期保留无体积压力。

用法: python patch_usage_retention.py            # 打补丁(幂等, 自动备份, node --check 校验)
      python patch_usage_retention.py --check    # 只检查当前状态, 不修改
      python patch_usage_retention.py --restore  # 从备份还原原始文件
"""
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ZCode 桌面版运行时位置: 换机器/安装位置请改默认值或设环境变量 ZCODE_CJS_PATH
ZCODE_CJS = Path(os.environ.get(
    "ZCODE_CJS_PATH",
    r"D:\APPS\ZCode\resources\glm\zcode.cjs",
))
# node 仅用于打补丁后的语法校验, 缺失时自动跳过; 可用环境变量 ZCODE_NODE_PATH 指定
NODE = Path(os.environ.get(
    "ZCODE_NODE_PATH",
    r"D:\APPS\NodeJs\node.exe",
))

# 100 年(毫秒): 作为剪枝默认截止偏移, 等效于"永不清理"
CENTURY_MS = "3155760000000"

# 结构化匹配: 剪枝函数默认值 "t.beforeTime??Date.now()-<混淆变量名>"。
# 不写死混淆名(RCs/DCs 等), 版本更新改名后仍能定位。
PATTERN = re.compile(r"(t\.beforeTime\?\?Date\.now\(\)-)([A-Za-z_$][\w$]*)")
MARKER = CENTURY_MS  # 已打补丁的判定标记


def check_running():
    """检测 ZCode 是否正在运行(仅提示, 补丁本身写入不受锁影响)。"""
    try:
        out = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq ZCode.exe"],
            capture_output=True, timeout=10,
        ).stdout.decode("gbk", "replace")
        return "ZCode.exe" in out
    except Exception:
        return False


def status(data_text):
    if MARKER in data_text:
        return "patched"
    if PATTERN.search(data_text):
        return "patchable"
    return "unknown"


def main():
    argv = sys.argv[1:]
    do_restore = "--restore" in argv
    check_only = "--check" in argv

    if not ZCODE_CJS.exists():
        print(f"[X] 未找到运行时文件: {ZCODE_CJS}")
        print("    若 ZCode 更换了安装目录, 请修改本脚本顶部的 ZCODE_CJS。")
        return 1

    data = ZCODE_CJS.read_bytes()
    text = data.decode("utf-8", "replace")
    st = status(text)

    if do_restore:
        bak = ZCODE_CJS.with_name(ZCODE_CJS.name + ".orig.bak")
        if not bak.exists():
            print(f"[X] 没有备份文件: {bak}")
            return 1
        shutil.copy2(bak, ZCODE_CJS)
        print(f"[OK] 已从备份还原: {bak} -> {ZCODE_CJS}")
        print("     重启 ZCode 后恢复官方默认行为(30 天清理)。")
        return 0

    print(f"目标: {ZCODE_CJS}")
    print(f"状态: {st}" + ("(已打补丁)" if st == "patched" else ""))
    if st == "unknown":
        print("[X] 未定位到剪枝默认值 (t.beforeTime??Date.now()-<var>)。")
        print("    ZCode 版本结构可能已变化, 请人工复核后再处理。")
        return 1
    if st == "patched":
        print("[OK] 用量三表已是无限制保留, 无需操作。")
        return 0
    if check_only:
        print("[--] 当前为官方默认(30 天清理), 尚未打补丁。")
        return 0

    # ---- 执行补丁 ----
    running = check_running()
    if running:
        print("[!] 检测到 ZCode 正在运行: 补丁可以写入, 但需完全退出并重启 ZCode 后生效。")

    m = PATTERN.search(text)
    old_expr = m.group(0)
    new_expr = m.group(1) + MARKER
    print(f"补丁点: {old_expr}  ->  {new_expr}")

    bak = ZCODE_CJS.with_name(ZCODE_CJS.name + ".orig.bak")
    if not bak.exists():
        shutil.copy2(ZCODE_CJS, bak)
        print(f"备份: {bak}")
    else:
        print(f"备份已存在, 保留原备份: {bak}")

    patched = PATTERN.sub(lambda mm: mm.group(1) + MARKER, text, count=1)
    tmp = ZCODE_CJS.with_name(ZCODE_CJS.name + ".patch.tmp")
    tmp.write_bytes(patched.encode("utf-8"))

    try:
        tmp.replace(ZCODE_CJS)
    except PermissionError:
        print(f"[!] 原文件被占用, 已生成待替换文件: {tmp}")
        print("    请完全退出 ZCode(托盘右键退出)后重新运行本脚本完成替换。")
        return 2

    # ---- 校验 ----
    ok = True
    if NODE.exists():
        r = subprocess.run([str(NODE), "--check", str(ZCODE_CJS)],
                           capture_output=True, text=True, timeout=60)
        ok = r.returncode == 0
        print("node --check:", "通过" if ok else "失败\n" + (r.stderr or "")[:800])
    else:
        print("(未找到 node, 跳过语法校验)")

    if not ok:
        shutil.copy2(bak, ZCODE_CJS)
        print("[X] 语法校验失败, 已从备份还原原始文件。")
        return 1

    # 确认替换成功后清理 tmp(replace 失败时 tmp 仍保留待人工处理)
    if tmp.exists():
        tmp.unlink(missing_ok=True)
    print("[OK] 补丁完成: 用量三表(model_usage/turn_usage/tool_usage)不再自动清理。")
    print("     重启 ZCode 生效; 更新后如被覆盖, 重跑本脚本或'重装状态条'快捷方式即可。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
