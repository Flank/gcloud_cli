# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Integration tests for network list-ip-addresses."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class NetworkListIpAddressesTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.network_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='networks-list-ip-addresses'))

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    self.CleanUpResource(
        self.network_name, 'networks', scope=e2e_test_base.GLOBAL)

  def testListIpAddresses(self):
    self.Run('compute networks create {0} --subnet-mode auto'.format(
        self.network_name))
    self.Run('compute networks list-ip-addresses {0}'.format(self.network_name))
    self.AssertNewOutputContains(
        'TYPE IP_RANGE REGION OWNER PURPOSE', reset=False, normalize_space=True)
    self.AssertNewOutputContains(
        'SUBNETWORK ', reset=False, normalize_space=True)


if __name__ == '__main__':
  e2e_test_base.main()
