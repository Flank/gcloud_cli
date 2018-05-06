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
"""Tests for the sole-tenancy node-templates describe subcommand."""
import textwrap

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class NodeTemplatesDescribeTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.NODE_TEMPLATES[1]],
    ])
    result = self.Run('compute sole-tenancy node-templates describe '
                      'template-1 --region region-1')

    self.CheckRequests(
        [(self.compute_alpha.nodeTemplates,
          'Get',
          self.messages.ComputeNodeTemplatesGetRequest(
              nodeTemplate='template-1',
              project='my-project',
              region='region-1'))],
    )
    self.assertEqual(test_resources.NODE_TEMPLATES[1], result)
    self.assertMultiLineEqual(
        self.stdout.getvalue(),
        textwrap.dedent("""\
            creationTimestamp: '2018-01-15T10:00:00.0Z'
            description: a cold template
            kind: compute#nodeTemplate
            name: template-2
            nodeAffinityLabels:
              environment: prod
              nodeGrouping: backend
            nodeType: n1-node-96-624
            region: https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1
            selfLink: https://www.googleapis.com/compute/alpha/projects/my-project/regions/region-1/nodeTemplates/template-2
            status: CREATING
            statusMessage: Template is being created.
            """))


if __name__ == '__main__':
  test_case.main()
