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
# $Id: test_db.py,v 1.43 2002/09/10 00:19:54 richard Exp $ 

import unittest, os, shutil, time

from roundup.hyperdb import String, Password, Link, Multilink, Date, \
    Interval, DatabaseError, Boolean, Number
from roundup import date, password
from roundup.indexer import Indexer

def setupSchema(db, create, module):
    status = module.Class(db, "status", name=String())
    status.setkey("name")
    user = module.Class(db, "user", username=String(), password=Password(),
        assignable=Boolean(), age=Number(), roles=String())
    user.setkey("username")
    file = module.FileClass(db, "file", name=String(), type=String(),
        comment=String(indexme="yes"))
    issue = module.IssueClass(db, "issue", title=String(indexme="yes"),
        status=Link("status"), nosy=Multilink("user"), deadline=Date(),
        foo=Interval(), files=Multilink("file"), assignedto=Link('user'))
    session = module.Class(db, 'session', title=String())
    session.disableJournalling()
    db.post_init()
    if create:
        status.create(name="unread")
        status.create(name="in-progress")
        status.create(name="testing")
        status.create(name="resolved")
    db.commit()

class MyTestCase(unittest.TestCase):
    def tearDown(self):
        if os.path.exists('_test_dir'):
            shutil.rmtree('_test_dir')

class config:
    DATABASE='_test_dir'
    MAILHOST = 'localhost'
    MAIL_DOMAIN = 'fill.me.in.'
    INSTANCE_NAME = 'Roundup issue tracker'
    ISSUE_TRACKER_EMAIL = 'issue_tracker@%s'%MAIL_DOMAIN
    ISSUE_TRACKER_WEB = 'http://some.useful.url/'
    ADMIN_EMAIL = 'roundup-admin@%s'%MAIL_DOMAIN
    FILTER_POSITION = 'bottom'      # one of 'top', 'bottom', 'top and bottom'
    ANONYMOUS_ACCESS = 'deny'       # either 'deny' or 'allow'
    ANONYMOUS_REGISTER = 'deny'     # either 'deny' or 'allow'
    MESSAGES_TO_AUTHOR = 'no'       # either 'yes' or 'no'
    EMAIL_SIGNATURE_POSITION = 'bottom'

