@echo off
chcp 65001 >nul
title ZCode Token 状态条 - 重装注入
setlocal
rem PYTHON 路径按自己机器修改; 找不到时会回退到 PATH 里的 python
set "PYTHON=D:\APPS\Python\python.exe"
if not exist "%PYTHON%" set "PYTHON=python"

echo ==================================================
echo   ZCode Token 状态条 - 重装注入
echo   适用场景: ZCode 自动升级后状态条消失
echo ==================================================
echo.

"%PYTHON%" "%~dp0reinject_statusbar.py"

echo.
echo --------------------------------------------------
echo   后续步骤:
echo   - 若上面提示"运行中替换失败"并弹出了监控窗口:
echo     1) 完全退出 ZCode (托盘图标右键, 选退出)
echo     2) 等监控窗口显示 [OK] 替换完成
echo     3) 重新启动 ZCode, 状态条回归
echo   - 若上面提示"完成。启动 ZCode 即可...":
echo     直接启动 ZCode 就能看到状态条
echo   - 监控窗口确认注入加载后会自动退出
echo --------------------------------------------------
pause