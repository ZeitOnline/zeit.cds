from pyftpdlib import ftpserver
import asyncore
import threading
                
_stop_serving = False

def start_ftp_server(dir, user='test', password='testpw',
                     host='', port=2001,
                     suppress_real_errors=True):
    # we don't want our FTP server to create all kinds of logging messages
    def dummy_logger(msg):
        pass
    ftpserver.log = dummy_logger
    ftpserver.logline = dummy_logger

    # this is dangerous as we might suppress real errors we want to
    # see during debugging. But we don't want the FTP server (on a
    # separate thread) to spit out a random traceback during
    # doctesting either.
    if suppress_real_errors:
        ftpserver.logerror = dummy_logger

    # we allow the user to read and write to the directory
    _authorizer = ftpserver.DummyAuthorizer()
    _authorizer.add_user(user, password, dir, perm='elradfmw')

    # we can now set up the ftp server
    class MyFTPHandler(ftpserver.FTPHandler):
        authorizer = _authorizer
    address = (host, port)
    ftpd = ftpserver.FTPServer(address, MyFTPHandler)

    # normally we'd start the server with serve_forever, but
    # we instead write a custom loop that we can actually shut
    # down during doctests when we call stop_ftp_server()
    global _stop_serving
    _stop_serving = False
    
    def run_ftp_server():
        map = asyncore.socket_map
        ftpd._map = ftpd.handler._map = map
        while map or ftpserver._tasks:
            if map:
                asyncore.poll(1, map)
            if ftpserver._tasks:
                ftpserver._scheduler()
            if _stop_serving:
                ftpd.close_all()

    # now we start the FTP server in a separate thread
    thread = threading.Thread(target=run_ftp_server)
    thread.start()

def stop_ftp_server():
    global _stop_serving
    _stop_serving = True