class anydbmDBTestCase(MyTestCase):
    def setUp(self):
        from roundup.backends import anydbm
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        self.db = anydbm.Database(config, 'test')
        setupSchema(self.db, 1, anydbm)
        self.db2 = anydbm.Database(config, 'test')
        setupSchema(self.db2, 0, anydbm)

    def testStringChange(self):
        self.db.issue.create(title="spam", status='1')
        self.assertEqual(self.db.issue.get('1', 'title'), 'spam')
        self.db.issue.set('1', title='eggs')
        self.assertEqual(self.db.issue.get('1', 'title'), 'eggs')
        self.db.commit()
        self.assertEqual(self.db.issue.get('1', 'title'), 'eggs')
        self.db.issue.create(title="spam", status='1')
        self.db.commit()
        self.assertEqual(self.db.issue.get('2', 'title'), 'spam')
        self.db.issue.set('2', title='ham')
        self.assertEqual(self.db.issue.get('2', 'title'), 'ham')
        self.db.commit()
        self.assertEqual(self.db.issue.get('2', 'title'), 'ham')
        self.db.issue.set('1', title=None)
        self.assertEqual(self.db.issue.get('1', "title"), None)

    def testLinkChange(self):
        self.db.issue.create(title="spam", status='1')
        self.assertEqual(self.db.issue.get('1', "status"), '1')
        self.db.issue.set('1', status='2')
        self.assertEqual(self.db.issue.get('1', "status"), '2')
        self.db.issue.set('1', status=None)
        self.assertEqual(self.db.issue.get('1', "status"), None)

    def testMultilinkChange(self):
        u1 = self.db.user.create(username='foo')
        u2 = self.db.user.create(username='bar')
        self.db.issue.create(title="spam", nosy=[u1])
        self.assertEqual(self.db.issue.get('1', "nosy"), [u1])
        self.db.issue.set('1', nosy=[])
        self.assertEqual(self.db.issue.get('1', "nosy"), [])
        self.db.issue.set('1', nosy=[u1,u2])
        self.assertEqual(self.db.issue.get('1', "nosy"), [u1,u2])

    def testDateChange(self):
        self.db.issue.create(title="spam", status='1')
        a = self.db.issue.get('1', "deadline")
        self.db.issue.set('1', deadline=date.Date())
        b = self.db.issue.get('1', "deadline")
        self.db.commit()
        self.assertNotEqual(a, b)
        self.assertNotEqual(b, date.Date('1970-1-1 00:00:00'))
        self.db.issue.set('1', deadline=date.Date())
        self.db.issue.set('1', deadline=None)
        self.assertEqual(self.db.issue.get('1', "deadline"), None)

    def testIntervalChange(self):
        self.db.issue.create(title="spam", status='1')
        a = self.db.issue.get('1', "foo")
        self.db.issue.set('1', foo=date.Interval('-1d'))
        self.assertNotEqual(self.db.issue.get('1', "foo"), a)
        self.db.issue.set('1', foo=None)
        self.assertEqual(self.db.issue.get('1', "foo"), None)

    def testBooleanChange(self):
        userid = self.db.user.create(username='foo', assignable=1)
        self.db.user.create(username='foo2', assignable=0)
        a = self.db.user.get(userid, 'assignable')
        self.db.user.set(userid, assignable=0)
        self.assertNotEqual(self.db.user.get(userid, 'assignable'), a)
        self.db.user.set(userid, assignable=0)
        self.db.user.set(userid, assignable=1)
        self.db.user.set('1', assignable=None)
        self.assertEqual(self.db.user.get('1', "assignable"), None)

    def testNumberChange(self):
        self.db.user.create(username='foo', age='1')
        a = self.db.user.get('1', 'age')
        self.db.user.set('1', age='3')
        self.assertNotEqual(self.db.user.get('1', 'age'), a)
        self.db.user.set('1', age='1.0')
        self.db.user.set('1', age=None)
        self.assertEqual(self.db.user.get('1', "age"), None)

    def testNewProperty(self):
        self.db.issue.create(title="spam", status='1')
        self.db.issue.addprop(fixer=Link("user"))
        # force any post-init stuff to happen
        self.db.post_init()
        props = self.db.issue.getprops()
        keys = props.keys()
        keys.sort()
        self.assertEqual(keys, ['activity', 'assignedto', 'creation',
            'creator', 'deadline', 'files', 'fixer', 'foo', 'id', 'messages',
            'nosy', 'status', 'superseder', 'title'])
        self.assertEqual(self.db.issue.get('1', "fixer"), None)

    def testRetire(self):
        self.db.issue.create(title="spam", status='1')
        b = self.db.status.get('1', 'name')
        a = self.db.status.list()
        self.db.status.retire('1')
        # make sure the list is different 
        self.assertNotEqual(a, self.db.status.list())
        # can still access the node if necessary
        self.assertEqual(self.db.status.get('1', 'name'), b)
        self.db.commit()
        self.assertEqual(self.db.status.get('1', 'name'), b)
        self.assertNotEqual(a, self.db.status.list())

    def testSerialisation(self):
        self.db.issue.create(title="spam", status='1',
            deadline=date.Date(), foo=date.Interval('-1d'))
        self.db.commit()
        assert isinstance(self.db.issue.get('1', 'deadline'), date.Date)
        assert isinstance(self.db.issue.get('1', 'foo'), date.Interval)
        self.db.user.create(username="fozzy",
            password=password.Password('t. bear'))
        self.db.commit()
        assert isinstance(self.db.user.get('1', 'password'), password.Password)

    def testTransactions(self):
        # remember the number of items we started
        num_issues = len(self.db.issue.list())
        num_files = self.db.numfiles()
        self.db.issue.create(title="don't commit me!", status='1')
        self.assertNotEqual(num_issues, len(self.db.issue.list()))
        self.db.rollback()
        self.assertEqual(num_issues, len(self.db.issue.list()))
        self.db.issue.create(title="please commit me!", status='1')
        self.assertNotEqual(num_issues, len(self.db.issue.list()))
        self.db.commit()
        self.assertNotEqual(num_issues, len(self.db.issue.list()))
        self.db.rollback()
        self.assertNotEqual(num_issues, len(self.db.issue.list()))
        self.db.file.create(name="test", type="text/plain", content="hi")
        self.db.rollback()
        self.assertEqual(num_files, self.db.numfiles())
        for i in range(10):
            self.db.file.create(name="test", type="text/plain", 
                    content="hi %d"%(i))
            self.db.commit()
        num_files2 = self.db.numfiles()
        self.assertNotEqual(num_files, num_files2)
        self.db.file.create(name="test", type="text/plain", content="hi")
        self.db.rollback()
        self.assertNotEqual(num_files, self.db.numfiles())
        self.assertEqual(num_files2, self.db.numfiles())

    def testDestroyNoJournalling(self):
        self.innerTestDestroy(klass=self.db.session)

    def testDestroyJournalling(self):
        self.innerTestDestroy(klass=self.db.issue)

    def innerTestDestroy(self, klass):
        newid = klass.create(title='Mr Friendly')
        n = len(klass.list())
        self.assertEqual(klass.get(newid, 'title'), 'Mr Friendly')
        klass.destroy(newid)
        self.assertRaises(IndexError, klass.get, newid, 'title')
        self.assertNotEqual(len(klass.list()), n)
        if klass.do_journal:
            self.assertRaises(IndexError, klass.history, newid)

        # now with a commit
        newid = klass.create(title='Mr Friendly')
        n = len(klass.list())
        self.assertEqual(klass.get(newid, 'title'), 'Mr Friendly')
        self.db.commit()
        klass.destroy(newid)
        self.assertRaises(IndexError, klass.get, newid, 'title')
        self.db.commit()
        self.assertRaises(IndexError, klass.get, newid, 'title')
        self.assertNotEqual(len(klass.list()), n)
        if klass.do_journal:
            self.assertRaises(IndexError, klass.history, newid)

        # now with a rollback
        newid = klass.create(title='Mr Friendly')
        n = len(klass.list())
        self.assertEqual(klass.get(newid, 'title'), 'Mr Friendly')
        self.db.commit()
        klass.destroy(newid)
        self.assertNotEqual(len(klass.list()), n)
        self.assertRaises(IndexError, klass.get, newid, 'title')
        self.db.rollback()
        self.assertEqual(klass.get(newid, 'title'), 'Mr Friendly')
        self.assertEqual(len(klass.list()), n)
        if klass.do_journal:
            self.assertNotEqual(klass.history(newid), [])

    def testExceptions(self):
        # this tests the exceptions that should be raised
        ar = self.assertRaises

        #
        # class create
        #
        # string property
        ar(TypeError, self.db.status.create, name=1)
        # invalid property name
        ar(KeyError, self.db.status.create, foo='foo')
        # key name clash
        ar(ValueError, self.db.status.create, name='unread')
        # invalid link index
        ar(IndexError, self.db.issue.create, title='foo', status='bar')
        # invalid link value
        ar(ValueError, self.db.issue.create, title='foo', status=1)
        # invalid multilink type
        ar(TypeError, self.db.issue.create, title='foo', status='1',
            nosy='hello')
        # invalid multilink index type
        ar(ValueError, self.db.issue.create, title='foo', status='1',
            nosy=[1])
        # invalid multilink index
        ar(IndexError, self.db.issue.create, title='foo', status='1',
            nosy=['10'])

        #
        # key property
        # 
        # key must be a String
        ar(TypeError, self.db.user.setkey, 'password')
        # key must exist
        ar(KeyError, self.db.user.setkey, 'fubar')

        #
        # class get
        #
        # invalid node id
        ar(IndexError, self.db.issue.get, '1', 'title')
        # invalid property name
        ar(KeyError, self.db.status.get, '2', 'foo')

        #
        # class set
        #
        # invalid node id
        ar(IndexError, self.db.issue.set, '1', title='foo')
        # invalid property name
        ar(KeyError, self.db.status.set, '1', foo='foo')
        # string property
        ar(TypeError, self.db.status.set, '1', name=1)
        # key name clash
        ar(ValueError, self.db.status.set, '2', name='unread')
        # set up a valid issue for me to work on
        self.db.issue.create(title="spam", status='1')
        # invalid link index
        ar(IndexError, self.db.issue.set, '6', title='foo', status='bar')
        # invalid link value
        ar(ValueError, self.db.issue.set, '6', title='foo', status=1)
        # invalid multilink type
        ar(TypeError, self.db.issue.set, '6', title='foo', status='1',
            nosy='hello')
        # invalid multilink index type
        ar(ValueError, self.db.issue.set, '6', title='foo', status='1',
            nosy=[1])
        # invalid multilink index
        ar(IndexError, self.db.issue.set, '6', title='foo', status='1',
            nosy=['10'])
        # invalid number value
        ar(TypeError, self.db.user.create, username='foo', age='a')
        # invalid boolean value
        ar(TypeError, self.db.user.create, username='foo', assignable='true')
        self.db.user.create(username='foo')
        # invalid number value
        ar(TypeError, self.db.user.set, '3', username='foo', age='a')
        # invalid boolean value
        ar(TypeError, self.db.user.set, '3', username='foo', assignable='true')

    def testJournals(self):
        self.db.user.create(username="mary")
        self.db.user.create(username="pete")
        self.db.issue.create(title="spam", status='1')
        self.db.commit()

        # journal entry for issue create
        journal = self.db.getjournal('issue', '1')
        self.assertEqual(1, len(journal))
        (nodeid, date_stamp, journaltag, action, params) = journal[0]
        self.assertEqual(nodeid, '1')
        self.assertEqual(journaltag, 'test')
        self.assertEqual(action, 'create')
        keys = params.keys()
        keys.sort()
        self.assertEqual(keys, ['assignedto', 'deadline', 'files',
            'foo', 'messages', 'nosy', 'status', 'superseder', 'title'])
        self.assertEqual(None,params['deadline'])
        self.assertEqual(None,params['foo'])
        self.assertEqual([],params['nosy'])
        self.assertEqual('1',params['status'])
        self.assertEqual('spam',params['title'])

        # journal entry for link
        journal = self.db.getjournal('user', '1')
        self.assertEqual(1, len(journal))
        self.db.issue.set('1', assignedto='1')
        self.db.commit()
        journal = self.db.getjournal('user', '1')
        self.assertEqual(2, len(journal))
        (nodeid, date_stamp, journaltag, action, params) = journal[1]
        self.assertEqual('1', nodeid)
        self.assertEqual('test', journaltag)
        self.assertEqual('link', action)
        self.assertEqual(('issue', '1', 'assignedto'), params)

        # journal entry for unlink
        self.db.issue.set('1', assignedto='2')
        self.db.commit()
        journal = self.db.getjournal('user', '1')
        self.assertEqual(3, len(journal))
        (nodeid, date_stamp, journaltag, action, params) = journal[2]
        self.assertEqual('1', nodeid)
        self.assertEqual('test', journaltag)
        self.assertEqual('unlink', action)
        self.assertEqual(('issue', '1', 'assignedto'), params)

        # test disabling journalling
        # ... get the last entry
        time.sleep(1)
        entry = self.db.getjournal('issue', '1')[-1]
        (x, date_stamp, x, x, x) = entry
        self.db.issue.disableJournalling()
        self.db.issue.set('1', title='hello world')
        self.db.commit()
        entry = self.db.getjournal('issue', '1')[-1]
        (x, date_stamp2, x, x, x) = entry
        # see if the change was journalled when it shouldn't have been
        self.assertEqual(date_stamp, date_stamp2)
        self.db.issue.enableJournalling()
        self.db.issue.set('1', title='hello world 2')
        self.db.commit()
        entry = self.db.getjournal('issue', '1')[-1]
        (x, date_stamp2, x, x, x) = entry
        # see if the change was journalled
        self.assertNotEqual(date_stamp, date_stamp2)

    def testPack(self):
        self.db.issue.create(title="spam", status='1')
        self.db.commit()
        self.db.issue.set('1', status='2')
        self.db.commit()

        # sleep for at least a second, then get a date to pack at
        time.sleep(1)
        pack_before = date.Date('.')

        # one more entry
        self.db.issue.set('1', status='3')
        self.db.commit()

        # pack
        self.db.pack(pack_before)
        journal = self.db.getjournal('issue', '1')

        # we should have the create and last set entries now
        self.assertEqual(2, len(journal))

    def testIDGeneration(self):
        id1 = self.db.issue.create(title="spam", status='1')
        id2 = self.db2.issue.create(title="eggs", status='2')
        self.assertNotEqual(id1, id2)

    def testSearching(self):
        self.db.file.create(content='hello', type="text/plain")
        self.db.file.create(content='world', type="text/frozz",
            comment='blah blah')
        self.db.issue.create(files=['1', '2'], title="flebble plop")
        self.db.issue.create(title="flebble frooz")
        self.db.commit()
        self.assertEquals(self.db.indexer.search(['hello'], self.db.issue),
            {'1': {'files': ['1']}})
        self.assertEquals(self.db.indexer.search(['world'], self.db.issue), {})
        self.assertEquals(self.db.indexer.search(['frooz'], self.db.issue),
            {'2': {}})
        self.assertEquals(self.db.indexer.search(['flebble'], self.db.issue),
            {'2': {}, '1': {}})

    def testReindexing(self):
        self.db.issue.create(title="frooz")
        self.db.commit()
        self.assertEquals(self.db.indexer.search(['frooz'], self.db.issue),
            {'1': {}})
        self.db.issue.set('1', title="dooble")
        self.db.commit()
        self.assertEquals(self.db.indexer.search(['dooble'], self.db.issue),
            {'1': {}})
        self.assertEquals(self.db.indexer.search(['frooz'], self.db.issue), {})

    def testForcedReindexing(self):
        self.db.issue.create(title="flebble frooz")
        self.db.commit()
        self.assertEquals(self.db.indexer.search(['flebble'], self.db.issue),
            {'1': {}})
        self.db.indexer.quiet = 1
        self.db.indexer.force_reindex()
        self.db.post_init()
        self.db.indexer.quiet = 9
        self.assertEquals(self.db.indexer.search(['flebble'], self.db.issue),
            {'1': {}})

