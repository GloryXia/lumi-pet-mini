import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import install_pet
from validate_pet import PACKAGE, validate


class InstallationTests(unittest.TestCase):
    def test_install_and_update_preserve_existing_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'lumi'
            install_pet.install(dest)
            self.assertEqual((dest / 'spritesheet.webp').read_bytes(), (PACKAGE / 'spritesheet.webp').read_bytes())
            (dest / 'user-note.txt').write_text('keep me')
            report = install_pet.install(dest)
            self.assertEqual((Path(report['backup']) / 'user-note.txt').read_text(), 'keep me')

    def test_failed_replacement_restores_original_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'lumi'
            install_pet.install(dest)
            (dest / 'user-note.txt').write_text('rollback')
            replace = install_pet.os.replace

            def fail_staged(source, target):
                if Path(source).name.startswith('.lumi-stage-'):
                    raise OSError('simulated replacement failure')
                return replace(source, target)

            with patch.object(install_pet.os, 'replace', side_effect=fail_staged):
                with self.assertRaises(OSError):
                    install_pet.install(dest)
            self.assertEqual((dest / 'user-note.txt').read_text(), 'rollback')
            self.assertEqual(validate(dest)['ok'], True)

    def test_dry_run_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'lumi'
            self.assertTrue(install_pet.install(dest, dry_run=True)['dry_run'])
            self.assertFalse(dest.exists())

    def test_other_pet_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            dest = Path(tmp) / 'other'
            dest.mkdir()
            (dest / 'pet.json').write_text(json.dumps({'id': 'other'}))
            with self.assertRaises(ValueError):
                install_pet.install(dest)
            self.assertEqual(json.loads((dest / 'pet.json').read_text())['id'], 'other')


if __name__ == '__main__':
    unittest.main()
