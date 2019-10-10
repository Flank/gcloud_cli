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
"""Tests for googlecloudsdk.api_lib.compute.csek_utils."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.api_lib.compute import csek_utils
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import resources
from tests.lib import sdk_test_base


DISK1_NAME = 'hamlet'
DISK2_NAME = 'ophelia'
SAMPLE_WRAPPED_KEY = ('ea2QS4AIhWKprsmuk/mh7g3vdBDGiTcSynFASvJC/rs/3BmOnW'
                      'G8/kBsy/Ql9AnLaQ/EQtkCQgyUZcLlM+OmEqduWuoCkorp8xG8'
                      'h9Y5UrlVz4AZbmQd99UhPejuH2L1+qmU1bGmGVhV4mcJtZNDwO'
                      'o4rCHdMuu9czHCsvDQZtseJQmnjZO2e8NGOa0rd6CZkJtammM1'
                      '7wYEAixZ+DbLgvAvtl16p1FMsLQ8ArsjrNBd9ll9pb/+9dKMCy'
                      'NXyY/jOKRDrtg+AyKWjg0FifmjCvzZ0pYC+DCM6jJIc9IsX6Kp'
                      '4gNhJTPfzXCvhviqUNGM6xMMXUvq4fCaBoaHOdm66w==')


class CsekKeyUtilsTest(sdk_test_base.SdkBase):

  def SetUp(self):
    def CreateVersion(version):
      registry = resources.REGISTRY.Clone()
      registry.RegisterApiByName('compute', version)
      return registry
    self._registries = {
        'v1': CreateVersion('v1'),
        'beta': CreateVersion('beta'),
        'alpha': CreateVersion('alpha'),
    }

  def _MakeDiskRef(self, name='hamlet', version=None):
    version = version if version else 'v1'
    return self._registries[version].Create(
        'compute.disks',
        disk=name,
        zone='us-central1-f',
        project='proj1')

  def testBadUriPattern(self):
    with self.assertRaisesRegex(
        core_exceptions.Error,
        r'Invalid value for \[uri\] pattern: \[foo\]'):
      csek_utils.UriPattern('foo')

  def testParseFailEmptyString(self):
    with self.assertRaisesRegex(
        core_exceptions.Error,
        '(No JSON object could be decoded|Expecting value.*)'):
      csek_utils.CsekKeyStore._ParseAndValidate('')

  def testParseFailNotArray(self):
    with self.assertRaisesRegex(
        core_exceptions.Error,
        'Key file\'s top-level element must be a JSON list.'):
      csek_utils.CsekKeyStore._ParseAndValidate('{ }')

  def testParseFailShortKey(self):
    disk = self._MakeDiskRef()
    with self.assertRaisesRegex(
        core_exceptions.Error,
        r'Key should contain 44 characters \(including padding\), '
        r'but is \[4\] characters long.'):
      csek_utils.CsekKeyStore._ParseAndValidate('''
          [ {{ "uri": "{0}",
              "key": "asdf",
              "key-type": "raw" }} ]
          '''.format(disk))

  def testParseFailKeyNotBase64UrlChars(self):
    disk = self._MakeDiskRef()
    with self.assertRaisesRegex(
        core_exceptions.Error,
        r'Base64 encoded strings contain only'):
      csek_utils.CsekKeyStore._ParseAndValidate('''
          [ {{ "uri": "{0}",
              "key": "!bcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=",
              "key-type": "raw" }} ]
          '''.format(disk))

  def testParseFailBadPadding(self):
    disk = self._MakeDiskRef()
    with self.assertRaisesRegex(
        core_exceptions.Error,
        r'Bad padding.  Keys should end with an \'=\' character.'):
      csek_utils.CsekKeyStore._ParseAndValidate('''
          [ {{ "uri": "{0}",
              "key": "abcdefghijklmnopqrstuvwxyz1234567890AAAAAAAZ",
              "key-type": "raw" }} ]
          '''.format(disk))

  def testParseFaileBadKeyType(self):
    disk = self._MakeDiskRef()
    with self.assertRaisesRegex(
        core_exceptions.Error,
        r'Invalid key type \[rAW\]'):
      csek_utils.CsekKeyStore(
          """
          [ {{ "uri": "{0}",
               "key": "abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=",
               "key-type": "rAW" }} ]
          """.format(disk))

  def testParseOkEmpty(self):
    mks = csek_utils.CsekKeyStore('[]')
    self.assertEqual(len(mks), 0)

  def testExerciseSingletonFileRawKey(self):
    disk1 = self._MakeDiskRef(DISK1_NAME, 'v1')
    disk1_alpha = self._MakeDiskRef(DISK1_NAME, 'alpha')
    disk1_beta = self._MakeDiskRef(DISK1_NAME, 'beta')
    disk2 = self._MakeDiskRef(DISK2_NAME, 'v1')
    mks = csek_utils.CsekKeyStore(
        """
        [ {{ "uri": "{0}",
             "key": "abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=",
             "key-type": "raw" }} ]
        """.format(disk1))
    self.assertEqual(len(mks), 1)
    self.assertEqual(
        mks.LookupKey(disk1).key_material,
        'abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')
    self.assertEqual(
        mks.LookupKey(disk1_alpha).key_material,
        'abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')
    self.assertEqual(
        mks.LookupKey(disk1_beta).key_material,
        'abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=')
    self.assertEqual(mks.LookupKey(disk2), None)

  def testExerciseSingletonFileWrappedKeyAllowed(self):
    disk1 = self._MakeDiskRef(DISK1_NAME)
    disk2 = self._MakeDiskRef(DISK2_NAME)
    mks = csek_utils.CsekKeyStore(
        """
        [ {{ "uri": "{0}",
             "key": "{1}",
             "key-type": "rsa-encrypted" }} ]
        """.format(disk1, SAMPLE_WRAPPED_KEY),
        allow_rsa_encrypted=True)
    self.assertEqual(len(mks), 1)
    self.assertEqual(mks.LookupKey(disk1).key_material, SAMPLE_WRAPPED_KEY)
    self.assertEqual(mks.LookupKey(disk2), None)

  def testExerciseSingletonFileWrappedKeyNotAllowed(self):
    disk = self._MakeDiskRef()
    with self.assertRaisesRegex(csek_utils.BadKeyTypeException, re.escape(
        'Invalid key type [rsa-encrypted]: this feature is only allowed in the '
        'alpha and beta versions of this command.')):
      csek_utils.CsekKeyStore(
          """
          [ {{ "uri": "{0}",
               "key": "{1}",
               "key-type": "rsa-encrypted" }} ]
          """.format(disk, SAMPLE_WRAPPED_KEY))

  def testExerciseBadKeyInFileWithTwoEntries(self):
    disk1 = self._MakeDiskRef(DISK1_NAME, 'v1')
    disk2 = self._MakeDiskRef(DISK2_NAME, 'v1')
    with self.assertRaisesRegex(csek_utils.InvalidKeyException,
                                disk2.RelativeName()):
      csek_utils.CsekKeyStore(
          """
          [ {{ "uri": "{0}",
               "key": "abcdefghijklmnopqrstuvwxyz1234567890AAAAAAA=",
               "key-type": "raw" }},
            {{ "uri": "{1}",
               "key": "WaffleWaffleWaffleWaffleWaffleWaffleWaffleXX",
               "key-type": "raw" }} ]
          """.format(disk1, disk2))

if __name__ == '__main__':
  sdk_test_base.main()
