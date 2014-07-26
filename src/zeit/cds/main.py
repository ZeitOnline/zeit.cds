# -*- coding: utf-8 -*-
# Copyright (c) 2009 gocept gmbh & co. kg
# See also LICENSE.txt

from __future__ import with_statement
import ftplib
import ftputil
import gocept.filestore
import logging
import logging.handlers
import os
import sys
import tempfile


log = logging.getLogger(__name__)


def setup_logging(logfile):
    if not logfile:
        return
    handler = logging.handlers.TimedRotatingFileHandler(
        logfile, when='D', interval=7, backupCount=5)
    handler.setFormatter(logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)


def export(store_dir, hostname, port, user, password, ftp_dir, logfile=None):
    setup_logging(logfile)
    log.info("Starting export.")

    filestore = _get_filestore(store_dir)

    with handle_ftp_session_error():
        if not filestore.list('new'):
            log.info("No new files to export.")
            return

        with ftp_session(hostname, port, user, password,
                         ftp_dir, 'write') as host:
            for item in sorted(filestore.list('new')):
                item_name = os.path.basename(item)
                upload_path = os.path.join(ftp_dir, item_name)
                log.info("Uploading: %s" % item_name)
                host.upload(item, upload_path, mode='b')
                filestore.move(item_name, 'new', 'cur')
                log.info("Moved from 'new' to 'cur': %s" % item_name)


def import_(store_dir, hostname, port, user, password, ftp_dir, logfile=None):
    setup_logging(logfile)
    log.info("Starting import.")

    filestore = _get_filestore(store_dir)

    with handle_ftp_session_error():
        with ftp_session(hostname, port, user, password,
                         ftp_dir, 'read') as host:
            files = sorted(host.listdir(ftp_dir))
            # there is always going to be a file 'read' but we will ignore this
            files.remove('read')
            if not files:
                log.info("No new files to import.")
                return
            for item in files:
                log.info("Downloading: %s" % item)
                dummy, path = tempfile.mkstemp(prefix='zeit.cds.')
                item_path = os.path.join(ftp_dir, item)
                try:
                    host.download(item_path, path, mode='b')
                    with filestore.create(item) as f:
                        with open(path, 'rb') as g:
                            f.write(g.read())
                finally:
                    host.remove(item_path)
                    log.info("File removed on server: %s" % item)
                    os.remove(path)
                filestore.move(item, 'tmp', 'new')
                log.info("Moved from 'tmp' to 'new': %s" % item)


class handle_ftp_session_error(object):
    def __enter__(self):
        pass

    def __exit__(self, type, value, traceback):
        if isinstance(value, FTPSessionError):
            if value.exc_info == (None, None, None):
                log.error("Exiting.")
            else:
                log.error("Exiting with exception:", exc_info=value.exc_info)
            return True
        log.error("Exiting with success.")


def _get_filestore(store_dir):
    filestore = gocept.filestore.FileStore(store_dir)
    filestore.prepare()
    log.info("Accessed filestore %s" % store_dir)
    return filestore


class FTPSession(ftplib.FTP):
    def __init__(self, host, userid, password, port):
        """Act like ftplib.FTP's constructor but connect to other port."""
        ftplib.FTP.__init__(self)
        self.connect(host, port)
        self.login(userid, password)


class FTPSessionError(Exception):
    def __init__(self, exc_info):
        self.exc_info = exc_info


class ftp_session(object):
    def __init__(self, hostname, port, user, password, ftp_dir, lock_name):
        self.hostname = hostname
        self.port = port
        self.user = user
        self.password = password
        self.ftp_dir = ftp_dir
        self.lock_name = lock_name
        self.lock_path = os.path.join(ftp_dir, lock_name)
        self.host = None

    def __enter__(self):
        log.info("Connecting to CDS FTP server "
                 "(host %s, port %s, user %s, dir %s)" %
                 (self.hostname, self.port, self.user, self.ftp_dir))

        try:
            host = self.host = ftputil.FTPHost(
                self.hostname, self.user, self.password,
                port=self.port, session_factory=FTPSession)
        except ftputil.FTPError:
            log.error("Could not connect to CDS FTP server.")
            raise FTPSessionError(sys.exc_info())

        try:
            for name in ['write', 'read']:
                if host.path.exists(os.path.join(self.ftp_dir, name)):
                    log.info("Cannot access CDS FTP server as '%s' lockfile "
                             "exists." % name)
                    raise FTPSessionError((None, None, None))
            log.info("Creating lock file: %s" % self.lock_name)
            f = host.open(self.lock_path, mode='wb')
            f.write('This is a lock file.')
            f.close()
            log.info("Lock file successfully created: %s" % self.lock_name)
        except ftputil.FTPError:
            log.error("Error accessing FTP server.")
            raise FTPSessionError(sys.exc_info())
        return host

    def __exit__(self, type, value, traceback):
        if isinstance(value, ftputil.FTPError):
            log.error("Error accessing FTP server.")
            raise FTPSessionError((type, value, traceback))
        log.info("Removing lock file: %s" % self.lock_name)
        try:
            self.host.remove(self.lock_path)
            log.info("Lock file successfully removed: %s" % self.lock_name)
            self.host.close()
            log.info("Disconnected from CDS FTP server")
        except ftputil.FTPError, e:
            log.error("Error accessing FTP server.")
            raise FTPSessionError(sys.exc_info())
