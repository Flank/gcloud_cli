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
"""Integration tests for manipulating interconnects."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import time

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib.surface.compute import e2e_test_base


@sdk_test_base.Filters.RunOnlyIfLongrunning
class AlphaInterconnectsTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.interconnect_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='interconnects-test-interconnect'))
    self.attachment_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='interconnects-test-attachment'))
    self.network_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='interconnects-test-network'))
    self.router_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='interconnects-test-router'))
    self.location = 'sjc-zone1-6'

  def GetRegion(self):
    return 'us-central1'

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    cmd = tuple(subcommand) + ('delete', name, '--quiet') + args
    self.RunCompute(*cmd)

  @contextlib.contextmanager
  def _InterconnectAttachment(self, name, interconnect, router, region):
    try:
      yield self.RunCompute('interconnects', 'attachments', 'create', name,
                            '--interconnect', interconnect, '--router', router,
                            '--region', region)
    finally:
      self.CleanUpResource(['interconnects', 'attachments'], name, '--region',
                           region)

  @contextlib.contextmanager
  def _Interconnect(self, name, location):
    try:
      yield self.RunCompute(
          'interconnects', 'create', name, '--interconnect-type=IT_PRIVATE',
          '--location', location, '--requested-link-count=1', '--admin-enabled',
          '--customer-name=gcloud-e2e-test',
          '--link-type=LINK_TYPE_ETHERNET_10G_LR')
    finally:
      self.CleanUpResource(['interconnects'], name)

  @contextlib.contextmanager
  def _Network(self, name):
    try:
      yield self.RunCompute('networks', 'create', name)
    finally:
      self.CleanUpResource(['networks'], name)

  @contextlib.contextmanager
  def _Router(self, name, network, region):
    try:
      yield self.RunCompute('routers', 'create', name, '--network', network,
                            '--region', region, '--asn', '65000')
    finally:
      self.CleanUpResource(['routers'], name, '--region', region)

  def testInterconnectsAndAttachments(self):
    with contextlib.nested(
        self._Interconnect(self.interconnect_name, self.location),
        self._Network(self.network_name),
        self._Router(self.router_name, self.network_name,
                     self.GetRegion())) as (interconnect_, _, _):

      # Check that created interconnects matches intended one.
      self.assertIsNotNone(interconnect_)
      self.assertEqual(self.interconnect_name, interconnect_.name)

      self.PollInterconnectUntilBecomeActive()

      updated_interconnect = self.RunCompute(
          'interconnects', 'update', self.interconnect_name, '--description',
          'this is my attachment')
      self.assertEqual('this is my attachment',
                       updated_interconnect.description)

      with self._InterconnectAttachment(
          self.attachment_name, self.interconnect_name, self.router_name,
          self.GetRegion()) as (attachment_):
        # Check that created attachments matches intended one.
        self.assertEqual(self.attachment_name, attachment_.name)
        # Add router interface.
        self.RunCompute('routers', 'add-interface', self.router_name,
                        '--region',
                        self.GetRegion(), '--interface-name', 'my-interface',
                        '--interconnect-attachment', self.attachment_name)

        router = self.RunCompute('routers', 'describe', self.router_name,
                                 '--region', self.GetRegion())
        self.assertEqual('my-interface', router.interfaces[0].name)

  def PollInterconnectUntilBecomeActive(self, timeout=35):
    """Wait until Interconnect reaches OS_ACTIVE or timeout.

    Args:
      timeout: timeout to raise exception.
    Raises:
      Exception: Interconnect took too long to become OS_ACTIVE.
    """
    start_time = time.time()
    end_time = start_time + timeout
    while time.time() <= end_time:
      interconnect = self.RunCompute('interconnects', 'describe',
                                     self.interconnect_name)
      if interconnect['operationalStatus'] == 'OS_ACTIVE':
        return
      time.sleep(5)
    raise Exception(
        'Interconnect took longer than {0} seconds to become OS_ACTIVE'.format(
            timeout))


@sdk_test_base.Filters.RunOnlyIfLongrunning
class BetaInterconnectsTest(AlphaInterconnectsTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.interconnect_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='interconnects-test-interconnect'))
    self.attachment_name = next(
        e2e_utils.GetResourceNameGenerator(
            prefix='interconnects-test-attachment'))
    self.network_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='interconnects-test-network'))
    self.router_name = next(
        e2e_utils.GetResourceNameGenerator(prefix='interconnects-test-router'))
    self.location = 'sjc-zone1-6'


if __name__ == '__main__':
  e2e_test_base.main()
