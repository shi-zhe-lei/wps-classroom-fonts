#!/usr/bin/env python3
"""Import exact, locally supplied font versions without downloading anything."""
import argparse
import csv
import hashlib
import os
from pathlib import Path
import shutil
import sys
import tempfile


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            result.update(block)
    return result.hexdigest()


def main():
    parser = argparse.ArgumentParser(description='从本地字体目录导入清单中的准确版本；不会下载字体。')
    parser.add_argument('source', type=Path, help='已有字体目录或完整离线包目录')
    parser.add_argument('--group', choices=['all', 'math', 'chinese', 'extra', 'open'], default='all')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if not args.source.is_dir():
        parser.error('来源必须是存在的目录。')
    with (root / 'manifests/catalog.tsv').open(encoding='utf-8') as stream:
        rows = list(csv.DictReader(stream, delimiter='\t'))
    if args.group == 'open':
        rows = [row for row in rows if row['distribution'] == 'OFL-1.1']
    elif args.group != 'all':
        rows = [row for row in rows if row['group'] == args.group]
    expected = {row['sha256']: row for row in rows}
    candidates = {}
    for folder, dirs, names in os.walk(args.source, followlinks=False):
        dirs[:] = [name for name in dirs if name not in {'.git', 'logs', '__MACOSX'} and not (Path(folder) / name).is_symlink()]
        for name in names:
            path = Path(folder) / name
            if path.suffix.lower() not in {'.ttf', '.ttc', '.otf', '.otc'} or path.is_symlink():
                continue
            if path.stat().st_size > 50 * 1024 * 1024:
                continue
            value = digest(path)
            if value in expected:
                candidates.setdefault(value, path)
    plan = []; ready = 0
    for value, row in expected.items():
        target = root / row['path']
        if not target.resolve().is_relative_to(root / 'fonts'):
            raise ValueError('目标字体路径超出项目 fonts 目录。')
        for part in [target, *target.parents]:
            if part == root:
                break
            if part.is_symlink():
                raise ValueError('目标字体路径不能含符号链接。')
        if target.exists():
            if not target.is_file() or digest(target) != value:
                raise ValueError('同名目标文件已有其他内容；未导入任何文件。')
            ready += 1
        elif value in candidates:
            plan.append((value, candidates[value], target))
    for value, source, target in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, name = tempfile.mkstemp(prefix='.import-', dir=target.parent)
        temporary = Path(name)
        try:
            with os.fdopen(fd, 'wb') as output, source.open('rb') as stream:
                shutil.copyfileobj(stream, output)
            if digest(temporary) != value:
                raise ValueError('复制后校验失败。')
            temporary.chmod(0o644)
            temporary.replace(target)
        finally:
            temporary.unlink(missing_ok=True)
    total = ready + len(plan)
    print(f'新增 {len(plan)} 个；已有 {ready} 个；本组就绪 {total}/{len(rows)}。')
    print('本地导入不会赋予额外的字体使用或分发权。请使用你有权使用的文件。')
    if total != len(rows):
        print('仍缺少清单规定版本；未匹配的字体没有导入。详见 manifests/catalog.tsv。')
        return 2
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError) as error:
        # Do not disclose user paths in a public issue pasted from this message.
        print(f'导入失败（{type(error).__name__}）；请检查目录权限、文件完整性及目标冲突。', file=sys.stderr)
        sys.exit(1)
