import __future__
import doctest
import doctest
import ftputil
import unittest


def setUp(test):
    # ftputil.FTPHost defines a __del__ that stops the
    # garbage collector from working, and this shows up in an
    # annoying way during the tests
    try:
        del ftputil.FTPHost.__del__
    except AttributeError:
        pass


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocFileSuite(
        'export.txt', 'import.txt',
        setUp=setUp,
        globs={'with_statement': __future__.with_statement},
        optionflags=doctest.ELLIPSIS | doctest.NORMALIZE_WHITESPACE))
    return suite
