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
"""Tests for the project-info describe subcommand."""
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class ProjectInfoDescribeTest(test_base.BaseTest, test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.PROJECTS[0]],
    ])

    self.Run("""
        compute project-info describe
        """)

    self.CheckRequests(
        [(self.compute_v1.projects,
          'Get',
          messages.ComputeProjectsGetRequest(
              project='my-project'))])
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            commonInstanceMetadata:
              items:
              - key: a
                value: b
              - key: c
                value: d
            creationTimestamp: '2013-09-06T17:54:10.636-07:00'
            name: my-project
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/
            """))


if __name__ == '__main__':
  test_case.main()
