#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Keep the legacy font destination so older installations remain manageable.
set -Eeuo pipefail
umask 077
fail() { printf '错误：%s\n' "$*" >&2; exit 1; }
usage() {
  cat <<'EOF'
WPS Classroom Fonts · WPS 课件字体助手

bash install.sh [open|math|chinese|extra|all]
bash check.sh   [open|math|chinese|extra|all]
bash undo.sh     open|math|chinese|extra|all

不指定安装/检查分组：完整包选择 all；仅含开源字体的包选择 open。
本地字体只准备了一部分时，请明确指定分组；不会静默跳过缺失文件。
open     9 个 STIX Two 开源字体文件（也是 math 的子集）
math    48 个数学、英语和符号字体文件
chinese  5 个常用中文字体文件
extra    5 个补充字体文件
all     58 个字体文件，包含 math + chinese + extra
撤销必须明确指定分组。安装和撤销请使用当前账号，不要加 sudo。
EOF
}
action="${1:-}"
[[ -n "$action" ]] || fail '缺少操作类型。'
shift
case "$action" in install|undo|check) ;; *) fail '不支持的操作。';; esac
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then usage; exit 0; fi
[[ $# -le 1 ]] || fail '参数过多；用 --help 查看用法。'
if [[ "$action" == undo && $# -eq 0 ]]; then usage; exit 1; fi
mode="${1:-auto}"
BASE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"
if [[ "$mode" == auto ]]; then
  # Decide only between the two supported complete distributions.
  present=0
  while read -r digest relative; do
    [[ "$relative" == fonts/* && "$relative" != *..* ]] || fail '字体清单格式错误。'
    if [[ -f "$BASE/$relative" ]]; then present=$((present + 1)); fi
  done < "$BASE/manifests/fonts.sha256"
  case "$present" in
    58) mode=all ;;
    9) mode=open ;;
    *) fail '字体准备不完整。请指定 open、math、chinese 或 extra，或先导入完整字体。';;
  esac
fi
case "$mode" in
  open) label='STIX Two 开源字体'; expected=9 ;;
  math) label='数学、英语和符号字体'; expected=48 ;;
  chinese) label='常用中文字体'; expected=5 ;;
  extra) label='补充字体'; expected=5 ;;
  all) label='全部三组字体'; expected=58 ;;
  *) fail '只能选择 open、math、chinese、extra 或 all。';;
esac
[[ "$(uname -s)" == Linux ]] || fail '请在麒麟或其他 Linux 电脑上运行。'
for cmd in date tee mkdir sort tr grep realpath awk fc-list sha256sum mktemp cat; do
  command -v "$cmd" >/dev/null 2>&1 || fail "缺少 $cmd，请先安装所需工具。"
done
if [[ "$action" != check ]]; then
  [[ "$EUID" != 0 ]] || fail '请使用平时打开 WPS 的账号运行，不要加 sudo。'
  for cmd in fc-cache mv flock chmod; do command -v "$cmd" >/dev/null 2>&1 || fail "缺少 $cmd。"; done
fi
if [[ "$action" == install ]]; then
  for cmd in fc-scan cp cmp rm; do command -v "$cmd" >/dev/null 2>&1 || fail "缺少 $cmd。"; done
fi
[[ -n "${HOME:-}" && "$HOME" == /* && "$HOME" != / ]] || fail '账号主目录不正确。'
HOME_REAL="$(realpath -e -- "$HOME")"
within_home() { case "$1/" in "$HOME_REAL/"*) ;; *) fail '数据位置必须在当前账号的主目录内。';; esac; }
CACHE="${XDG_CACHE_HOME:-$HOME/.cache}"
[[ "$CACHE" == /* ]] || fail '缓存目录必须是绝对路径。'
LOGDIR="$(realpath -m -- "$CACHE/wps-classroom-fonts/logs")"
within_home "$LOGDIR"
mkdir -p -- "$LOGDIR"
LOG="$(mktemp "$LOGDIR/$action-$mode-$(date +%Y%m%d-%H%M%S).XXXXXX.log")"
# Replace literal paths, never treat account or package names as regex patterns.
redact() {
  WCF_PACKAGE="$BASE" WCF_HOME="$HOME_REAL" awk '
    function replace_literal(text, needle, replacement, result, position) {
      while (length(needle) && (position = index(text, needle))) {
        result = result substr(text, 1, position - 1) replacement
        text = substr(text, position + length(needle))
      }
      return result text
    }
    { print replace_literal(replace_literal($0, ENVIRON["WCF_PACKAGE"], "<package>"), ENVIRON["WCF_HOME"], "<home>"); fflush() }
  '
}
exec > >(redact | tee "$LOG") 2>&1
temporary=''
cleanup() { if [[ -n "$temporary" && -f "$temporary" ]]; then rm -f -- "$temporary"; fi; }
trap cleanup EXIT
on_error() { local rc=$?; printf '\n操作中止（退出码 %s），请查看日志。\n' "$rc" >&2; exit "$rc"; }
trap on_error ERR
printf 'WPS 课件字体助手：%s\n选择：%s\n日志：%s\n\n' "$action" "$label" "$LOG"

PROFILE="$BASE/manifests/families.tsv"
[[ -f "$PROFILE" && ! -L "$PROFILE" ]] || fail '缺少字体检查清单，请完整复制项目。'
profile_subjects=(); profile_labels=(); profile_families=()
while IFS=$'\t' read -r scope subject display family; do
  [[ -n "$scope" && "$scope" != \#* ]] || continue
  case "$scope" in open|math|chinese|extra) ;; *) fail '检查清单分组错误。';; esac
  [[ -n "$subject" && -n "$display" && -n "$family" ]] || fail '检查清单不完整。'
  if [[ "$mode" == all ]]; then [[ "$scope" != open ]] || continue
  else [[ "$mode" == "$scope" ]] || continue; fi
  profile_subjects+=("$subject"); profile_labels+=("$display"); profile_families+=("$family")
done < "$PROFILE"
[[ ${#profile_families[@]} -gt 0 ]] || fail '这一组没有检查项目。'
show_status() {
  MISSING_COUNT=0
  local subject total found i missing_names
  for subject in 数学 英语 语文 补充字体; do
    total=0; found=0; missing_names=''
    for i in "${!profile_families[@]}"; do
      [[ "${profile_subjects[$i]}" == "$subject" ]] || continue
      total=$((total + 1))
      if printf '%s\n' "$families" | grep -Fix -- "${profile_families[$i]}" >/dev/null; then
        found=$((found + 1))
      else
        MISSING_COUNT=$((MISSING_COUNT + 1))
        missing_names+="  ${profile_labels[$i]}（${profile_families[$i]}）"$'\n'
      fi
    done
    [[ $total -gt 0 ]] || continue
    if [[ $found -eq $total ]]; then printf '%s：已识别（%s/%s）\n' "$subject" "$found" "$total"
    else printf '%s：需补充（已识别 %s/%s）\n%s' "$subject" "$found" "$total" "$missing_names"; fi
  done
}
if [[ "$action" == check ]]; then
  families="$(fc-list --format '%{family}\n' | tr ',' '\n' | sort -fu)"
  show_status
  if [[ "$MISSING_COUNT" -gt 0 ]]; then
    printf '\n请准备对应字体后运行：bash install.sh %s\n' "$mode"
    exit 2
  fi
  printf '\n所选组的字体均已识别。请重新打开 WPS，用原课件确认显示效果。\n'
  exit 0
fi

DATA="${XDG_DATA_HOME:-$HOME/.local/share}"
[[ "$DATA" == /* ]] || fail '字体数据目录必须是绝对路径。'
DATA="$(realpath -m -- "$DATA")"; within_home "$DATA"
FONT_ROOT="$(realpath -m -- "$DATA/fonts")"; within_home "$FONT_ROOT"
STATE="$DATA/wps-classroom-fonts"
[[ ! -L "$STATE" ]] || fail '状态目录不能是符号链接。'
mkdir -p -- "$STATE"
[[ ! -L "$STATE/operation.lock" ]] || fail '锁文件不能是符号链接。'
exec 9> "$STATE/operation.lock"
flock -n 9 || fail '另一个安装或撤销操作正在进行，请等待完成。'
DEST="$FONT_ROOT/classroom-math-offline-v1"
MARKER="$DEST/.classroom-font-installer-v1"
[[ ! -L "$DEST" ]] || fail '字体安装目录是符号链接，已停止。'
if [[ -e "$DEST" ]]; then
  [[ -d "$DEST" && -f "$MARKER" && ! -L "$MARKER" ]] || fail '这个目录不属于本字体工具，已停止。'
  [[ "$(cat "$MARKER")" == classroom-font-installer-v1 ]] || fail '字体目录标记不匹配。'
fi

font_hashes=(); font_relative=(); declare -A seen=()
scopes=("$mode"); [[ "$mode" != all ]] || scopes=(math chinese extra)
for scope in "${scopes[@]}"; do
  manifest="$BASE/manifests/groups/$scope.sha256"
  [[ -f "$manifest" && ! -L "$manifest" ]] || fail '分组清单缺失，请完整复制项目。'
  while IFS= read -r line; do
    [[ "$line" =~ ^([0-9a-f]{64})[[:space:]]{2}(fonts/(MathType-official|Open-stix2-otf|Windows-common|Chinese-common|Supplemental)/[0-9a-f]{64}\.(ttf|otf|ttc|otc))$ ]] || fail '分组清单格式不正确。'
    digest="${BASH_REMATCH[1]}"; relative="${BASH_REMATCH[2]}"; filename="${relative##*/}"
    [[ "${filename%.*}" == "$digest" && -z "${seen[$digest]:-}" ]] || fail '清单包含重复项或文件名与校验值不符。'
    seen[$digest]=1
    case "$scope" in
      open) [[ "$relative" == fonts/Open-stix2-otf/* ]] || fail '开源组混入其他字体。';;
      chinese) [[ "$relative" == fonts/Chinese-common/* ]] || fail '中文组混入其他字体。';;
      extra) [[ "$relative" == fonts/Supplemental/* ]] || fail '补充组混入其他字体。';;
      math) [[ "$relative" != fonts/Chinese-common/* && "$relative" != fonts/Supplemental/* ]] || fail '数学组混入其他字体。';;
    esac
    font_hashes+=("$digest"); font_relative+=("$relative")
  done < "$manifest"
done
[[ ${#font_relative[@]} -eq $expected ]] || fail '分组清单数量不正确。'

if [[ "$action" == install ]]; then
  printf '正在检查所选的 %s 个字体文件……\n' "$expected"
  font_names=()
  # Validate every source and destination before making the first font change.
  for i in "${!font_relative[@]}"; do
    source_file="$BASE/${font_relative[$i]}"; target="$DEST/${font_relative[$i]##*/}"
    [[ -f "$source_file" && ! -L "$source_file" ]] || fail "缺少字体：${font_relative[$i]}。公开版可安装 open；其他字体须先在本地导入。"
    case "$(realpath -e -- "$source_file")" in "$BASE/fonts/"*) ;; *) fail '源字体指向项目之外。';; esac
    actual="$(sha256sum < "$source_file")"; actual="${actual%% *}"
    [[ "$actual" == "${font_hashes[$i]}" ]] || fail '字体校验失败；尚未修改任何已安装字体。'
    [[ ! -L "$target" ]] || fail '目标字体是符号链接，已停止。'
    if [[ -e "$target" ]]; then
      if [[ ! -f "$target" ]] || ! cmp -s -- "$source_file" "$target"; then
        fail '已有同名文件内容不同；尚未修改任何字体。'
      fi
    fi
    name="$(fc-scan --format '%{family}\n' -- "$source_file" 2>/dev/null | tr '\n' ' ')" || fail '有无法识别的字体。'
    [[ -n "$name" ]] || fail '有无法识别的字体。'
    font_names+=("${name% }")
  done
  printf '请先保存课件并完全退出 WPS。\n安装位置：%s\n\n' "$DEST"
  mkdir -p -- "$DEST"; chmod 0755 -- "$DEST"
  if [[ ! -e "$MARKER" ]]; then printf 'classroom-font-installer-v1\n' > "$MARKER"; fi
  new=0; same=0
  for i in "${!font_relative[@]}"; do
    source_file="$BASE/${font_relative[$i]}"; target="$DEST/${font_relative[$i]##*/}"
    if [[ -f "$target" ]]; then same=$((same + 1)); printf '保留已有：%s\n' "${font_names[$i]}"; continue; fi
    temporary="$(mktemp "$DEST/.incoming.XXXXXX")"
    cp -- "$source_file" "$temporary"
    actual="$(sha256sum < "$temporary")"; actual="${actual%% *}"
    [[ "$actual" == "${font_hashes[$i]}" ]] || fail '复制后校验失败。请检查存储设备并重试。'
    chmod 0644 -- "$temporary"; mv -- "$temporary" "$target"; temporary=''
    new=$((new + 1)); printf '新增：%s\n' "${font_names[$i]}"
  done
  printf '\n本组新增 %s 个文件；本组已存在 %s 个；跳过 0 个。\n' "$new" "$same"
  fc-cache -f "$DEST"
  families="$(fc-list --format '%{file}\t%{family}\n' | awk -F '\t' -v dest="$DEST/" 'index($1,dest)==1 {print $2}' | tr ',' '\n' | sort -fu)"
  show_status
  [[ "$MISSING_COUNT" -eq 0 ]] || { printf '仍有字体未识别，请运行 bash check.sh %s。\n' "$mode"; exit 2; }
  printf '\n所选字体安装并识别成功。重新打开 WPS 检查课件。\n'
  exit 0
fi

if [[ ! -e "$DEST" ]]; then printf '没有本工具安装的字体，无需撤销。\n'; exit 0; fi
targets=()
for i in "${!font_relative[@]}"; do
  target="$DEST/${font_relative[$i]##*/}"
  [[ ! -L "$target" ]] || fail '待撤销文件是符号链接，已停止。'
  [[ -e "$target" ]] || continue
  [[ -f "$target" ]] || fail '待撤销路径不是普通字体文件。'
  actual="$(sha256sum < "$target")"; actual="${actual%% *}"
  [[ "$actual" == "${font_hashes[$i]}" ]] || fail '待撤销文件内容已改变；尚未移动任何字体。'
  targets+=("$target")
done
if [[ ${#targets[@]} -eq 0 ]]; then printf '本组字体没有安装，无需撤销。\n'; exit 0; fi
BACKROOT="$(realpath -m -- "$DATA/classroom-math-font-backups")"; within_home "$BACKROOT"
case "$BACKROOT/" in "$FONT_ROOT/"*) fail '备份位置不能在字体搜索目录内。';; esac
mkdir -p -- "$BACKROOT"
BACKUP="$(mktemp -d "$BACKROOT/$mode-$(date +%Y%m%d-%H%M%S).XXXXXX")"
for target in "${targets[@]}"; do mv -- "$target" "$BACKUP/${target##*/}"; done
fc-cache -f "$DEST"
printf '已撤销本组 %s 个字体文件，文件保存在备份里。\n备份位置：%s\n' "${#targets[@]}" "$BACKUP"
printf '请完全退出并重新打开 WPS。需要恢复时，再运行对应的安装命令。\n'
