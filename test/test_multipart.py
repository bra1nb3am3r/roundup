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
# $Id: test_multipart.py,v 1.4 2001/08/07 00:24:43 richard Exp $ 

import unittest, cStringIO

from roundup.mailgw import Message

class MultipartTestCase(unittest.TestCase):
    def setUp(self):
        self.fp = cStringIO.StringIO()
        w = self.fp.write
        w('Content-Type: multipart/mixed; boundary="foo"\r\n\r\n')
        w('This is a multipart message. Ignore this bit.\r\n')
        w('--foo\r\n')

        w('Content-Type: text/plain\r\n\r\n')
        w('Hello, world!\r\n')
        w('\r\n')
        w('Blah blah\r\n')
        w('foo\r\n')
        w('-foo\r\n')
        w('--foo\r\n')

        w('Content-Type: multipart/alternative; boundary="bar"\r\n\r\n')
        w('This is a multipart message. Ignore this bit.\r\n')
        w('--bar\r\n')

        w('Content-Type: text/plain\r\n\r\n')
        w('Hello, world!\r\n')
        w('\r\n')
        w('Blah blah\r\n')
        w('--bar\r\n')

        w('Content-Type: text/html\r\n\r\n')
        w('<b>Hello, world!</b>\r\n')
        w('--bar--\r\n')
        w('--foo\r\n')

        w('Content-Type: text/plain\r\n\r\n')
        w('Last bit\n')
        w('--foo--\r\n')
        self.fp.seek(0)

    def testMultipart(self):
        m = Message(self.fp)
        self.assert_(m is not None)

        # skip the first bit
        p = m.getPart()
        self.assert_(p is not None)
        self.assertEqual(p.fp.read(),
            'This is a multipart message. Ignore this bit.\r\n')

        # first text/plain
        p = m.getPart()
        self.assert_(p is not None)
        self.assertEqual(p.gettype(), 'text/plain')
        self.assertEqual(p.fp.read(),
            'Hello, world!\r\n\r\nBlah blah\r\nfoo\r\n-foo\r\n')

        # sub-multipart
        p = m.getPart()
        self.assert_(p is not None)
        self.assertEqual(p.gettype(), 'multipart/alternative')

        # sub-multipart text/plain
        q = p.getPart()
        self.assert_(q is not None)
        q = p.getPart()
        self.assert_(q is not None)
        self.assertEqual(q.gettype(), 'text/plain')
        self.assertEqual(q.fp.read(), 'Hello, world!\r\n\r\nBlah blah\r\n')

        # sub-multipart text/html
        q = p.getPart()
        self.assert_(q is not None)
        self.assertEqual(q.gettype(), 'text/html')
        self.assertEqual(q.fp.read(), '<b>Hello, world!</b>\r\n')

        # sub-multipart end
        q = p.getPart()
        self.assert_(q is None)

        # final text/plain
        p = m.getPart()
        self.assert_(p is not None)
        self.assertEqual(p.gettype(), 'text/plain')
        self.assertEqual(p.fp.read(),
            'Last bit\n')

        # end
        p = m.getPart()
        self.assert_(p is None)

def suite():
   return unittest.makeSuite(MultipartTestCase, 'test')


#
# $Log: test_multipart.py,v $
# Revision 1.4  2001/08/07 00:24:43  richard
# stupid typo
#
# Revision 1.3  2001/08/07 00:15:51  richard
# Added the copyright/license notice to (nearly) all files at request of
# Bizar Software.
#
# Revision 1.2  2001/07/29 07:01:39  richard
# Added vim command to all source so that we don't get no steenkin' tabs :)
#
# Revision 1.1  2001/07/28 06:43:02  richard
# Multipart message class has the getPart method now. Added some tests for it.
#
#
# vim: set filetype=python ts=4 sw=4 et si
