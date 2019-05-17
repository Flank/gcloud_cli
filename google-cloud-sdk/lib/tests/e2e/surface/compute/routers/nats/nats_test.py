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
"""Integration tests for nats."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib.sdk_test_base import Retry
from tests.lib.surface.compute import e2e_test_base


class NatsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.network_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-network'))
    self.router_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-router'))
    self.nat_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-nat'))
    self.address_name_1 = next(
        e2e_utils.GetResourceNameGenerator(prefix='routers-test-address-1'))
    self.address_name_2 = next(
        e2e_utils.GetResourceNameGenerator(prefix='routers-test-address-2'))

  def TearDown(self):
    logging.info('Starting TearDown (will delete resources if test fails).')
    self.CleanUpResource(
        self.router_name, 'routers', scope=e2e_test_base.REGIONAL)
    self.CleanUpResource(
        self.network_name, 'networks', scope=e2e_test_base.GLOBAL)

  def testBasicCommands(self):
    self.Run('compute networks create {0} --subnet-mode custom'.format(
        self.network_name))
    self.Run('compute routers create {0} --network {1} --region {2}'.format(
        self.router_name, self.network_name, self.region))

    self.Run(
        'compute routers nats create {0} --router {1} --region {2} '
        '--nat-all-subnet-ip-ranges --auto-allocate-nat-external-ips'.format(
            self.nat_name, self.router_name, self.region))

    self.Run(
        'compute routers nats describe {0} --router {1} --region {2}'.format(
            self.nat_name, self.router_name, self.region))
    self.AssertNewOutputContains('name: {0}'.format(self.nat_name))

    self.Run('compute routers get-status {0} --region {1}'.format(
        self.router_name, self.region))
    self.AssertNewOutputContains(self.nat_name)

    self.Run('compute routers nats list --router {0} --region {1}'.format(
        self.router_name, self.region))
    self.AssertNewOutputContains(self.nat_name)

    # Retry deletion in case resource was not ready yet.
    cmd = 'compute routers nats delete {0} --router {1} --region {2}'.format(
        self.nat_name, self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute routers delete {0} --region {1}'.format(
        self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))

  def testWithStaticIps(self):
    self.Run('compute networks create {0} --subnet-mode custom'.format(
        self.network_name))
    self.Run('compute routers create {0} --network {1} --region {2}'.format(
        self.router_name, self.network_name, self.region))
    self.Run('compute addresses create {0} {1} --region {2}'.format(
        self.address_name_1, self.address_name_2, self.region))
    self.Run('compute addresses describe {0} --region {1}'.format(
        self.address_name_1, self.region))
    output = self.GetNewOutput()
    # Output contains a line of the form "address: 10.1.2.3"
    ip_address_1 = [st for st in output.split('\n') if 'address' in st
                   ][0].split()[1]
    self.Run('compute addresses describe {0} --region {1}'.format(
        self.address_name_2, self.region))
    output = self.GetNewOutput()
    ip_address_2 = [st for st in output.split('\n') if 'address' in st
                   ][0].split()[1]

    self.Run('compute routers nats create {0} --router {1} --region {2} '
             '--nat-all-subnet-ip-ranges --nat-external-ip-pool {3},{4}'.format(
                 self.nat_name, self.router_name, self.region,
                 self.address_name_1, self.address_name_2))

    self.Run(
        'compute routers nats describe {0} --router {1} --region {2}'.format(
            self.nat_name, self.router_name, self.region))
    self.AssertNewOutputContains('name: {0}'.format(self.nat_name))

    self.Run('compute routers get-status {0} --region {1}'.format(
        self.router_name, self.region))
    output = self.GetNewOutput()
    self.assertTrue(self.nat_name in output)
    self.assertTrue(ip_address_1 in output)
    self.assertTrue(ip_address_2 in output)

    # Retry deletion in case resource was not ready yet.
    cmd = 'compute routers nats delete {0} --router {1} --region {2}'.format(
        self.nat_name, self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute routers delete {0} --region {1}'.format(
        self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute addresses delete {0} {1} --region {2}'.format(
        self.address_name_1, self.address_name_2, self.region)
    Retry(lambda: self.Run(cmd))


class NatsTestBeta(NatsTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.network_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-network'))
    self.router_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-router'))
    self.nat_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='routers-test-nat'))
    self.address_name_1 = next(
        e2e_utils.GetResourceNameGenerator(prefix='routers-test-address-1'))
    self.address_name_2 = next(
        e2e_utils.GetResourceNameGenerator(prefix='routers-test-address-2'))

  def testLogging(self):
    self.Run('compute networks create {0} --subnet-mode custom'.format(
        self.network_name))
    self.Run('compute routers create {0} --network {1} --region {2}'.format(
        self.router_name, self.network_name, self.region))

    self.Run('compute routers nats create {0} --router {1} --region {2} '
             '--nat-all-subnet-ip-ranges --auto-allocate-nat-external-ips '
             '--enable-logging '.format(
                 self.nat_name, self.router_name, self.region))

    self.Run(
        'compute routers nats describe {0} --router {1} --region {2}'.format(
            self.nat_name, self.router_name, self.region))
    self.AssertNewOutputContainsAll([
        'name: {0}'.format(self.nat_name), 'logConfig:', 'enable: true',
        # Default filter should be ALL.
        'filter: ALL'
    ])

    # Change the log filter, verify that it's reflected on describe
    self.Run('compute routers nats update {0} --router {1} --region {2} '
             '--log-filter TRANSLATIONS_ONLY'.format(
                 self.nat_name, self.router_name, self.region))
    self.Run(
        'compute routers nats describe {0} --router {1} --region {2}'.format(
            self.nat_name, self.router_name, self.region))
    self.AssertNewOutputContains('filter: TRANSLATIONS_ONLY')

    # Retry deletion in case resource was not ready yet.
    cmd = 'compute routers nats delete {0} --router {1} --region {2}'.format(
        self.nat_name, self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute routers delete {0} --region {1}'.format(
        self.router_name, self.region)
    Retry(lambda: self.Run(cmd))

    cmd = 'compute networks delete {0}'.format(self.network_name)
    Retry(lambda: self.Run(cmd))


if __name__ == '__main__':
  e2e_test_base.main()
