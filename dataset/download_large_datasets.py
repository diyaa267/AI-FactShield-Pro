from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import quote
import hashlib, json, zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'dataset' / 'large_sources'
OUT.mkdir(parents=True, exist_ok=True)

FILES = {
    'Gujarati_F&R_News.zip': ('77fec7e22af5e916816f3dc98a2781a7', 'https://zenodo.org/records/11408513/files/Gujarati_F%26R_News.zip?download=1'),
    'Hindi_F&R_News.zip': ('3be2e9e1f636472c99308a5eac1bb7e1', 'https://zenodo.org/records/11408513/files/Hindi_F%26R_News.zip?download=1'),
    'Marathi_F&R_News.zip': ('5aa6a5904c6812ead2a09448ffa51b38', 'https://zenodo.org/records/11408513/files/Marathi_F%26R_News.zip?download=1'),
    'Telugu_F&R_News.zip': ('de7c018e8c9346da73196c2f997fc6df', 'https://zenodo.org/records/11408513/files/Telugu_F%26R_News.zip?download=1'),
}


def md5(path):
    h = hashlib.md5()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def download(name, expected, url):
    path = OUT / name
    if path.exists() and md5(path).lower() == expected:
        print(f'[OK] {name} already downloaded and checksum matches')
        return path
    print(f'[DOWNLOAD] {name}')
    req = Request(url, headers={'User-Agent': 'AI-FactShield-Pro/1.0'})
    with urlopen(req, timeout=120) as r, path.open('wb') as f:
        total = int(r.headers.get('Content-Length') or 0)
        done = 0
        while True:
            chunk = r.read(1024 * 1024)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            if total:
                print(f'  {done/total*100:5.1f}%', end='\r')
    print()
    got = md5(path)
    if got.lower() != expected:
        raise RuntimeError(f'Checksum mismatch for {name}: expected {expected}, got {got}')
    print(f'[OK] {name} verified: {got}')
    return path


if __name__ == '__main__':
    manifest = {'source': 'Zenodo 10.5281/zenodo.11408513', 'files': {}}
    for name, (checksum, url) in FILES.items():
        p = download(name, checksum, url)
        manifest['files'][name] = {'path': str(p.relative_to(ROOT)), 'md5': checksum}
        with zipfile.ZipFile(p) as z:
            z.extractall(OUT / Path(name).stem)
    (OUT / 'download_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('Large multilingual dataset download complete.')
