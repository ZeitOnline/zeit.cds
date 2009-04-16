# Copyright (c) 2008-2009 gocept gmbh & co. kg
# See also LICENSE.txt

import __future__

import unittest
import doctest

from zope.testing import doctest

def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(doctest.DocFileSuite(
        'export.txt', 'import.txt',
        globs={'with_statement': __future__.with_statement},
        optionflags=doctest.ELLIPSIS|doctest.NORMALIZE_WHITESPACE))
    return suite
