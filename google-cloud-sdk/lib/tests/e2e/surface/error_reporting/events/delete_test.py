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

"""Integration tests of the 'delete' subcommand."""

from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.surface.error_reporting import base


class DeleteIntegrationTest(base.ErrorReportingIntegrationTestBase):
  """Test 'events delete' subcommand."""

  def testDeleteEvents(self):
    self.RunCmd('events delete')
    self.AssertErrContains('Really delete all events')
    self.AssertErrContains('deleted')

  def testDeleteEventsNonExistingProject(self):
    bad_project = 'error-reporting-gcloud-e2e-does-not-exist'
    properties.VALUES.core.project.Set(bad_project)
    with self.AssertRaisesHttpExceptionRegexp('not found'):
      self.RunCmd('events delete')


if __name__ == '__main__':
  test_case.main()
