"""Exercise interpreter isolation and actual image decoding at the CLI boundary."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(os.environ.get('MUSE_TEST_SCRIPTS', str(Path(__file__).resolve().parents[2] / 'skills' / 'core' / 'muse-commands' / 'scripts')))
PROBE = SCRIPTS / 'muse-runtime-dependencies.py'
IMAGE_PYTHON = os.environ.get('MUSE_TEST_IMAGE_PYTHON', sys.executable)


class RuntimeDependenciesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='muse dependency checks ')
        cls.root = Path(cls.temporary.name)
        cls.missing = cls.root / 'without pillow'
        subprocess.run([sys.executable, '-I', '-m', 'venv', '--without-pip', str(cls.missing)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cls.python = str(cls.missing / 'bin' / 'python')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def run_probe(self, selected, image=False, env=None, cwd=None):
        args = [sys.executable, '-I', str(PROBE), '--python', selected]
        if image:
            args.append('--require-image-decoder')
        result = subprocess.run(args, env=env, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=25)
        self.assertEqual(result.stderr, '')
        return result.returncode, json.loads(result.stdout)

    def test_standard_library_does_not_require_pillow(self):
        code, report = self.run_probe(self.python)
        self.assertEqual((code, report['status']), (0, 'PASS'))
        self.assertEqual(report['image_decoder']['status'], 'NOT_REQUESTED')
        self.assertEqual(report['runtime']['isolated'], 1)
        self.assertFalse(report['runtime']['user_site_enabled'])

    def test_missing_pillow_fails_under_isolation(self):
        code, report = self.run_probe(self.python, image=True)
        self.assertEqual(code, 2)
        self.assertEqual(report['error'], 'IMAGE_DECODER_UNAVAILABLE')

    def test_actual_png_and_jpeg_verify_and_decode(self):
        code, report = self.run_probe(IMAGE_PYTHON, image=True)
        self.assertEqual((code, report['status']), (0, 'PASS'))
        self.assertEqual(report['image_decoder']['formats'], ['PNG', 'JPEG'])
        self.assertTrue(report['image_decoder']['pillow_version'])

    def test_virtualenv_launcher_is_not_dereferenced(self):
        code, report = self.run_probe(self.python)
        self.assertEqual(code, 0)
        self.assertEqual(report['requested_python'], self.python)
        # Python 3.7 canonicalizes macOS /var to /private/var in sys.executable.
        self.assertTrue(os.path.samefile(report['runtime']['executable'], self.python))
        self.assertTrue(os.path.samefile(report['runtime']['prefix'], self.missing))
        self.assertNotEqual(report['runtime']['prefix'], report['runtime']['base_prefix'])

    def test_relative_interpreter_is_rejected(self):
        code, report = self.run_probe('python3')
        self.assertEqual(code, 2)
        self.assertEqual(report['error'], 'PYTHON_PATH_MUST_BE_ABSOLUTE')

    def test_missing_executable_is_reported(self):
        code, report = self.run_probe(str(self.root / 'absent-python'))
        self.assertEqual(code, 2)
        self.assertEqual(report['error'], 'PYTHON_EXECUTABLE_UNAVAILABLE')

    def test_non_utf8_startup_output_is_reported(self):
        selected = self.python
        site = subprocess.check_output([selected, '-I', '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'], universal_newlines=True).strip()
        hook = Path(site) / 'invalid_output.pth'
        for descriptor in (1, 2):
            with self.subTest(descriptor=descriptor):
                try:
                    hook.write_text("import os; os.write(%s, b'\\xff')\n" % descriptor)
                    code, report = self.run_probe(selected)
                    self.assertEqual((code, report['error']), (2, 'PYTHON_PROBE_INVALID_RESPONSE'))
                finally:
                    hook.unlink()

    def test_pythonpath_and_working_directory_cannot_supply_pillow(self):
        poison = self.root / 'poison'
        (poison / 'PIL').mkdir(parents=True)
        marker = poison / 'loaded'
        (poison / 'PIL' / '__init__.py').write_text('from pathlib import Path\nPath(' + repr(str(marker)) + ').write_text("unexpected")\n')
        environment = dict(os.environ, PYTHONPATH=str(poison))
        code, report = self.run_probe(self.python, image=True, env=environment, cwd=str(poison))
        self.assertEqual((code, report['error']), (2, 'IMAGE_DECODER_UNAVAILABLE'))
        self.assertFalse(marker.exists())

    def test_importable_but_broken_jpeg_decoder_fails(self):
        broken = self.root / 'broken decoder'
        subprocess.run([sys.executable, '-I', '-m', 'venv', '--without-pip', str(broken)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        selected = str(broken / 'bin' / 'python')
        site = subprocess.check_output([selected, '-I', '-c', 'import sysconfig; print(sysconfig.get_path("purelib"))'], universal_newlines=True).strip()
        package = Path(site) / 'PIL'
        package.mkdir()
        (package / '__init__.py').write_text('__version__ = "fault-fixture"\n')
        (package / 'Image.py').write_text('class Handle:\n    format = "PNG"\n    size = (1, 1)\n    def __enter__(self): return self\n    def __exit__(self, *args): pass\n    def verify(self): pass\n    def load(self): pass\ndef open(stream):\n    if stream.getvalue().startswith(bytes.fromhex("89504e47")): return Handle()\n    raise OSError("JPEG codec unavailable")\n')
        code, report = self.run_probe(selected, image=True)
        self.assertEqual((code, report['error']), (2, 'IMAGE_DECODER_FAILED'))
        self.assertEqual(report['image_decoder']['formats'], ['PNG'])

    def test_subprocess_timeout_is_a_failed_probe(self):
        spec = importlib.util.spec_from_file_location('probe_test', str(PROBE))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with patch.object(module.subprocess, 'run', side_effect=subprocess.TimeoutExpired('probe', 15)):
            report = module.probe(self.python, False)
        self.assertEqual((report['status'], report['error']), ('FAIL', 'PYTHON_PROBE_TIMEOUT'))


if __name__ == '__main__':
    unittest.main()
