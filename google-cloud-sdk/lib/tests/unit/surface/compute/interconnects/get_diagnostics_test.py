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

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class InterconnectsDiagnosticsAlphaTest(test_base.BaseTest):

  def Project(self):
    return 'my-project'

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    self.api_version = 'alpha'
    self.v1_messages = core_apis.GetMessagesModule('compute', self.api_version)
    self.resources = resources.REGISTRY.Clone()
    self.resources.RegisterApiByName('compute', self.api_version)

  def testSimpleCase(self):
    self.make_requests.side_effect = [[self.messages.InterconnectDiagnostics()]]
    self.Run("""
        compute interconnects get-diagnostics my-interconnect1
        """)
    self.CheckRequests(
        [(self.compute_alpha.interconnects, 'GetDiagnostics',
          self.messages.ComputeInterconnectsGetDiagnosticsRequest(
              project='my-project', interconnect='my-interconnect1'))],)

  def testWithUrl(self):
    self.make_requests.side_effect = [[self.messages.InterconnectDiagnostics()]]
    self.Run(
        'compute interconnects get-diagnostics https://www.googleapis.com/'
        'compute/alpha/projects/my-project/global/interconnects/'
        'my-interconnect1')
    self.CheckRequests(
        [(self.compute_alpha.interconnects, 'GetDiagnostics',
          self.messages.ComputeInterconnectsGetDiagnosticsRequest(
              project='my-project', interconnect='my-interconnect1'))],)


if __name__ == '__main__':
  test_case.main()

