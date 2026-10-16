#!/usr/bin/env bash
# Terminal entry point; no new GUI/runtime dependency is required.
set -u
BASE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
action="${1:-install}"
mode="${2:-auto}"
case "$action" in install|undo|check) ;; *) printf '不支持的操作。\n'; exit 1;; esac
case "$mode" in auto|open|math|chinese|extra|all) ;; *) printf '不支持的字体组。\n'; exit 1;; esac
printf 'WPS 课件字体工具\n\n'
if [[ "$action" == install ]]; then
  printf '安装会补齐所选字体，已经装好的相同文件会保留。\n请先保存课件并完全退出 WPS。\n\n'
fi
bash "$BASE/tools/font-actions.sh" "$action" "$mode"
result=$?
printf '\n'
if [[ $result -eq 0 ]]; then
  case "$action" in
    install) printf '操作完成。现在可以重新打开 WPS 和原课件。\n' ;;
    undo) printf '撤销操作完成。\n' ;;
    check) printf '所选组的字体已识别，日志位置见上方。\n' ;;
  esac
else
  printf '操作没有全部完成。请查看上面的提示和日志位置。\n'
fi
if [[ -t 0 ]]; then
  printf '\n按回车关闭此窗口。'
  IFS= read -r _ || true
fi
exit "$result"
