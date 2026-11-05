"""Provide OpenSSL 1.1.x for Qt 5.15.2.

The old Qt repo path (tools_openssl_x64/x86) returns 404 now, so the
libraries are taken from other places.  Output layout (expected by
windeploy.py and appimage.py):
    ssl/bin/*.dll          (Windows)
    ssl/lib/lib*.so.*      (Linux)
"""
import common as c
from config import ssl_dir, os_name
import glob
import os
import re
import shutil
import subprocess
import sys
import urllib.request

c.print('>> Providing OpenSSL 1.1 for Qt for {}'.format(os_name))

if os_name == 'macos':
    exit(0)


def fresh(path):
    if os.path.lexists(path):
        if os.path.islink(path):
            os.remove(path)
        else:
            shutil.rmtree(path, ignore_errors=True)
    os.makedirs(path, exist_ok=True)


def windows():
    if os_name == 'win32':
        bases = [r'C:\Program Files (x86)\OpenSSL-Win32',
                 r'C:\Program Files (x86)\OpenSSL',
                 r'C:\Program Files\OpenSSL-Win32']
        names = ['libssl-1_1.dll', 'libcrypto-1_1.dll']
    else:
        bases = [r'C:\Program Files\OpenSSL-Win64',
                 r'C:\Program Files\OpenSSL']
        names = ['libssl-1_1-x64.dll', 'libcrypto-1_1-x64.dll']

    out = os.path.join(ssl_dir, 'bin')
    fresh(ssl_dir)
    os.makedirs(out, exist_ok=True)

    found = set()
    for base in bases:
        for name in names:
            for f in glob.glob(os.path.join(base, '**', name), recursive=True):
                c.print('>> Copying', f)
                shutil.copy(f, out)
                found.add(name)
    if len(found) != len(names):
        c.print('>> OpenSSL 1.1 DLLs not found, missing:',
                sorted(set(names) - found))
        c.print('>> Install them first: choco install openssl '
                '--version=1.1.1.2100 --allow-downgrade --force -y')
        exit(1)


def linux():
    base = 'http://security.ubuntu.com/ubuntu/pool/main/o/openssl/'
    pattern = r'libssl1\.1_1\.1\.1f-1ubuntu2[0-9.]*_amd64\.deb'
    try:
        html = urllib.request.urlopen(base).read().decode('utf-8', 'ignore')
        debs = set(re.findall(pattern, html))
    except Exception as e:
        c.print('>> Failed to list', base, e)
        debs = set()
    if not debs:
        debs = {'libssl1.1_1.1.1f-1ubuntu2.24_amd64.deb'}

    def key(n):
        return [int(x) for x in re.findall(r'\d+', n.split('ubuntu')[1])]
    deb = sorted(debs, key=key)[-1]

    c.download(base + deb, deb)
    tmp = os.path.abspath('ssl_deb')
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    subprocess.run(['dpkg-deb', '-x', deb, tmp], check=True)

    fresh(ssl_dir)
    out = os.path.join(ssl_dir, 'lib')
    os.makedirs(out, exist_ok=True)
    files = glob.glob(os.path.join(tmp, 'usr', 'lib', '*', 'lib*.so.1.1'))
    if not files:
        c.print('>> No libssl/libcrypto 1.1 found in', deb)
        exit(1)
    for f in files:
        c.print('>> Copying', f)
        shutil.copy(f, out)


if os_name.startswith('win'):
    windows()
else:
    linux()
