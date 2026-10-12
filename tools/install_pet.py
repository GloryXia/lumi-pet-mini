"""Install the validated Lumi package, keeping a full backup on updates."""
import argparse
import json
import os
from pathlib import Path
import shutil
import tempfile
from datetime import datetime, timezone
from validate_pet import PACKAGE, validate


def install(destination, dry_run=False):
    report = validate()
    destination = Path(destination).expanduser().absolute()
    if destination.is_symlink():
        raise ValueError('Destination must not be a symlink')
    if destination.exists():
        manifest = destination / 'pet.json'
        if not manifest.is_file() or manifest.is_symlink():
            raise ValueError('Existing destination is not a pet package')
        if json.loads(manifest.read_text()).get('id') != 'lumi':
            raise ValueError('Refusing to replace a different pet')
    report.update(destination=str(destination), dry_run=dry_run)
    if dry_run:
        return report
    destination.parent.mkdir(parents=True, exist_ok=True)
    staged = Path(tempfile.mkdtemp(prefix='.lumi-stage-', dir=destination.parent))
    backup = None
    try:
        for name in ('pet.json', 'spritesheet.webp'):
            shutil.copy2(PACKAGE / name, staged / name)
        if destination.exists():
            backup_root = destination.parent / '.lumi-backups'
            backup_root.mkdir(exist_ok=True)
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup = backup_root / stamp
            os.replace(destination, backup)
        try:
            os.replace(staged, destination)
        except BaseException:
            if backup is not None:
                os.replace(backup, destination)
            raise
    finally:
        if staged.exists():
            shutil.rmtree(staged)
    report['backup'] = str(backup) if backup else None
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    default_root = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
    parser.add_argument('--dest', type=Path, default=default_root / 'pets/lumi')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    print(json.dumps(install(args.dest, args.dry_run), ensure_ascii=False, indent=2))
