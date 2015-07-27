import argparse
import hashlib
import os
import requests
import sys

from clint.textui import progress

# http://stackoverflow.com/a/3431835
def hashfile(f, hasher, blocksize=65536):
    buf = f.read(blocksize)
    while len(buf) > 0:
        hasher.update(buf)
        buf = f.read(blocksize)
    return hasher.hexdigest()

parser = argparse.ArgumentParser()
parser.add_argument('packurl', help='The Solder pack API url')
args = parser.parse_args()

PACK_URL = args.packurl

session = requests.session()

pack_info = session.get(PACK_URL).json()

latest_pack_build = pack_info['latest']

pack_directory = pack_info['name']

if os.path.exists(pack_directory):
    print '+ Pack directory {} already exists, do you want to continue? [y/N]'.format(pack_directory),
    choice = raw_input().strip().lower()
    while choice not in ('y', 'n', ''):
        print 'Invalid option! [y/N]',
        choice = raw_input().strip().lower()
    if choice != 'y':
        print '+ Aborting'
        sys.exit(0)
else:
    print '+ Creating pack directory {}'.format(pack_directory)
    os.mkdir(pack_directory)

os.chdir(pack_directory)

build_info = session.get(PACK_URL + '/' + latest_pack_build).json()

for mod in build_info['mods']:
    output_filename = '{name}-{version}.zip'.format(**mod)
    if os.path.exists(output_filename):
        print '+ {} already exists, not redownloading'.format(output_filename)
    else:
        print '+ Downloading {name} at {version} to {fname}'.format(name=mod['name'], version=mod['version'], fname=output_filename)
        tmp_filename = output_filename + '.tmp'
        r = session.get(mod['url'], stream=True)
        total_length = int(r.headers.get('Content-Length'))
        with open(tmp_filename, 'wb') as f:
            for chunk in progress.bar(r.iter_content(chunk_size=1024), expected_size=(total_length / 1024.0) + 1):
                if chunk:
                    f.write(chunk)
            f.flush()
        os.rename(tmp_filename, output_filename)
    md5sum = ''
    with open(output_filename, 'rb') as f:
        md5sum = hashfile(f, hashlib.md5())
    if md5sum != mod['md5']:
        print "! Error: MD5 hash doesn't match (local: {} remote: {})".format(md5sum, mod['md5'])
        sys.exit(1)

print '+ Done!'