class anydbmReadOnlyDBTestCase(MyTestCase):
    def setUp(self):
        from roundup.backends import anydbm
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        db = anydbm.Database(config, 'test')
        setupSchema(db, 1, anydbm)
        self.db = anydbm.Database(config)
        setupSchema(self.db, 0, anydbm)
        self.db2 = anydbm.Database(config, 'test')
        setupSchema(self.db2, 0, anydbm)

    def testExceptions(self):
        # this tests the exceptions that should be raised
        ar = self.assertRaises

        # this tests the exceptions that should be raised
        ar(DatabaseError, self.db.status.create, name="foo")
        ar(DatabaseError, self.db.status.set, '1', name="foo")
        ar(DatabaseError, self.db.status.retire, '1')


class bsddbDBTestCase(anydbmDBTestCase):
    def setUp(self):
        from roundup.backends import bsddb
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        self.db = bsddb.Database(config, 'test')
        setupSchema(self.db, 1, bsddb)
        self.db2 = bsddb.Database(config, 'test')
        setupSchema(self.db2, 0, bsddb)

class bsddbReadOnlyDBTestCase(anydbmReadOnlyDBTestCase):
    def setUp(self):
        from roundup.backends import bsddb
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        db = bsddb.Database(config, 'test')
        setupSchema(db, 1, bsddb)
        self.db = bsddb.Database(config)
        setupSchema(self.db, 0, bsddb)
        self.db2 = bsddb.Database(config, 'test')
        setupSchema(self.db2, 0, bsddb)


