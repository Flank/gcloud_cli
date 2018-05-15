# Copyright 2014 Google Inc. All Rights Reserved.
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

"""Tests for projects undelete."""

from __future__ import absolute_import
from __future__ import unicode_literals
from tests.lib import test_case
from tests.lib.surface.projects import base
from tests.lib.surface.projects import util


class ProjectsUndeleteTest(base.ProjectsUnitTestBase):

  def testUndeleteValidProject(self):
    test_project_id = util.GetTestActiveProject().projectId
    self.mock_client.projects.Undelete.Expect(
        self.messages.CloudresourcemanagerProjectsUndeleteRequest(
            projectId=test_project_id),
        self.messages.Empty())
    self.RunProjectsBeta('undelete', test_project_id)
    self.AssertOutputEquals('')
    self.AssertErrEquals("""\
Restored project [https://cloudresourcemanager.googleapis.com/v1/projects/feisty-catcher-644].
""")


if __name__ == '__main__':
  test_case.main()
