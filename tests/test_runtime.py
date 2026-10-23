#!/usr/bin/env python3
"""Real-font integration tests; never overwrite HOME or scan real user fonts."""
import csv
import fcntl
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[1]
FONT_DIR = 'classroom-math-offline-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        cache = Path.home() / '.cache'
        cache.mkdir(exist_ok=True)
        self.temp = Path(tempfile.mkdtemp(prefix='wcf-test-', dir=cache))
        self.package = self.temp / "Package with spaces ' 100% 中文"
        self.package.mkdir()
        for name in ['tools', 'manifests', 'actions']:
            shutil.copytree(ROOT / name, self.package / name, ignore=shutil.ignore_patterns('__pycache__'))
        for path in ROOT.iterdir():
            if path.suffix in {'.sh', '.desktop'}:
                shutil.copyfile(path, self.package / path.name)
        shutil.copytree(ROOT / 'fonts/Open-stix2-otf', self.package / 'fonts/Open-stix2-otf')
        self.data = self.temp / 'data'
        self.dest = self.data / 'fonts' / FONT_DIR
        self.cache = self.temp / 'cache'
        (self.data / 'fonts').mkdir(parents=True)
        self.cache.mkdir()
        config = self.temp / 'fonts.conf'
        config.write_text(f'<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd"><fontconfig><dir>{escape(str(self.data / "fonts"))}</dir><cachedir>{escape(str(self.cache))}</cachedir></fontconfig>', encoding='utf-8')
        self.env = dict(os.environ, XDG_DATA_HOME=str(self.data), XDG_CACHE_HOME=str(self.cache), FONTCONFIG_FILE=str(config))
        self.open_rows = self.rows('open')

    def tearDown(self):
        resolved = self.temp.resolve()
        assert resolved.parent == (Path.home() / '.cache').resolve() and resolved.name.startswith('wcf-test-')
        shutil.rmtree(resolved)

    def rows(self, group):
        return [line.split() for line in (self.package / f'manifests/groups/{group}.sha256').read_text().splitlines()]

    def run_command(self, args, expected=0):
        result = subprocess.run(args, cwd=self.package, env=self.env, stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result.stdout + result.stderr

    def action(self, name, *args, expected=0):
        return self.run_command(['bash', str(self.package / f'{name}.sh'), *args], expected)

    def installed(self):
        return {p.name: sha(p) for p in self.dest.glob('*') if p.suffix in {'.otf', '.ttf', '.ttc', '.otc'}}

    def test_default_open_repeat_check_and_undo(self):
        self.assertIn('新增 9 个文件', self.action('install'))
        before = self.installed(); self.assertEqual(len(before), 9)
        self.assertIn('已存在 9 个', self.action('install'))
        self.assertEqual(self.installed(), before)
        self.action('check')
        self.assertIn('仍缺少：NEU-BZ-S92', self.action('check', 'all', expected=2))
        self.action('undo', 'open')
        self.assertEqual(self.installed(), {})
        backups = list((self.data / 'classroom-math-font-backups').glob('*/*.otf'))
        self.assertEqual({p.name: sha(p) for p in backups}, before)
        self.action('install', 'open'); self.assertEqual(self.installed(), before)

    def test_full_request_without_local_fonts_makes_no_font_changes(self):
        self.action('install', 'all', expected=1)
        self.assertEqual(self.installed(), {})
        self.assertFalse(self.dest.exists())

    def test_corrupt_source_preflight(self):
        source = self.package / self.open_rows[-1][1]
        source.write_bytes(source.read_bytes() + b'corruption')
        self.action('install', 'open', expected=1)
        self.assertFalse(self.dest.exists())

    def test_destination_conflict_preflight(self):
        self.action('install', 'open')
        first = self.dest / Path(self.open_rows[0][1]).name
        last = self.dest / Path(self.open_rows[-1][1]).name
        first.unlink(); last.write_bytes(b'modified-local-file')
        before = self.installed()
        self.action('install', 'open', expected=1)
        self.assertFalse(first.exists()); self.assertEqual(self.installed(), before)

    def test_undo_refuses_modified_file_before_any_move(self):
        self.action('install', 'open')
        last = self.dest / Path(self.open_rows[-1][1]).name
        last.write_bytes(b'modified-local-file')
        before = self.installed()
        self.action('undo', 'open', expected=1)
        self.assertEqual(self.installed(), before)
        self.assertFalse((self.data / 'classroom-math-font-backups').exists())

    def test_undo_requires_explicit_group(self):
        self.action('install', 'open')
        before = self.installed()
        self.action('undo', expected=1)
        self.assertEqual(self.installed(), before)

    def test_manifest_traversal_and_duplicate_rejected(self):
        manifest = self.package / 'manifests/groups/open.sha256'
        original = manifest.read_text()
        manifest.write_text(original.replace('fonts/Open-stix2-otf/', '../outside/', 1))
        self.action('install', 'open', expected=1)
        lines = original.splitlines(); lines[-1] = lines[0]
        manifest.write_text('\n'.join(lines) + '\n')
        self.action('install', 'open', expected=1)
        self.assertFalse(self.dest.exists())

    def test_source_symlink_rejected(self):
        source = self.package / self.open_rows[0][1]
        external = self.temp / 'external.otf'
        source.replace(external); source.symlink_to(external)
        self.action('install', 'open', expected=1)
        self.assertFalse(self.dest.exists())

    def test_destination_symlink_rejected(self):
        external = self.temp / 'external-dir'; external.mkdir()
        self.dest.symlink_to(external, target_is_directory=True)
        self.action('install', 'open', expected=1)
        self.assertEqual(list(external.iterdir()), [])

    def test_unowned_directory_rejected(self):
        self.dest.mkdir()
        sentinel = self.dest / 'keep.txt'; sentinel.write_text('unrelated')
        self.action('install', 'open', expected=1)
        self.assertEqual(sentinel.read_text(), 'unrelated')

    def test_concurrent_operation_rejected(self):
        state = self.data / 'wps-classroom-fonts'; state.mkdir()
        with (state / 'operation.lock').open('w') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.action('install', 'open', expected=1)
        self.assertFalse(self.dest.exists())

    def test_outside_home_and_font_backup_paths_rejected(self):
        self.env['XDG_DATA_HOME'] = '/tmp/wcf-forbidden-target'
        self.action('install', 'open', expected=1)
        self.env['XDG_DATA_HOME'] = str(self.data)
        self.action('install', 'open')
        before = self.installed()
        (self.data / 'classroom-math-font-backups').symlink_to(self.data / 'fonts', target_is_directory=True)
        self.action('undo', 'open', expected=1)
        self.assertEqual(self.installed(), before)

    def test_logs_private_and_redacted(self):
        output = self.action('install', 'open')
        self.action('check')
        self.assertNotIn(str(Path.home()), output)
        for path in (self.cache / 'wps-classroom-fonts/logs').glob('*.log'):
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            self.assertNotIn(str(Path.home()), path.read_text())
            self.assertNotIn(str(self.package), path.read_text())
        self.assertFalse((self.package / 'logs').exists())

    def test_desktop_entries_real_parser_and_file_uris(self):
        import gi
        gi.require_version('Gio', '2.0')
        from gi.repository import Gio, GLib
        for path in self.package.rglob('*.desktop'):
            self.run_command(['desktop-file-validate', str(path)])
        for relative, expected in [('install.desktop', 0), ('check.desktop', 0), ('actions/undo-open.desktop', 0), ('actions/install-open.desktop', 0), ('actions/install-extra.desktop', 1), ('actions/install-lesson.desktop', 1), ('actions/undo-lesson.desktop', 0)]:
            path = self.package / relative
            app = Gio.DesktopAppInfo.new_from_filename(str(path))
            self.assertIsNotNone(app); self.assertTrue(app.get_boolean('Terminal'))
            ok, args = GLib.shell_parse_argv(app.get_commandline()); self.assertTrue(ok)
            args = [path.as_uri() if arg == '%k' else arg.replace('%%', '%') for arg in args]
            self.run_command(args, expected)
        self.assertEqual(len(self.installed()), 9)

    def test_import_matching_files_and_unknown_version(self):
        source = self.temp / 'provided'; source.mkdir()
        value, relative = self.open_rows[0]
        target = self.package / relative
        target.replace(source / 'arbitrary-name.otf')
        (source / 'unknown.ttf').write_bytes(b'not-an-approved-font')
        result = self.run_command(['python3', str(self.package / 'tools/import-fonts.py'), str(source), '--group', 'open'])
        self.assertIn('新增 1 个', result); self.assertEqual(sha(target), value)
        self.assertFalse((self.package / 'fonts/unknown.ttf').exists())

    @unittest.skipUnless(os.environ.get('WCF_TEST_FULL_SOURCE'), 'Optional local 65-file font set not provided')
    def test_full_install_every_group_undo_restore_and_legacy(self):
        self.run_command(['python3', str(self.package / 'tools/import-fonts.py'), os.environ.get('WCF_TEST_FULL_SOURCE', '')])
        self.assertIn('新增 65 个文件', self.action('install'))
        before = self.installed(); self.assertEqual(len(before), 65)
        self.assertIn('仍缺少：NEU-BZ-S92', self.action('check', 'all', expected=2))
        sentinel = self.dest / 'unrelated.txt'; sentinel.write_text('preserve')
        for group, count in [('lesson', 7), ('chinese', 5), ('extra', 5), ('math', 48)]:
            self.action('undo', group)
            remaining = self.installed()
            removed = {Path(rel).name for _, rel in self.rows(group)}
            self.assertEqual(len(remaining), 65 - count)
            self.assertEqual(remaining, {k: v for k, v in before.items() if k not in removed})
            self.action('install', group); self.assertEqual(self.installed(), before)
        self.assertEqual(sentinel.read_text(), 'preserve')
        self.action('undo', 'all'); self.assertEqual(self.installed(), {})
        self.assertEqual(sentinel.read_text(), 'preserve')

    @unittest.skipUnless(os.environ.get('WCF_TEST_FULL_SOURCE'), 'Optional local font set not provided')
    def test_legacy_upgrade_and_lesson_undo_preserve_all_original_fonts(self):
        self.run_command(['python3', str(self.package / 'tools/import-fonts.py'), os.environ['WCF_TEST_FULL_SOURCE']])
        for group in ['math', 'chinese', 'extra']:
            self.action('install', group)
        original = self.installed()
        self.assertEqual(len(original), 58)
        result = self.action('install')
        self.assertIn('新增 7 个文件', result)
        self.assertIn('已存在 58 个', result)
        self.assertIn('尚未随包提供：NEU-BZ-S92', result)
        complete = self.installed()
        self.assertEqual(len(complete), 65)
        self.assertTrue(original.items() <= complete.items())
        result = self.action('check', 'lesson', expected=2)
        self.assertIn('课件补充：已识别（7/7）', result)
        self.assertIn('仍缺少：NEU-BZ-S92', result)
        self.assertNotIn('所选组的字体均已识别', result)
        self.action('check', 'math')
        self.action('undo', 'lesson')
        self.assertEqual(self.installed(), original)
        self.action('install', 'lesson')
        self.assertEqual(self.installed(), complete)

    def test_pending_check_uses_actual_account_fonts_and_respects_group(self):
        self.action('install', 'open')
        pending = self.package / 'manifests/pending.tsv'
        # Fixture: a separately installed family satisfies a pending request.
        pending.write_text('lesson\tSTIX Two Math\tFixture only\n', encoding='utf-8')
        result = self.action('check', 'lesson', expected=2)
        self.assertIn('STIX Two Math：当前账号已经识别（非本包提供）', result)
        self.assertNotIn('仍缺少：STIX Two Math', result)
        self.assertNotIn('待补清单', self.action('check', 'open'))
        pending.unlink()
        self.action('install', 'open', expected=1)
        self.assertEqual(len(self.installed()), 9)


if __name__ == '__main__':
    unittest.main(verbosity=2)
