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
"""Tests for the sole-tenancy node-templates delete subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class NodeTemplatesDeleteTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([[self.messages.Operation()]])
    self.WriteInput('y\n')
    self.Run('compute sole-tenancy node-templates delete template-1 '
             '--region region-1')

    self.CheckRequests([(self.compute_beta.nodeTemplates, 'Delete',
                         self.messages.ComputeNodeTemplatesDeleteRequest(
                             nodeTemplate='template-1',
                             project='my-project',
                             region='region-1'))])


if __name__ == '__main__':
  test_case.main()
