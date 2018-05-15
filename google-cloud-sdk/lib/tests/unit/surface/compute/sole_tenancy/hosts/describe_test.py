# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the sole-tenancy hosts describe subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class HostsDescribeTest(test_base.BaseTest):

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.SelectApi(self.track.prefix)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.HOSTS[0]],
    ])
    self.Run("""
        compute sole-tenancy hosts describe my-host --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_alpha.hosts,
          'Get',
          self.messages.ComputeHostsGetRequest(
              host='my-host',
              project='my-project',
              zone='zone-1'))],
    )
    self.AssertOutputEquals("""\
    description: Host 1
    hostType: n1-host-64-208
    instances:
    - https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/instances/instance-1
    - https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/instances/instance-2
    name: host-1
    selfLink: https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1/hosts/host-1
    status: READY
    statusMessage: Host has room.
    zone: https://www.googleapis.com/compute/alpha/projects/my-project/zones/zone-1
    """, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
