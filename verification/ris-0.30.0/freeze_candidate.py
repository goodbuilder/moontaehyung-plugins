"""Freeze only the authorized plugin distribution; verify the bytes before testing the archive."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
from zipfile import ZipFile, ZIP_DEFLATED, ZipInfo


def digest(data):
    return hashlib.sha256(data).hexdigest()


def freeze(root, packet):
    files = sorted(p for p in subprocess.check_output(
        ['git','-C',str(root),'ls-files','-co','--exclude-standard','-z','.']).decode().split('\0') if p)
    manifest = {}
    archive = packet/'candidate-source.zip'
    # Refuse to replace an attested candidate. Select a new empty output for any new freeze.
    with ZipFile(archive, 'x', compression=ZIP_DEFLATED) as z:
        for rel in files:
            path = root/rel
            if path.is_symlink() or not path.is_file():
                raise ValueError('Unexpected distribution entry '+rel)
            data=path.read_bytes()
            manifest[rel]=digest(data)
            entry=ZipInfo('moontaehyung/'+rel,date_time=(2026,11,25,0,0,0))
            entry.create_system=3
            entry.external_attr=(stat.S_IFREG | (path.stat().st_mode & 0o777)) << 16
            entry.compress_type=ZIP_DEFLATED
            z.writestr(entry,data)
    manifest_bytes=(json.dumps(manifest,ensure_ascii=False,sort_keys=True,indent=2)+'\n').encode()
    (packet/'source-manifest.json').write_bytes(manifest_bytes)
    print(json.dumps(dict(base=subprocess.check_output(['git','-C',root,'rev-parse','HEAD'],text=True).strip(),
                          plugin_version=json.loads((root/'.codex-plugin/plugin.json').read_text())['version'],
                          files=len(files),manifest_sha256=digest(manifest_bytes),archive_sha256=digest(archive.read_bytes())),indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('source',type=Path)
    p.add_argument('empty_destination',type=Path)
    args=p.parse_args()
    args.empty_destination.mkdir(parents=True,exist_ok=True)
    freeze(args.source.resolve(),args.empty_destination.resolve())
