#!/usr/bin/env python3
"""Exercise release archives against isolated Git commits and private files."""
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]


class ReleaseTests(unittest.TestCase):
    """Keep real project history and the user's Git configuration untouched."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wcf-release-test-')
        self.repo = Path(self.temp.name)
        (self.repo / 'tools').mkdir()
        (self.repo / 'manifests/groups').mkdir(parents=True)
        for name in ('build-release.py', 'verify-public.py'):
            target = self.repo / 'tools' / name
            shutil.copyfile(ROOT / 'tools' / name, target)
            target.chmod(0o755)
        shutil.copyfile(ROOT / 'manifests/groups/open.sha256', self.repo / 'manifests/groups/open.sha256')
        shutil.copytree(ROOT / 'fonts/Open-stix2-otf', self.repo / 'fonts/Open-stix2-otf')
        (self.repo / 'VERSION').write_text('1.0.0\n', encoding='utf-8')
        (self.repo / '.gitignore').write_text('/private/\n/build/\n*.log\n', encoding='utf-8')
        self.git('init', '-q')
        self.git('config', 'user.name', 'Release test')
        self.git('config', 'user.email', 'release-test@example.invalid')
        self.git('config', 'commit.gpgsign', 'false')
        self.git('config', 'core.autocrlf', 'false')
        self.archive = self.repo / 'build/wps-classroom-fonts-v1.0.0.zip'

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        """Run Git exclusively inside the disposable fixture repository."""
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)

    def commit(self):
        self.git('add', '.')
        self.git('commit', '-qm', 'Prepare release fixture')

    def build(self, success):
        """Check success or rejection without depending on localized errors."""
        result = subprocess.run([sys.executable, str(self.repo / 'tools/build-release.py')], capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(self.archive.exists())

    def test_archive_is_committed_only_checksummed_and_reproducible(self):
        self.commit()
        (self.repo / 'private').mkdir()
        (self.repo / 'private/local.ttf').write_bytes(b'private font')
        (self.repo / 'operation.log').write_text('private diagnostic', encoding='utf-8')
        (self.repo / 'untracked.txt').write_text('not committed', encoding='utf-8')
        self.build(True)
        first = self.archive.read_bytes()
        digest = hashlib.sha256(first).hexdigest()
        self.assertEqual(self.archive.with_suffix('.zip.sha256').read_text().strip(), f'{digest}  {self.archive.name}')
        with zipfile.ZipFile(self.archive) as archive:
            self.assertIsNone(archive.testzip())
            names = [name for name in archive.namelist() if not name.endswith('/')]
            expected = {'wps-classroom-fonts/' + name for name in self.git('ls-files').stdout.decode().splitlines()}
            self.assertEqual(set(names), expected)
            self.assertEqual(len([name for name in names if '/fonts/' in name]), 9)
            mode = archive.getinfo('wps-classroom-fonts/tools/build-release.py').external_attr >> 16
            self.assertTrue(mode & 0o111)
        self.build(True)
        self.assertEqual(self.archive.read_bytes(), first)

    def test_dirty_or_staged_tracked_changes_rejected(self):
        self.commit()
        (self.repo / 'VERSION').write_text('1.0.1\n', encoding='utf-8')
        self.build(False)
        self.git('add', 'VERSION')
        self.build(False)

    def test_unreviewed_font_in_commit_rejected(self):
        (self.repo / 'fonts/unreviewed.ttf').write_bytes(b'not in OFL manifest')
        self.commit()
        self.build(False)

    def test_missing_commit_rejected(self):
        self.build(False)

    def test_invalid_version_rejected(self):
        (self.repo / 'VERSION').write_text('1.0.0/invalid\n', encoding='utf-8')
        self.commit()
        self.build(False)


if __name__ == '__main__':
    unittest.main(verbosity=2)
