#
# Copyright (c) 2001 Bizar Software Pty Ltd (http://www.bizarsoftware.com.au/)
# This module is free software, and you may redistribute it and/or modify
# under the same terms as Python, so long as this copyright message and
# disclaimer are retained in their original form.
#
# IN NO EVENT SHALL BIZAR SOFTWARE PTY LTD BE LIABLE TO ANY PARTY FOR
# DIRECT, INDIRECT, SPECIAL, INCIDENTAL, OR CONSEQUENTIAL DAMAGES ARISING
# OUT OF THE USE OF THIS CODE, EVEN IF THE AUTHOR HAS BEEN ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# BIZAR SOFTWARE PTY LTD SPECIFICALLY DISCLAIMS ANY WARRANTIES, INCLUDING,
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE.  THE CODE PROVIDED HEREUNDER IS ON AN "AS IS"
# BASIS, AND THERE IS NO OBLIGATION WHATSOEVER TO PROVIDE MAINTENANCE,
# SUPPORT, UPDATES, ENHANCEMENTS, OR MODIFICATIONS.
#
# $Id: test_mysql.py,v 1.11 2004/09/25 15:49:31 a1s Exp $

import unittest, os, shutil, time, imp

from roundup.hyperdb import DatabaseError
from roundup import init, backends

from db_test_base import DBTest, ROTest, config, SchemaTest, ClassicInitTest


class mysqlOpener:
    if hasattr(backends, 'mysql'):
        from roundup.backends import mysql as module

    def setUp(self):
        self.module.db_nuke(config)

    def tearDown(self):
        self.db.close()
        self.nuke_database()

    def nuke_database(self):
        self.module.db_nuke(config)

class mysqlDBTest(mysqlOpener, DBTest):
    def setUp(self):
        mysqlOpener.setUp(self)
        DBTest.setUp(self)

class mysqlROTest(mysqlOpener, ROTest):
    def setUp(self):
        mysqlOpener.setUp(self)
        ROTest.setUp(self)

class mysqlSchemaTest(mysqlOpener, SchemaTest):
    def setUp(self):
        mysqlOpener.setUp(self)
        SchemaTest.setUp(self)

class mysqlClassicInitTest(mysqlOpener, ClassicInitTest):
    backend = 'mysql'
    def setUp(self):
        mysqlOpener.setUp(self)
        ClassicInitTest.setUp(self)
    def tearDown(self):
        ClassicInitTest.tearDown(self)
        self.nuke_database()

from session_common import RDBMSTest
class mysqlSessionTest(mysqlOpener, RDBMSTest):
    def setUp(self):
        mysqlOpener.setUp(self)
        RDBMSTest.setUp(self)
    def tearDown(self):
        RDBMSTest.tearDown(self)
        mysqlOpener.tearDown(self)

def test_suite():
    suite = unittest.TestSuite()
    if not hasattr(backends, 'mysql'):
        print "Skipping mysql tests"
        return suite

    from roundup.backends import mysql
    try:
        # Check if we can run mysql tests
        import MySQLdb
        db = mysql.Database(config, 'admin')
        db.close()
    except (MySQLdb.ProgrammingError, DatabaseError), msg:
        print "Skipping mysql tests (%s)"%msg
    else:
        print 'Including mysql tests'
        suite.addTest(unittest.makeSuite(mysqlDBTest))
        suite.addTest(unittest.makeSuite(mysqlROTest))
        suite.addTest(unittest.makeSuite(mysqlSchemaTest))
        suite.addTest(unittest.makeSuite(mysqlClassicInitTest))
        suite.addTest(unittest.makeSuite(mysqlSessionTest))
    return suite

if __name__ == '__main__':
    runner = unittest.TextTestRunner()
    unittest.main(testRunner=runner)

# vim: set et sts=4 sw=4 :
