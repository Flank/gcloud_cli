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
"""Gcloud tests that exercise network profiles listing."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.network import commands
from tests.lib.surface.firebase.test.network import fake_catalogs
from tests.lib.surface.firebase.test.network import unit_base


class TestNetworkProfilesListTest(unit_base.NetworkMockClientTest):

  def testNetworkProfilesList_NoConfigsFound(self):
    self.ExpectNetworkCatalogGet(fake_catalogs.EmptyNetworkConfigCatalog())
    self.Run(commands.NETWORK_PROFILES_LIST)
    self.AssertErrContains('Listed 0 items.')

  def testNetworkProfilesList_ConfigsFound(self):
    self.ExpectNetworkCatalogGet(fake_catalogs.FakeNetworkConfigCatalog())
    self.Run(commands.NETWORK_PROFILES_LIST)
    self.AssertOutputEquals(
        """+------------+
           | PROFILE_ID |
           +------------+
           | LTE |
           +------------+
           +------+-------+------------+-------------------+-----------+-------+
           | RULE | DELAY | LOSS_RATIO | DUPLICATION_RATIO | BANDWIDTH | BURST |
           +------+-------+------------+-------------------+-----------+-------+
           | up | 1 | 0.2 | 0.3 | 4.4 | 5.5 |
           | down | 6 | 0.7 | 0.8 | 9.9 | 10.0 |
           +------+-------+------------+-------------------+-----------+-------+
           +------------+
           | EDGE |
           +------------+
           +------+-------+------------+-------------------+-----------+-------+
           | RULE | DELAY | LOSS_RATIO | DUPLICATION_RATIO | BANDWIDTH | BURST |
           +------+-------+------------+-------------------+-----------+-------+
           | up | 10 | 0.02 | 0.03 | 0.44 | 0.55 |
           | down | 60 | 0.07 | 0.08 | 0.99 | 1.0 |
           +------+-------+------------+-------------------+-----------+-------+
        """, normalize_space=True)

  def testNetworkProfilesList_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('Error9', 'Environment catalog failure.')
    self.ExpectNetworkCatalogGetError(err)

    with self.assertRaises(exceptions.HttpException):
      self.Run(commands.NETWORK_PROFILES_LIST)

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.network-profiles\.list)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
