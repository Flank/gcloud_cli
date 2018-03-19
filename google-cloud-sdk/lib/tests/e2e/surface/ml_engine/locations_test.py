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
"""e2e tests for ml-engine locations command group."""
from googlecloudsdk.calliope import base
from tests.lib import e2e_base
from tests.lib import test_case


class MlEngineLocationsIntegrationTest(e2e_base.WithServiceAuth):
  """e2e tests for ml-engine locations command group.

  The locations command group is very simple, all commands access readonly APIs.
  """

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA

  def testListCommand(self):
    self.Run('ml-engine locations list')
    self.AssertOutputContains('us-east1')

  def testDescribeCommand(self):
    self.Run('ml-engine locations describe us-east1')
    self.AssertOutputContains('"name": "us-east1"')


if __name__ == '__main__':
  test_case.main()
