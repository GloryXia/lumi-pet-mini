import contextlib
import io
import json
import hashlib
import shutil
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
import native_pet


class NativeLifecycleTests(unittest.TestCase):
    def call(self, *args):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = native_pet.main(list(args))
        self.assertEqual(code, 0)
        return json.loads(output.getvalue())

    def test_native_install_is_discoverable_and_preserves_legacy_pet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / 'lumi'
            old.mkdir()
            (old / 'pet.json').write_text('{"id":"lumi"}')
            report = self.call('install', '--pets-root', tmp)
            dest = Path(report['destination'])
            manifest = json.loads((dest / 'pet.json').read_text())
            self.assertEqual(manifest['spriteVersionNumber'], 2)
            self.assertEqual(manifest['displayName'], '露米 Lumi · 项目版')
            self.assertTrue((dest / manifest['spritesheetPath']).is_file())
            self.assertEqual((old / 'pet.json').read_text(), '{"id":"lumi"}')
            again = self.call('install', '--pets-root', tmp)
            self.assertTrue(again['already_installed'])
            self.assertEqual(len(native_pet.status(root)['installed']), 1)

    def test_uninstall_and_restore_keep_a_recoverable_native_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.call('install', '--pets-root', tmp)
            report = self.call('uninstall', '--pets-root', tmp)
            self.assertFalse(Path(report['removed']).exists())
            restored = self.call('restore', report['backup'], '--pets-root', tmp)
            self.assertTrue(Path(restored['restored']).is_dir())
            self.assertTrue(native_pet.status(tmp)['installed'][0]['ok'])

    def test_export_contains_only_the_native_loader_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = native_pet.export(Path(tmp) / 'lumi.zip')
            with zipfile.ZipFile(report['archive']) as archive:
                prefix = native_pet.release_id() + '/'
                self.assertEqual(set(archive.namelist()), {prefix+'pet.json', prefix+'spritesheet.webp'})
                self.assertEqual(json.loads(archive.read(prefix+'pet.json'))['spriteVersionNumber'], 2)

    def test_corrupt_backup_is_rejected_without_replacing_installation(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.call('install', '--pets-root', tmp)
            report = self.call('install', '--force', '--pets-root', tmp)
            manifest = Path(report['backup']) / 'pet.json'
            obj = json.loads(manifest.read_text())
            obj['displayName'] = 'modified backup'
            manifest.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                native_pet.restore(report['backup'], tmp)
            self.assertTrue(native_pet.destination(tmp).is_dir())

    def test_restore_cannot_target_an_unrelated_pet(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.call('install', '--pets-root', tmp)
            report = self.call('uninstall', '--pets-root', tmp)
            backup = Path(report['backup'])
            receipt = backup.parent / f'{backup.name}.json'
            obj = json.loads(receipt.read_text())
            obj['installation_id'] = '../lumi'
            receipt.write_text(json.dumps(obj))
            with self.assertRaisesRegex(ValueError, 'installation ID'):
                native_pet.restore(backup, tmp)

    def test_retiring_old_release_keeps_current_release_and_can_be_restored(self):
        with tempfile.TemporaryDirectory() as tmp:
            current = self.call('install', '--pets-root', tmp)
            old_sheet = native_pet.ROOT / 'assets/pets/lumi-actions-v3/spritesheet.webp'
            old_id = 'lumi-project-' + hashlib.sha256(old_sheet.read_bytes()).hexdigest()[:12]
            if old_id == native_pet.release_id():
                self.skipTest('Current package is the original v3 release')
            old = Path(tmp) / old_id
            old.mkdir()
            shutil.copy2(old_sheet, old / 'spritesheet.webp')
            shutil.copy2(native_pet.PACKAGE / 'pet.json', old / 'pet.json')
            removed = self.call('uninstall', '--pets-root', tmp, '--release-id', old_id)
            self.assertFalse(old.exists())
            self.assertTrue(Path(current['destination']).is_dir())
            self.call('restore', removed['backup'], '--pets-root', tmp)
            self.assertTrue(old.is_dir())

    def test_old_release_option_does_not_accept_a_legacy_or_foreign_pet(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(ValueError, 'installation ID'):
                native_pet.remove(tmp, 'lumi')
