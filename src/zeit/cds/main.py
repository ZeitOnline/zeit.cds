# -*- coding: utf-8 -*-
# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$

import ftputil
import gocept.filestore


def export(store_dir, server, user, password, upload_dir):
    host = ftputil.FTPHost(server, user, password)

    filestore = gocept.filestore.filestore.FileStore(store_dir)
    filestore.prepare()

    write_lock_path = os.path.join(upload_dir, 'write')
    if host.path.exists(write_lock_path):
        #XXX: Logging
        return
    f = host.open(write_lock_path, mode='wb')
    f.write('This is a lock file.')
    f.close()

    try:
        for item in filestore.list('new'):
            item_name = os.path.basename(item)
            upload_path = os.path.join(upload_dir, item_name)
            host.upload(item, upload_path, mode='b')
            filestore.move(item_name, 'new', 'cur')
    finally:
        host.remove(write_lock_path)
