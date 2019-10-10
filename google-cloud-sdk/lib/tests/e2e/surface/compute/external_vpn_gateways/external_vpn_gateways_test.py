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
"""Integration tests for external VPN gateways labels."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib

from apitools.base.py.exceptions import HttpError
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from tests.lib import e2e_utils
from tests.lib.surface.compute import e2e_test_base


class ExternalVpnGatewaysGaTest(e2e_test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.GA
    self.external_vpn_gateway_name = next(e2e_utils.GetResourceNameGenerator(
        prefix='gcloud-compute-test-external-vpn-gateway'))

  def RunCompute(self, *cmd):
    return self.Run(('compute',) + cmd)

  def CleanUpResource(self, subcommand, name, *args):
    try:
      cmd = (subcommand, 'delete', name, '--quiet') + args
      self.RunCompute(*cmd)
    except exceptions.ToolException:
      pass
    except HttpError:
      pass

  @contextlib.contextmanager
  def _ExternalVpnGateway(self, name):
    try:
      yield self.RunCompute('external-vpn-gateways', 'create',
                            name, '--interfaces', '0=9.9.9.9')
    finally:
      self.CleanUpResource('external-vpn-gateways', name)

  def testExternalVpnGateway(self):
    with self._ExternalVpnGateway(self.external_vpn_gateway_name):
      self.AssertNewOutputContains(self.external_vpn_gateway_name)
      self.Run('compute external-vpn-gateways describe {0}'.format(
          self.external_vpn_gateway_name))
      self.AssertNewOutputContains('name: {0}'.format(
          self.external_vpn_gateway_name), reset=False)
      self.AssertNewOutputContains(
          'interfaces:\n- id: 0\n  ipAddress: 9.9.9.9', reset=False)
      self.AssertNewOutputContains(
          'redundancyType: SINGLE_IP_INTERNALLY_REDUNDANT', reset=False)


if __name__ == '__main__':
  e2e_test_base.main()
