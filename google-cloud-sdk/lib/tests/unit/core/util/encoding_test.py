# -*- coding: utf-8 -*- #

# Copyright 2015 Google LLC. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for the encoding  module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import sys

from googlecloudsdk.core.util import encoding
from tests.lib import test_case
import six


_ASCII = 'Unicode'
_CP500 = _ASCII.encode('cp500')
_ISO_8859_1 = b'\xdc\xf1\xee\xe7\xf2\xd0\xe9'  # ÜñîçòÐé
_UNICODE = 'Ṳᾔḯ¢◎ⅾℯ'
_UTF8 = _UNICODE.encode('utf-8')


class DecodeTest(test_case.Base):

  def testDecodeAscii(self):
    expected = _ASCII
    actual = encoding.Decode(_ASCII)
    self.assertEqual(expected, actual)

  def testDecodeCp500(self):
    """This is a mutant killer."""
    expected = _CP500.decode('cp500')
    actual = encoding.Decode(_CP500, encoding='cp500')
    self.assertEqual(expected, actual)

  def testDecodeCp500FileSystemEncoding(self):
    """This is a mutant killer."""
    self.StartObjectPatch(sys, 'getfilesystemencoding', return_value='cp500')
    expected = _CP500.decode('cp500')
    actual = encoding.Decode(_CP500)
    self.assertEqual(expected, actual)

  def testDecodeCp500DefaultEncoding(self):
    """This is a mutant killer."""
    # We have to make sure getfilesystemencoding fails on all systems.
    self.StartObjectPatch(sys, 'getfilesystemencoding', return_value='ascii')
    self.StartObjectPatch(sys, 'getdefaultencoding', return_value='cp500')
    expected = _CP500.decode('cp500')
    actual = encoding.Decode(_CP500)
    self.assertEqual(expected, actual)

  def testDecodeIso8859_1(self):
    expected = _ISO_8859_1.decode('iso-8859-1')
    actual = encoding.Decode(_ISO_8859_1)
    self.assertEqual(expected, actual)

  def testDecodeUnicode(self):
    expected = _UNICODE
    actual = encoding.Decode(_UNICODE)
    self.assertEqual(expected, actual)

  def testDecodeUtf8(self):
    expected = _UTF8.decode('utf-8')
    actual = encoding.Decode(_UTF8)
    self.assertEqual(expected, actual)

  def testDecodeUtf8AttrKwarg(self):
    expected = _ISO_8859_1.decode('iso-8859-1')
    actual = encoding.Decode(_ISO_8859_1, encoding='utf-8')
    self.assertEqual(expected, actual)


class EncodingGetSetEncodedValueTests(test_case.Base):

  def testSetEncodedValueDict(self):
    d = {}
    self.assertEqual(d, {})
    encoding.SetEncodedValue(d, 'foo', '1')
    self.assertEqual(d, {'foo': '1'})

    encoding.SetEncodedValue(d, 'foo', '0')
    self.assertEqual(d, {'foo': '0'})

    encoding.SetEncodedValue(d, 'foo', None)
    self.assertEqual(d, {})

    encoding.SetEncodedValue(d, 'foo', None)
    self.assertEqual(d, {})

    encoding.SetEncodedValue(d, 'foo', '1')
    encoding.SetEncodedValue(d, 'bar', '2')
    self.assertEqual(d, {'foo': '1', 'bar': '2'})
    encoding.SetEncodedValue(d, 'bar', None)
    self.assertEqual(d, {'foo': '1'})

  def testSetEncodedValueAscii(self):
    d = {}
    self.assertEqual(d, {})
    value = 'ascii'
    encoding.SetEncodedValue(d, 'foo', value)
    raw = d['foo']
    # If we're in python 3, the raw value is not encoded. In python 2, the raw
    # value is encoded.
    self.assertEqual(six.PY3, isinstance(raw, six.text_type))
    actual = encoding.GetEncodedValue(d, 'foo')
    self.assertTrue(isinstance(actual, six.text_type))
    self.assertEqual(value, actual)

    actual = encoding.GetEncodedValue(d, 'bar')
    self.assertEqual(None, actual)

    actual = encoding.GetEncodedValue(d, 'bar', '')
    self.assertEqual('', actual)

  def testSetEncodedValueUnicode(self):
    self.StartObjectPatch(sys, 'getfilesystemencoding').return_value = 'utf-8'
    d = {}
    self.assertEqual(d, {})
    value = 'Ṳᾔḯ¢◎ⅾℯ'
    encoding.SetEncodedValue(d, 'foo', value)
    raw = d['foo']
    # If we're in python 3, the raw value is not encoded. In python 2, the raw
    # value is encoded.
    self.assertEqual(six.PY3, isinstance(raw, six.text_type))
    actual = encoding.GetEncodedValue(d, 'foo')
    self.assertTrue(isinstance(actual, six.text_type))
    self.assertEqual(value, actual)


if __name__ == '__main__':
  test_case.main()
