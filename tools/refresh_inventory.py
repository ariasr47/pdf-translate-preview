"""Refresh checksums after reviewing source edits; never adds/removes inventory entries.

Run from this source preview: python tools/refresh_inventory.py
Review and commit the resulting SHA256SUMS.json diff along with the source change.
Checksums bind bytes, not their safety or correctness. Run tests separately.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath


def refresh(root):
    root=Path(root).resolve()
    manifest=root/'SHA256SUMS.json'
    if manifest.is_symlink():raise ValueError('manifest must not be a symlink')
    old=json.loads(manifest.read_text(encoding='utf-8'))
    result={}
    for name in old:
        relative=PurePosixPath(name)
        if (relative.is_absolute() or '..' in relative.parts or '\\' in name
                or ':' in name or name=='SHA256SUMS.json'):
            raise ValueError('invalid inventory path')
        path=root.joinpath(*relative.parts)
        if (not path.is_file() or path.is_symlink()
                or any(p.is_symlink() for p in path.parents if p != root and p.is_relative_to(root))
                or not path.resolve().is_relative_to(root)):
            raise ValueError('inventory file missing or linked: '+name)
        result[name]=hashlib.sha256(path.read_bytes()).hexdigest()
    changed=[name for name in sorted(old) if old[name]!=result[name]]
    manifest.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    return changed


if __name__=='__main__':
    for name in refresh(Path(__file__).resolve().parents[1]):print('Updated checksum: '+name)
