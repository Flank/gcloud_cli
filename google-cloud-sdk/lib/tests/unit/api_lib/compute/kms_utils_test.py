# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for googlecloudsdk.api_lib.compute.kms_utils."""

from googlecloudsdk.api_lib.compute import kms_utils
from googlecloudsdk.calliope import parser_errors
from tests.lib import test_case

DEFAULT_PROJECT = 'default-project'
KEY_PROJECT = 'key-project'
KEY_LOCATION = 'global'
KEY_KEYRING = 'ring'
KEY_NAME = 'my-key'
EXAMPLE_KEY = (
    'projects/key-project/locations/global/keyRings/ring/cryptoKeys/my-key')
EXAMPLE_KEY_IN_DEFAULT_PROJECT = ('projects/default-project/locations/global/'
                                  'keyRings/ring/cryptoKeys/my-key')


class EmptyClass(object):
  pass


class BootDiskKmsKey(object):

  def __init__(self):
    self.boot_disk_kms_key = KEY_NAME
    self.boot_disk_kms_project = KEY_PROJECT

  def MakeGetOrRaise(self, key):
    val = {
        'boot_disk_kms_key': self.boot_disk_kms_key,
        'boot_disk_kms_project': self.boot_disk_kms_project,
    }.get(key.strip('-').replace('-', '_'))
    def ValueFunc():
      if val:
        return val
      raise parser_errors.RequiredArgumentError('is required', key)
    return ValueFunc


class BootDiskKmsKeyWithParts(object):

  def __init__(self):
    self.boot_disk_kms_key = KEY_NAME
    self.boot_disk_kms_location = KEY_LOCATION
    self.boot_disk_kms_keyring = KEY_KEYRING
    self.boot_disk_kms_project = KEY_PROJECT

  def MakeGetOrRaise(self, key):
    val = {
        'boot_disk_kms_key': self.boot_disk_kms_key,
        'boot_disk_kms_location': self.boot_disk_kms_location,
        'boot_disk_kms_keyring': self.boot_disk_kms_keyring,
        'boot_disk_kms_project': self.boot_disk_kms_project,
    }.get(key.strip('-').replace('-', '_'))
    def ValueFunc():
      if val:
        return val
      raise parser_errors.RequiredArgumentError('is required', key)
    return ValueFunc


class KmsKeyUtilsTest(test_case.TestCase):

  def testDictToKmsKey(self):
    self.assertIsNone(kms_utils._DictToKmsKey(None, DEFAULT_PROJECT))
    self.assertIsNone(kms_utils._DictToKmsKey({}, DEFAULT_PROJECT))
    self.assertEquals(
        kms_utils._DictToKmsKey(
            {'kms-key': EXAMPLE_KEY}, DEFAULT_PROJECT).RelativeName(),
        EXAMPLE_KEY)
    self.assertEquals(
        kms_utils._DictToKmsKey(
            {'kms-key': KEY_NAME,
             'kms-keyring': KEY_KEYRING,
             'kms-location': KEY_LOCATION}, DEFAULT_PROJECT).RelativeName(),
        EXAMPLE_KEY_IN_DEFAULT_PROJECT)

  def testArgsToKmsKey(self):
    self.assertEquals(
        kms_utils._ArgsToKmsKey(EmptyClass(), DEFAULT_PROJECT),
        None)

    key = BootDiskKmsKey()
    key.boot_disk_kms_key = EXAMPLE_KEY
    key.boot_disk_kms_project = None
    self.assertEquals(
        kms_utils._ArgsToKmsKey(key, DEFAULT_PROJECT).RelativeName(),
        EXAMPLE_KEY)

    key_parts = BootDiskKmsKeyWithParts()
    key_parts.boot_disk_kms_project = None
    self.assertEquals(
        kms_utils._ArgsToKmsKey(key_parts, DEFAULT_PROJECT).RelativeName(),
        EXAMPLE_KEY_IN_DEFAULT_PROJECT)

  def testGetSpecifiedKmsArgs(self):
    self.assertEquals(kms_utils._GetSpecifiedKmsArgs(EmptyClass()), set([]))
    self.assertEquals(
        kms_utils._GetSpecifiedKmsArgs(BootDiskKmsKey()),
        set(['--boot-disk-kms-key', '--boot-disk-kms-project']))
    self.assertEquals(
        kms_utils._GetSpecifiedKmsArgs(BootDiskKmsKeyWithParts()),
        set(['--boot-disk-kms-key', '--boot-disk-kms-project',
             '--boot-disk-kms-location', '--boot-disk-kms-keyring']))

  def testGetSpecifiedKmsDict(self):
    self.assertIsNone(kms_utils._GetSpecifiedKmsDict({}))
    self.assertEquals(
        kms_utils._GetSpecifiedKmsDict({'kms-key': 'hi'}), set(['kms-key']))
    self.assertEquals(
        kms_utils._GetSpecifiedKmsDict(
            {'kms-key': 'hi', 'kms-location': 'global'}),
        set(['kms-key', 'kms-location']))
    self.assertEquals(
        kms_utils._GetSpecifiedKmsDict(
            {'kms-location': 'global', 'kms-key': 'hi'}),
        set(['kms-key', 'kms-location']))
    self.assertEquals(
        kms_utils._GetSpecifiedKmsDict({'kms-keyring': 'hi'}),
        set(['kms-keyring']))


if __name__ == '__main__':
  test_case.main()
