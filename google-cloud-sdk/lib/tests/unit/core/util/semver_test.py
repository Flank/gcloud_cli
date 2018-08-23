# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Unit tests for the semver module."""

from __future__ import absolute_import
from __future__ import print_function
from __future__ import unicode_literals
from googlecloudsdk.core.util import semver
from tests.lib import test_case


class SemverTest(test_case.TestCase):

  def Less(self, version1, version2, expected=True):
    semver1 = semver.SemVer(version1)
    semver2 = semver.SemVer(version2)
    self.assertEqual(expected, semver1 < semver2)
    self.assertEqual(expected, semver2 > semver1)
    self.assertEqual(not expected, semver1 >= semver2)
    self.assertEqual(not expected, semver2 <= semver1)

  def Equal(self, version1, version2, expected=True):
    semver1 = semver.SemVer(version1)
    semver2 = semver.SemVer(version2)
    self.assertEqual(expected, semver1 == semver2)
    self.assertEqual(not expected, semver1 != semver2)

  def Distance(self, version1, version2, expected):
    semver1 = semver.SemVer(version1)
    semver2 = semver.SemVer(version2)
    major, minor, patch = semver1.Distance(semver2)
    self.assertEqual(major, expected[0])
    self.assertEqual(minor, expected[1])
    self.assertEqual(patch, expected[2])

  def testDistance(self):
    self.Distance('1.0.0', '1.0.0', [0, 0, 0])
    self.Distance('1.1.0', '1.0.0', [0, 1, 0])
    self.Distance('1.0.0', '1.1.0', [0, -1, 0])
    self.Distance('1.0.1', '1.0.0', [0, 0, 1])
    self.Distance('1.0.0', '1.0.1', [0, 0, -1])
    self.Distance('2.0.0', '0.0.1', [2, 0, -1])

    self.Distance('1.0.0-alpha+asdf', '1.0.0-alpha+asdf', [0, 0, 0])
    self.Distance('1.0.0', '1.1.0-alpha', [0, -1, 0])
    self.Distance('1.0.1-alpha', '1.0.0', [0, 0, 1])
    self.Distance('1.0.0', '1.0.1-alpha+asdf', [0, 0, -1])
    self.Distance('2.0.0-alpha+asdf', '0.0.1', [2, 0, -1])

  def testBasicCompare(self):
    self.Equal('1.0.0', '1.0.0')
    self.Equal('1.1.0', '1.1.0')
    self.Equal('1.0.5', '1.0.5')
    self.Equal('1.0.5-alpha', '1.0.5-alpha')
    self.Equal('1.0.5-alpha', '1.0.5-alPHa', expected=False)
    self.Equal('1.0.5-alpha+asdf', '1.0.5-alpha+asdf')
    self.Equal('1.0.5+asdf', '1.0.5+jkl', expected=False)

    self.Less('0.0.0', '1.0.0')
    self.Less('0.0.0', '0.1.0')
    self.Less('0.0.0', '0.0.1')

    self.Less('1.0.0', '10.0.0')
    self.Less('11.0.0', '20.0.0')

    self.Less('0.1.0', '0.10.0')
    self.Less('0.11.0', '0.20.0')

    self.Less('0.0.1', '0.0.10')
    self.Less('0.0.11', '0.0.20')

  def testPreReleaseCompare(self):
    self.Equal('0.0.0-alpha', '0.0.0-alpha')
    self.Less('0.0.0-alpha', '0.0.0')
    self.Less('0.0.0', '0.0.0-alpha', expected=False)
    self.Less('0.0.0', '0.0.0', expected=False)
    self.Less('0.0.0', '0.0.0+foo', expected=False)
    self.Less('0.0.0+foo', '0.0.0', expected=False)
    self.Less('0.0.0+001', '0.0.0', expected=False)
    self.Less('0.0.0-alpha', '0.0.0-beta')
    self.Less('0.0.0-0', '0.0.0-1')
    self.Less('0.0.0-alp-ha.0', '0.0.0-alp-ha.1')
    self.Less('0.0.0-alpha.2', '0.0.0-alpha.10')
    self.Less('0.0.0-alpha.1.-b', '0.0.0-alpha.1.-c')
    self.Less('1.0.5-alpha', '1.0.5-alPHa', expected=False)
    self.Less('1.0.5-alPHa', '1.0.5-alpha', expected=False)
    self.Less('0.0.0-1.2.3-abc.456pdq.xyz789', '0.0.0-1.3.3-abc.456pdq.xyz789')
    self.Less('0.0.0-1.2.3-abc.456pdq.xyz789', '0.0.0-1.2.3-abc.a456pdq.xyz789')
    self.Less('0.0.0-1.2.3-abc.456pdq.xyz789', '0.0.0-a')

  def testBadParse(self):
    errors = [
        None,
        1,
        '',
        '0',
        '0.0',
        '0.0.0.',
        '-asdf',
        '0-asdf',
        'a.b.c',
        '01.0.0',
        '0a.0b.0c',
        '0.0.0-01',
        '0.0.0-a.01',
        '0.0.0-.0.',
        '0.0.0-0.0.',
        '0.0.0-..',
    ]

    for e in errors:
      with self.assertRaises(semver.ParseError):
        r = semver.SemVer(e)
        print(r.major, r.minor, r.patch, r.prerelease, r.build)
        print(e)


if __name__ == '__main__':
  test_case.main()
