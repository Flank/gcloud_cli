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

"""Tests that exercise describing network profiles in the device catalog."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.firebase.test import exceptions
from googlecloudsdk.calliope import exceptions as calliope_exceptions
from tests.lib import test_case
from tests.lib.surface.firebase.test import test_utils
from tests.lib.surface.firebase.test.network import commands
from tests.lib.surface.firebase.test.network import fake_catalogs
from tests.lib.surface.firebase.test.network import unit_base


class TestNetworkProfilesDescribeTest(unit_base.NetworkMockClientTest):

  def testNetworkProfilesDescribe_NetworkProfileNotFound(self):
    self.ExpectNetworkCatalogGet(fake_catalogs.FakeNetworkConfigCatalog())

    with self.assertRaises(exceptions.NetworkProfileNotFoundError):
      self.Run(commands.NETWORK_PROFILES_DESCRIBE + 'bad-profile')

    self.AssertErrContains("Could not find network profile ID 'bad-profile'")

  def testNetworkProfilesDescribe_NetworkProfileFound(self):
    self.ExpectNetworkCatalogGet(fake_catalogs.FakeNetworkConfigCatalog())
    self.Run(commands.NETWORK_PROFILES_DESCRIBE + 'EDGE')
    self.AssertOutputEquals("""downRule:
                                 bandwidth: 0.99
                                 burst: 1.0
                                 delay: '60'
                                 packetDuplicationRatio: 0.08
                                 packetLossRatio: 0.07
                               id: EDGE
                               upRule:
                                 bandwidth: 0.44
                                 burst: 0.55
                                 delay: '10'
                                 packetDuplicationRatio: 0.03
                                 packetLossRatio: 0.02
                            """, normalize_space=True)

  def testNetworkProfilesDescribe_ApiThrowsHttpError(self):
    err = test_utils.MakeHttpError('Error9', 'Environment catalog failure.')
    self.ExpectNetworkCatalogGetError(err)

    with self.assertRaises(calliope_exceptions.HttpException):
      self.Run(commands.NETWORK_PROFILES_DESCRIBE + 'LTE_nonexistent')

    self.AssertOutputEquals('')
    self.AssertErrMatches(r'(gcloud.*.test.network-profiles.describe)')
    self.AssertErrContains('Environment catalog failure.')


if __name__ == '__main__':
  test_case.main()
