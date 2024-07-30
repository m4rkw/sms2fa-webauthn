#!/usr/bin/env python3

import zipfile
import os
import sys
import datetime

def create_idempotent_zip(zip_filename, *source_dirs):
    if os.path.exists(zip_filename):
        os.remove(zip_filename)

    def add_to_zip(zipf, file_path, arcname):
        zip_info = zipfile.ZipInfo(arcname)
        mtime = os.stat(file_path).st_mtime
        dt = datetime.datetime.fromtimestamp(mtime)
        zip_info.date_time = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        zip_info.external_attr = 0o644 << 16
        with open(file_path, 'rb') as f:
            zipf.writestr(zip_info, f.read())

    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for source_dir in source_dirs:
            for root, _, files in sorted(os.walk(source_dir)):
                for file in sorted(files):
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, start=source_dir)
                    add_to_zip(zipf, file_path, arcname)

if len(sys.argv) <3:
    print("usage: %s <filename> <path> [..]" % (sys.argv[0].split('/')[-1]))
    sys.exit()

create_idempotent_zip(sys.argv[1], *sys.argv[2:])
