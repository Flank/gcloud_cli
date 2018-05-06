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
"""Tests that exercise IAM-related 'gcloud kms cryptokeys *' commands."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope.base import DeprecationException
from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptokeysIamTest(base.KmsMockTest):

  def SetUp(self):
    self.key_name = self.project_name.Descendant('global/my_kr/my_key')

  def testGet(self):
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys get-iam-policy '
               '--location={0} --keyring={1} {2}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))

  def testSet(self):
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys set-iam-policy '
               '--location={0} --keyring={1} {2} {3}'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id, 'fakefilename'))

  def testAddBinding(self):
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys add-iam-policy-binding '
               '--location={0} --keyring={1} {2} '
               '--member people --role roles/owner'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))

  def testRemoveBinding(self):
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys remove-iam-policy-binding '
               '--location={0} --keyring={1} {2} '
               '--member people --role roles/owner'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))


if __name__ == '__main__':
  test_case.main()
