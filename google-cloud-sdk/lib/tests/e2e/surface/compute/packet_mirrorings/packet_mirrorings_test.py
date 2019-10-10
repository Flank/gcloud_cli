# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Integration tests for the packet-mirrorings command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.sdk_test_base import Retry
from tests.lib.surface.compute import e2e_test_base


class PacketMirroringsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.network_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='packet-mirrorings-test-network'))
    self.subnet_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='packet-mirrorings-test-subnet'))
    self.health_check_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='packet-mirrorings-test-health-check'))
    self.backend_service_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='packet-mirrorings-test-backend-service'))
    self.forwarding_rule_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='packet-mirrorings-test-forwarding-rule'))
    self.packet_mirroring_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='packet-mirrorings-test-pm'))

  def TearDown(self):
    logging.info('Starting Teardown (will delete resources if test fails).')
    self.CleanUpResource(
        self.packet_mirroring_name,
        'packet-mirrorings',
        scope=e2e_test_base.REGIONAL)

  def testBasicCommands(self):
    self.Run('compute networks create {0} --subnet-mode custom'.format(
        self.network_name))
    self.Run(('compute networks subnets create {0} --network {1} --region {2} '
              '--range 10.2.0.0/16').format(self.subnet_name, self.network_name,
                                            self.region))
    self.Run(
        'compute health-checks create http {0} --region {1} --port 80'.format(
            self.health_check_name, self.region))
    self.Run(('compute backend-services create {0} --region {1} '
              '--load-balancing-scheme internal '
              '--health-checks {2} --health-checks-region {3}').format(
                  self.backend_service_name, self.region,
                  self.health_check_name, self.region))

    self.Run(('compute forwarding-rules create {0} --region {1} '
              '--load-balancing-scheme internal --backend-service {2} '
              '--ports 80 --network {3} --subnet {4} --is-mirroring-collector'
             ).format(self.forwarding_rule_name, self.region,
                      self.backend_service_name, self.network_name,
                      self.subnet_name))

    self.Run(('compute packet-mirrorings create {0} --network {1} '
              '--region {2} --mirrored-tags t1,t2 --mirrored-subnets {3} '
              '--collector-ilb {4}').format(self.packet_mirroring_name,
                                            self.network_name, self.region,
                                            self.subnet_name,
                                            self.forwarding_rule_name))
    self.Run('compute packet-mirrorings list')
    self.AssertNewOutputContainsAll([
        'NAME REGION NETWORK PRIORITY ENABLE', '{0} {1} {2} 1000 TRUE'.format(
            self.packet_mirroring_name, self.region, self.network_name)
    ],
                                    normalize_space=True)
    self.Run('compute packet-mirrorings describe {0} --region {1}'.format(
        self.packet_mirroring_name, self.region))
    self.AssertNewOutputContainsAll(
        ['name: {0}'.format(self.packet_mirroring_name), 'subnetworks'])

    self.Run(('compute packet-mirrorings update {0} --region {1} '
              '--priority 900 --add-mirrored-tags t3 --clear-mirrored-subnets '
              '--no-enable').format(self.packet_mirroring_name, self.region))
    self.Run('compute packet-mirrorings describe {0} --region {1}'.format(
        self.packet_mirroring_name, self.region))
    self.AssertNewOutputContainsAll(
        ['enable: \'FALSE\'', 't3', 'priority: 900'], reset=False)
    self.AssertNewOutputNotContains('subnetworks')

    # Retry deletion in case resource was not ready yet.
    cmd = 'compute packet-mirrorings delete {0} --region {1}'.format(
        self.packet_mirroring_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute forwarding-rules delete {0} --region {1}'.format(
        self.forwarding_rule_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute backend-services delete {0} --region {1}'.format(
        self.backend_service_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute health-checks delete {0} --region {1}'.format(
        self.health_check_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks subnets delete {0} --region {1}'.format(
        self.subnet_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))


if __name__ == '__main__':
  e2e_test_base.main()