class bsddb3DBTestCase(anydbmDBTestCase):
    def setUp(self):
        from roundup.backends import bsddb3
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        self.db = bsddb3.Database(config, 'test')
        setupSchema(self.db, 1, bsddb3)
        self.db2 = bsddb3.Database(config, 'test')
        setupSchema(self.db2, 0, bsddb3)

class bsddb3ReadOnlyDBTestCase(anydbmReadOnlyDBTestCase):
    def setUp(self):
        from roundup.backends import bsddb3
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        db = bsddb3.Database(config, 'test')
        setupSchema(db, 1, bsddb3)
        self.db = bsddb3.Database(config)
        setupSchema(self.db, 0, bsddb3)
        self.db2 = bsddb3.Database(config, 'test')
        setupSchema(self.db2, 0, bsddb3)


class gadflyDBTestCase(anydbmDBTestCase):
    ''' Gadfly doesn't support multiple connections to the one local
        database
    '''
    def setUp(self):
        from roundup.backends import gadfly
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        config.GADFLY_DATABASE = ('test', config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        self.db = gadfly.Database(config, 'test')
        setupSchema(self.db, 1, gadfly)

    def testIDGeneration(self):
        id1 = self.db.issue.create(title="spam", status='1')
        id2 = self.db.issue.create(title="eggs", status='2')
        self.assertNotEqual(id1, id2)

    def testNewProperty(self):
        # gadfly doesn't have an ALTER TABLE command :(
        pass

class gadflyReadOnlyDBTestCase(anydbmReadOnlyDBTestCase):
    def setUp(self):
        from roundup.backends import gadfly
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        config.GADFLY_DATABASE = ('test', config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        db = gadfly.Database(config, 'test')
        setupSchema(db, 1, gadfly)
        self.db = gadfly.Database(config)
        setupSchema(self.db, 0, gadfly)


class metakitDBTestCase(anydbmDBTestCase):
    def setUp(self):
        from roundup.backends import metakit
        import weakref
        metakit._instances = weakref.WeakValueDictionary()
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        self.db = metakit.Database(config, 'test')
        setupSchema(self.db, 1, metakit)
        self.db2 = metakit.Database(config, 'test')
        setupSchema(self.db2, 0, metakit)

    def testTransactions(self):
        # remember the number of items we started
        num_issues = len(self.db.issue.list())
        self.db.issue.create(title="don't commit me!", status='1')
        self.assertNotEqual(num_issues, len(self.db.issue.list()))
        self.db.rollback()
        self.assertEqual(num_issues, len(self.db.issue.list()))
        self.db.issue.create(title="please commit me!", status='1')
        self.assertNotEqual(num_issues, len(self.db.issue.list()))
        self.db.commit()
        self.assertNotEqual(num_issues, len(self.db.issue.list()))
        self.db.rollback()
        self.assertNotEqual(num_issues, len(self.db.issue.list()))
        self.db.file.create(name="test", type="text/plain", content="hi")
        self.db.rollback()
        for i in range(10):
            self.db.file.create(name="test", type="text/plain", 
                    content="hi %d"%(i))
            self.db.commit()
        # TODO: would be good to be able to ensure the file is not on disk after
        # a rollback...
        self.assertNotEqual(num_files, num_files2)
        self.db.file.create(name="test", type="text/plain", content="hi")
        self.db.rollback()

class metakitReadOnlyDBTestCase(anydbmReadOnlyDBTestCase):
    def setUp(self):
        from roundup.backends import metakit
        import weakref
        metakit._instances = weakref.WeakValueDictionary()
        # remove previous test, ignore errors
        if os.path.exists(config.DATABASE):
            shutil.rmtree(config.DATABASE)
        os.makedirs(config.DATABASE + '/files')
        db = metakit.Database(config, 'test')
        setupSchema(db, 1, metakit)
        self.db = metakit.Database(config)
        setupSchema(self.db, 0, metakit)
        self.db2 = metakit.Database(config, 'test')
        setupSchema(self.db2, 0, metakit)

def suite():
    l = [
         unittest.makeSuite(anydbmDBTestCase, 'test'),
         unittest.makeSuite(anydbmReadOnlyDBTestCase, 'test')
    ]
    #return unittest.TestSuite(l)

    try:
        import bsddb
        l.append(unittest.makeSuite(bsddbDBTestCase, 'test'))
        l.append(unittest.makeSuite(bsddbReadOnlyDBTestCase, 'test'))
    except:
        print 'bsddb module not found, skipping bsddb DBTestCase'

    try:
        import bsddb3
        l.append(unittest.makeSuite(bsddb3DBTestCase, 'test'))
        l.append(unittest.makeSuite(bsddb3ReadOnlyDBTestCase, 'test'))
    except:
        print 'bsddb3 module not found, skipping bsddb3 DBTestCase'

    try:
        import gadfly
        l.append(unittest.makeSuite(gadflyDBTestCase, 'test'))
        l.append(unittest.makeSuite(gadflyReadOnlyDBTestCase, 'test'))
    except:
        print 'gadfly module not found, skipping gadfly DBTestCase'

    try:
        import metakit
        l.append(unittest.makeSuite(metakitDBTestCase, 'test'))
        l.append(unittest.makeSuite(metakitReadOnlyDBTestCase, 'test'))
    except:
        print 'metakit module not found, skipping metakit DBTestCase'

    return unittest.TestSuite(l)

# vim: set filetype=python ts=4 sw=4 et si
