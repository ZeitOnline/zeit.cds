# -*- coding: utf-8 -*-
# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$

import ftputil
import ftplib
import gocept.filestore
import os
import logging


class FTPSession(ftplib.FTP):
    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to other port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)

def export(store_dir, server, port, user, password, upload_dir):
    filestore = gocept.filestore.filestore.FileStore(store_dir)
    filestore.prepare()
    logging.info("Accessed filestore %s" % store_dir)
    if not filestore.list('new'):
        logging.info("No new files to export. Exiting.")
        return

    logging.info(
        "Connecting to CDS FTP server "
        "(host %s, port %s, user %s, upload_dir %s)" %
        (server, port, user, upload_dir))
    host = ftputil.FTPHost(
        server, user, password, port=port, session_factory=FTPSession)

    
    write_lock_path = os.path.join(upload_dir, 'write')
    if host.path.exists(write_lock_path):
        logging.info("Cannot write on CDS FTP server as 'write' lockfile "
                     "exists. Exiting.")
        return

    logging.info("Creating lock file")
    f = host.open(write_lock_path, mode='wb')
    f.write('This is a lock file.')
    f.close()
    logging.info("Lock file successfully created")
    
    try:
        for item in filestore.list('new'):
            item_name = os.path.basename(item)
            upload_path = os.path.join(upload_dir, item_name)
            host.upload(item, upload_path, mode='b')
            logging.info("Uploaded file %s" % item_name)
            filestore.move(item_name, 'new', 'cur')
            logging.info("Moved file %s from 'new' to 'cur'" % item_name)
    finally:
        logging.info("Removing lock file")
        host.remove(write_lock_path)
        logging.info("Lock file successfully removed")
        host.close()
        logging.info("Disconnected from CDS FTP server")

