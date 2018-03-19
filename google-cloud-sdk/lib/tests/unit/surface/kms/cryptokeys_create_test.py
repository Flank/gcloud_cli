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
"""Tests that exercise the 'gcloud kms cryptokeys create' command."""

from googlecloudsdk.calliope.base import DeprecationException
from tests.lib import test_case
from tests.lib.surface.kms import base


class CryptokeysCreateTest(base.KmsMockTest):

  def SetUp(self):
    self.key_name = self.project_name.Descendant('global/my_kr/my_key')

  def testCreate(self):
    with self.assertRaises(DeprecationException):
      self.Run('kms cryptokeys create '
               '--location={0} --keyring={1} {2} --purpose=encryption'.format(
                   self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))


if __name__ == '__main__':
  test_case.main()
