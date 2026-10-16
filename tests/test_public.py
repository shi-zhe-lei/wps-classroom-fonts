#!/usr/bin/env python3
"""Ensure the publication guard inspects the index and rejects accidental leaks."""
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PublicAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='wcf-public-test-')
        self.repo = Path(self.temp.name)
        (self.repo / 'tools').mkdir()
        (self.repo / 'manifests/groups').mkdir(parents=True)
        shutil.copyfile(ROOT / 'tools/verify-public.py', self.repo / 'tools/verify-public.py')
        shutil.copyfile(ROOT / 'manifests/groups/open.sha256', self.repo / 'manifests/groups/open.sha256')
        shutil.copytree(ROOT / 'fonts/Open-stix2-otf', self.repo / 'fonts/Open-stix2-otf')
        self.git('init', '-q')
        self.git('add', '.')
        self.git('update-index', '--chmod=+x', 'tools/verify-public.py')

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(['git', '-C', str(self.repo), *args], check=True, capture_output=True)

    def audit(self, expected):
        result = subprocess.run([sys.executable, str(self.repo / 'tools/verify-public.py')], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)

    def inject(self, name, content):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        self.git('add', name)

    def test_clean_index(self):
        self.audit(0)

    def test_log_rejected(self):
        self.inject('logs/operation.log', b'example')
        self.audit(1)

    def test_unknown_font_rejected(self):
        self.inject('fonts/Local/extra.ttf', b'not-distributable')
        self.audit(1)

    def test_personal_path_and_token_rejected(self):
        path = '/' + 'home' + '/' + 'example-person' + '/private'
        self.inject('notes.md', path.encode())
        self.audit(1)
        self.inject('notes.md', ('gh' + 'p_' + 'a' * 36).encode())
        self.audit(1)

    def test_reads_staged_object_not_working_tree(self):
        self.inject('notes.md', b'Public project notes')
        (self.repo / 'notes.md').write_text('/' + 'home' + '/' + 'example-person' + '/private')
        self.audit(0)
        self.git('add', 'notes.md')
        self.audit(1)

    def test_non_ascii_runtime_filename_rejected(self):
        self.inject('安装.sh', b'#!/usr/bin/env bash\n')
        self.audit(1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
