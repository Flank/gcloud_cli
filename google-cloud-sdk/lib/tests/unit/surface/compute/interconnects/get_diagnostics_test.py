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
"""Tests for the interconnects get-diagnostics subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import resources
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.compute import test_base


# TODO(b/117336602) Stop using parameterized for track parameterization.
@parameterized.parameters((calliope_base.ReleaseTrack.ALPHA, 'alpha'),
                          (calliope_base.ReleaseTrack.BETA, 'beta'))
class InterconnectsDiagnosticsTest(
    parameterized.TestCase, test_base.BaseTest):

  def SelectApiVersion(self, track, api_version):
    self.track = track
    self.SelectApi(api_version)
    self.api_version = api_version
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)
    self.compute_message = getattr(self, 'compute_' + api_version)

  def testSimpleCase(self, track, api_version):
    self.SelectApiVersion(track, api_version)
    self.make_requests.side_effect = [[self.messages.InterconnectDiagnostics()]]
    self.Run("""
        compute interconnects get-diagnostics my-interconnect1
        """)
    self.CheckRequests(
        [(self.compute_message.interconnects, 'GetDiagnostics',
          self.messages.ComputeInterconnectsGetDiagnosticsRequest(
              project='my-project', interconnect='my-interconnect1'))],)

  def testWithUrl(self, track, api_version):
    self.SelectApiVersion(track, api_version)
    self.make_requests.side_effect = [[self.messages.InterconnectDiagnostics()]]
    self.Run('compute interconnects get-diagnostics https://www.googleapis.com/'
             'compute/' + api_version +
             '/projects/my-project/global/interconnects/'
             'my-interconnect1')
    self.CheckRequests(
        [(self.compute_message.interconnects, 'GetDiagnostics',
          self.messages.ComputeInterconnectsGetDiagnosticsRequest(
              project='my-project', interconnect='my-interconnect1'))],)


if __name__ == '__main__':
  test_case.main()
