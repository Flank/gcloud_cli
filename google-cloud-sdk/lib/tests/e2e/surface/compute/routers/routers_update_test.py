# -*- coding: utf-8 -*- #
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
"""Integration tests for gcloud compute routers update."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.sdk_test_base import Retry
from tests.lib.surface.compute import e2e_test_base


class RoutersUpdateBetaTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.network_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-update-test-network'))
    self.router_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-update-test-router'))

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    self.CleanUpResource(
        self.router_name, 'routers', scope=e2e_test_base.REGIONAL)
    self.CleanUpResource(
        self.network_name, 'networks', scope=e2e_test_base.GLOBAL)

  def testUpdateAdvertisements(self):
    self.Run('compute networks create {0} --subnet-mode custom'
             .format(self.network_name))

    self.Run('compute routers create {0} --network {1} --region {2} '
             '--asn 65000'.format(self.router_name, self.network_name,
                                  self.region))

    self.Run('compute routers update {0} --region {1} '
             '--advertisement-mode CUSTOM '
             '--set-advertisement-groups ALL_SUBNETS '
             '--set-advertisement-ranges 10.0.10.0/30'.format(
                 self.router_name, self.region))
    self.Run('compute routers describe {0} --region {1}'
             .format(self.router_name, self.region))
    self.AssertNewOutputContainsAll(
        ['CUSTOM', 'ALL_SUBNETS', '10.0.10.0/30'],
        reset=True,
        normalize_space=True)

    # Test clearing custom advertisements via explicit Patch.
    self.Run('compute routers update {0} --region {1} '
             '--set-advertisement-groups= '
             '--set-advertisement-ranges='.format(self.router_name,
                                                  self.region))
    self.Run('compute routers describe {0} --region {1}'
             .format(self.router_name, self.region))
    self.AssertNewOutputNotContains(
        'ALL_SUBNETS', reset=False, normalize_space=True)
    self.AssertNewOutputNotContains(
        '10.0.10.0/30', reset=True, normalize_space=True)

    # Test clearing custom advertisements via switching to DEFAULT mode.
    self.Run('compute routers update {0} --region {1} '
             '--advertisement-mode CUSTOM '
             '--set-advertisement-groups ALL_SUBNETS '
             '--set-advertisement-ranges 10.0.10.0/30'.format(
                 self.router_name, self.region))
    self.WriteInput('y\n')
    self.Run('compute routers update {0} --region {1} '
             '--advertisement-mode DEFAULT'.format(self.router_name,
                                                   self.region))
    self.Run('compute routers describe {0} --region {1}'
             .format(self.router_name, self.region))
    self.AssertNewOutputContains(
        'advertiseMode: DEFAULT', reset=False, normalize_space=True)
    self.AssertNewOutputNotContains(
        'ALL_SUBNETS', reset=False, normalize_space=True)
    self.AssertNewOutputNotContains(
        '10.0.10.0/30', reset=False, normalize_space=True)

    cmd = 'compute routers delete {0} --region {1}'.format(
        self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))

  def testUpdateAdvertisementsIncremental(self):
    self.Run('compute networks create {0} --subnet-mode custom'
             .format(self.network_name))

    self.Run('compute routers create {0} --network {1} --region {2} '
             '--asn 65000'.format(self.router_name, self.network_name,
                                  self.region))

    self.Run('compute routers update {0} --region {1} '
             '--advertisement-mode CUSTOM'.format(self.router_name,
                                                  self.region))
    self.Run('compute routers update {0} --region {1} '
             '--add-advertisement-groups ALL_SUBNETS'.format(
                 self.router_name, self.region))
    self.Run('compute routers update {0} --region {1} '
             '--add-advertisement-ranges 10.0.10.0/30'.format(
                 self.router_name, self.region))
    self.Run('compute routers describe {0} --region {1}'
             .format(self.router_name, self.region))
    self.AssertNewOutputContainsAll(
        ['CUSTOM', 'ALL_SUBNETS', '10.0.10.0/30'],
        reset=True,
        normalize_space=True)

    # Test clearing custom advertisements via incremental remove commands.
    self.Run('compute routers update {0} --region {1} '
             '--remove-advertisement-groups ALL_SUBNETS'.format(
                 self.router_name, self.region))
    self.Run('compute routers update {0} --region {1} '
             '--remove-advertisement-ranges 10.0.10.0/30'.format(
                 self.router_name, self.region))
    self.Run('compute routers describe {0} --region {1}'
             .format(self.router_name, self.region))
    self.AssertNewOutputNotContains(
        'ALL_SUBNETS', reset=False, normalize_space=True)
    self.AssertNewOutputNotContains(
        '10.0.10.0/30', reset=False, normalize_space=True)

    cmd = 'compute routers delete {0} --region {1}'.format(
        self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))


if __name__ == '__main__':
  e2e_test_base.main()
