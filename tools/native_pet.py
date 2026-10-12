"""Manage Lumi's native package through the host's local pet directory contract."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import struct
import subprocess
import sys
import zipfile
from install_pet import install
from validate_pet import ROOT, validate, validate_structure

PROJECT = json.loads((ROOT / 'native/project.json').read_text())
PROJECT_ID = PROJECT['project_id']
PACKAGE = ROOT / PROJECT['package_directory']


def pet_root():
    return Path(os.environ.get('CODEX_HOME', Path.home() / '.codex')).expanduser() / 'pets'


def release_id():
    digest = hashlib.sha256((PACKAGE / 'spritesheet.webp').read_bytes()).hexdigest()
    return f'{PROJECT_ID}-{digest[:12]}'


def destination(root=None):
    return Path(root or pet_root()) / release_id()


def archive_entries(archive):
    with Path(archive).open('rb') as stream:
        header = struct.unpack('<4I', stream.read(16))
        if header[3] > 40_000_000:
            raise ValueError('Unexpected ASAR header size')
        tree = json.loads(stream.read(header[3]))
    def walk(node, prefix=''):
        for name, entry in node.get('files', {}).items():
            path = f'{prefix}/{name}' if prefix else name
            if 'files' in entry:
                yield from walk(entry, path)
            else:
                yield path, entry
    return 8 + header[1], list(walk(tree))


def inspect_host(app=None):
    if sys.platform != 'darwin' and app is None:
        return {'detected': False, 'reason': 'Use --app to inspect a macOS app bundle; pet files can still be installed on other platforms.'}
    candidates = [Path(app)] if app else [Path('/Applications/Codex.app'), Path('/Applications/ChatGPT.app')]
    bundle = next((p for p in candidates if (p / 'Contents/Info.plist').is_file()), None)
    if bundle is None:
        return {'detected': False, 'reason': 'Codex App bundle not found'}
    info = plistlib.loads((bundle / 'Contents/Info.plist').read_bytes())
    result = {'detected': True, 'app': str(bundle), 'bundle_id': info.get('CFBundleIdentifier'),
              'version': info.get('CFBundleShortVersionString'), 'local_pet_loader_detected': False}
    if result['bundle_id'] != 'com.openai.codex':
        result['compatible'] = False
        result['reason'] = 'Unexpected application bundle identifier'
        return result
    archive = bundle / 'Contents/Resources/app.asar'
    if not archive.is_file():
        result.update(compatible=False, reason='Cannot inspect the installed pet loader')
        return result
    offset, entries = archive_entries(archive)
    with archive.open('rb') as stream:
        for path, entry in entries:
            if not path.startswith('.vite/build/') or not path.endswith('.js') or entry.get('unpacked'):
                continue
            if entry.get('size', 0) > 30_000_000:
                continue
            stream.seek(offset + int(entry['offset']))
            text = stream.read(entry['size']).decode('utf-8', errors='replace')
            if all(marker in text for marker in ('spriteVersionNumber', 'pet.json', 'custom:', '1536', '2288')):
                result.update(local_pet_loader_detected=True, compatible=True, loader_file=path)
                break
    result.setdefault('compatible', False)
    result['inspection'] = 'Read-only installed loader inspection; no host binaries or settings are modified.'
    return result


def status(root=None):
    folder = Path(root or pet_root())
    items = []
    for path in sorted(folder.glob(f'{PROJECT_ID}-*')):
        if not path.is_dir() or path.is_symlink():
            continue
        try:
            report, _ = validate_structure(path)
            matches_version = path.name == f"{PROJECT_ID}-{report['sha256'][:12]}"
            items.append({'directory': str(path), 'host_id': f'custom:{path.name}',
                          'current': path.name == release_id(), 'ok': matches_version, 'sha256': report['sha256']})
        except (OSError, ValueError, KeyError) as error:
            items.append({'directory': str(path), 'current': path.name == release_id(),
                          'ok': False, 'error': str(error)})
    return {'pet_root': str(folder), 'current_release_id': release_id(), 'installed': items,
            'legacy_lumi_present': (folder / 'lumi/pet.json').is_file(),
            'note': 'File status does not imply selection in the app. Refresh My pets and choose the project entry.'}


def export(output=None):
    report = validate(PACKAGE)
    path = Path(output or ROOT / 'dist' / f'{release_id()}.zip').expanduser().absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name in ('pet.json', 'spritesheet.webp'):
            archive.write(PACKAGE / name, f'{release_id()}/{name}')
    return {**report, 'archive': str(path), 'install_directory': release_id()}


def restore(backup, root=None):
    root = Path(root or pet_root()).expanduser().absolute()
    backup = Path(backup).expanduser().absolute()
    backup_root = root / '.lumi-backups'
    if backup.is_symlink() or not backup.is_dir() or backup.resolve().parent != backup_root.resolve():
        raise ValueError('Backup must be a directory in the target pet root .lumi-backups')
    metadata_path = backup_root / f'{backup.name}.json'
    metadata = json.loads(metadata_path.read_text())
    name = metadata['installation_id']
    if not re.fullmatch(r'lumi-project-[0-9a-f]{12}', name):
        raise ValueError('Invalid project backup installation ID')
    report, _ = validate_structure(backup)
    if report['sha256'] != metadata['sha256']:
        raise ValueError('Backup sprite changed since it was saved')
    if hashlib.sha256((backup / 'pet.json').read_bytes()).hexdigest() != metadata['manifest_sha256']:
        raise ValueError('Backup manifest changed since it was saved')
    target = root / name
    saved_current = None
    if target.is_symlink():
        raise ValueError('Installation must not be a symlink')
    if target.exists():
        current, _ = validate_structure(target)
        if current['id'] != PROJECT_ID:
            raise ValueError('Refusing to replace an unrelated pet during restore')
        saved_current = backup_root / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        os.replace(target, saved_current)
    try:
        os.replace(backup, target)
    except BaseException:
        if saved_current is not None:
            os.replace(saved_current, target)
        raise
    if saved_current:
        save_receipt(saved_current, name)
    metadata_path.unlink()
    return {'ok': True, 'restored': str(target), 'previous_install_backup': str(saved_current) if saved_current else None}


def remove(root=None):
    root = Path(root or pet_root()).expanduser().absolute()
    target = destination(root)
    if not target.exists():
        return {'ok': True, 'already_absent': True, 'destination': str(target)}
    validate(target)
    backup_root = root / '.lumi-backups'
    backup_root.mkdir(exist_ok=True)
    backup = backup_root / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    if target.is_symlink():
        raise ValueError('Installation must not be a symlink')
    metadata = backup_root / f'{backup.name}.json'
    save_receipt(target, target.name, metadata)
    try:
        os.replace(target, backup)
    except BaseException:
        metadata.unlink()
        raise
    return {'ok': True, 'removed': str(target), 'backup': str(backup)}


def save_receipt(backup, installation_id, path=None):
    report, _ = validate_structure(backup)
    receipt = {'installation_id': installation_id, 'sha256': report['sha256'],
               'manifest_sha256': hashlib.sha256((backup / 'pet.json').read_bytes()).hexdigest()}
    path = path or backup.parent / f'{backup.name}.json'
    Path(path).write_text(json.dumps(receipt, indent=2)+'\n')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    doctor_parser = sub.add_parser('doctor', help='Validate the package and inspect the installed native host')
    doctor_parser.add_argument('--app', type=Path)
    for command in ('install', 'status', 'uninstall', 'restore'):
        p = sub.add_parser(command)
        p.add_argument('--pets-root', type=Path)
        if command == 'install':
            p.add_argument('--dry-run', action='store_true')
            p.add_argument('--force', action='store_true')
        if command == 'restore':
            p.add_argument('backup', type=Path)
    p = sub.add_parser('export')
    p.add_argument('--output', type=Path)
    sub.add_parser('open-settings', help='Open the host settings using its public URL scheme')
    args = parser.parse_args(argv)
    try:
        if args.command == 'doctor':
            result = {'project_version': PROJECT['release_version'], 'package': validate(PACKAGE),
                      'host': inspect_host(args.app), 'installation': status()}
        elif args.command == 'install':
            target = destination(args.pets_root)
            result = install(target, args.dry_run, package=PACKAGE, force=args.force)
            result['host_id'] = f'custom:{target.name}'
            result['next_step'] = 'In Mini & Pets, refresh My pets and select 露米 Lumi · 项目版.'
            if result.get('backup'):
                backup = Path(result['backup'])
                save_receipt(backup, target.name)
        elif args.command == 'status':
            result = status(args.pets_root)
        elif args.command == 'export':
            result = export(args.output)
        elif args.command == 'restore':
            result = restore(args.backup, args.pets_root)
        elif args.command == 'uninstall':
            result = remove(args.pets_root)
        else:
            if sys.platform == 'darwin':
                subprocess.run(['open', 'codex://settings'], check=True)
            elif sys.platform == 'win32':
                os.startfile('codex://settings')
            else:
                raise ValueError('Open Mini & Pets manually in your native app')
            result = {'ok': True, 'opened': 'codex://settings', 'next_step': 'Choose Mini & Pets.'}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, KeyError, struct.error, subprocess.CalledProcessError) as error:
        print(json.dumps({'ok': False, 'error': str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
