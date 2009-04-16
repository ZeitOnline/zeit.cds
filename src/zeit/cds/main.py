# -*- coding: utf-8 -*-
# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt
# $Id$

import ftputil
import ftplib
import gocept.filestore
import os
import logging

log = logging.getLogger(__name__)

class FTPSession(ftplib.FTP):
    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to other port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)

def export(store_dir, hostname, port, user, password, upload_dir):
    filestore = gocept.filestore.filestore.FileStore(store_dir)
    filestore.prepare()
    log.info('Exporting files from Content-Drehscheibe at %s.' % store_dir)
    if not filestore.list('new'):
        log.debug("No new files to export. Exiting.")
        return

    log.debug(
        "Connecting to CDS FTP server "
        "(host %s, port %s, user %s, upload_dir %s)" %
        (hostname, port, user, upload_dir))
    try:
        host = ftputil.FTPHost(
            hostname, user, password, port=port, session_factory=FTPSession)
    except ftputil.FTPError:
        log.exception("Could not connect to CDS FTP server. Exiting")
        return

    try:
        write_lock_path = os.path.join(upload_dir, 'write')
        if host.path.exists(write_lock_path):
            log.debug("Cannot write on CDS FTP server as 'write' lockfile "
                         "exists. Exiting.")
            return

        log.debug("Creating lock file")
        f = host.open(write_lock_path, mode='wb')
        f.write('This is a lock file.')
        f.close()
        log.debug("Lock file successfully created")
    except ftputil.FTPError:
        log.exception("Error accessing FTP server. Exiting")
        return

    try:
        for item in filestore.list('new'):
            item_name = os.path.basename(item)
            upload_path = os.path.join(upload_dir, item_name)
            log.debug("Uploading: %s" % item_name)
            host.upload(item, upload_path, mode='b')
            filestore.move(item_name, 'new', 'cur')
            log.debug("Moved from 'new' to 'cur': %s" % item_name)
    except ftputil.FTPError:
        log.exception("Error while uploading file %s to FTP server. "
                          "Exiting." % item_name)
        return
    else:
        log.debug("Removing lock file")
        host.remove(write_lock_path)
        log.debug("Lock file successfully removed")
        host.close()
        log.info("Disconnected from CDS FTP server")
