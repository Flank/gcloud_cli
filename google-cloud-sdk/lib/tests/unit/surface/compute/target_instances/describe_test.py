# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the target-instances describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetInstancesDescribeTest(test_base.BaseTest,
                                  test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_INSTANCES[0]],
    ])

    self.Run("""
        compute target-instances describe target-instance-1
          --zone zone-1
        """)

    self.CheckRequests(
        [(self.compute_v1.targetInstances,
          'Get',
          messages.ComputeTargetInstancesGetRequest(
              targetInstance='target-instance-1',
              project='my-project',
              zone='zone-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            instance: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/instances/instance-1
            name: target-instance-1
            natPolicy: NO_NAT
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1/targetInstances/target-instance-1
            zone: https://www.googleapis.com/compute/v1/projects/my-project/zones/zone-1
            """))


if __name__ == '__main__':
  test_case.main()
