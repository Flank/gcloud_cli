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
"""Tests for the sole-tenancy node-types describe subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class NodeTypesDescribeTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.SelectApi(self.track.prefix)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.NODE_TYPES[0]],
    ])
    self.Run('compute sole-tenancy node-types describe iAPX-286 '
             '--zone zone-1')

    self.CheckRequests(
        [(self.compute_beta.nodeTypes, 'Get',
          self.messages.ComputeNodeTypesGetRequest(
              nodeType='iAPX-286', project='my-project', zone='zone-1'))],)
    self.AssertOutputEquals(
        """\
    cpuPlatform: '80286'
    creationTimestamp: '1982-02-01T10:00:00.0Z'
    deprecated:
      state: OBSOLETE
    description: oldie but goodie
    guestCpus: 1
    id: '159265359'
    kind: compute#nodeType
    localSsdGb: 0
    memoryMb: 256
    name: iAPX-286
    selfLink: https://www.googleapis.com/compute/beta/projects/my-project/zones/zone-1/nodeTypes/iAPX-286
    zone: zone-1
    """,
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
