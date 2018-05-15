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

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.resource_manager import liens
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.resource_manager import testbase


class LiensListTest(testbase.LiensUnitTestBase):

  def testNoFlagsEmptyList(self):
    self.mock_liens.List.Expect(
        liens.LiensMessages().CloudresourcemanagerLiensListRequest(
            parent='projects/t123'),
        liens.LiensMessages().ListLiensResponse())
    self.RunLiens('list', '--project', 't123')
    self.AssertOutputEquals('', normalize_space=True)

  def testListOneLien(self):
    self.mock_liens.List.Expect(
        liens.LiensMessages().CloudresourcemanagerLiensListRequest(
            parent='projects/t123'),
        liens.LiensMessages().ListLiensResponse(liens=[self.test_lien]))
    self.RunLiens('list', '--project', 't123')
    self.AssertOutputContains(
        """\
      NAME        ORIGIN                    REASON
      p1234-abc   unittest.googlecloudsdk   player' gotta play
      """,
        normalize_space=True)

  def testListFails(self):
    self.mock_liens.List.Expect(
        liens.LiensMessages().CloudresourcemanagerLiensListRequest(
            parent='projects/t123'),
        exception=http_error.MakeDetailedHttpError(
            url='https://cloudresourcemanager.googleapis.com/v1/liens',
            reason='INTERNAL',
            message=':/',
            details=[{
                '@type':
                    'type.googleapis.com/google.rpc.PreconditionFailure',
                'violations': [{
                    'type': 'PROJECT',
                    'subject': 'projects/t123',
                    'description': 'Useful details about this error.'
                }]
            }]))
    with self.assertRaises(api_exceptions.HttpException):
      self.RunLiens('list', '--project', 't123')
    self.AssertErrEquals(
        """ERROR: (gcloud.alpha.resource-manager.liens.list) INTERNAL: :/
- '@type': type.googleapis.com/google.rpc.PreconditionFailure
  violations:
  - description: Useful details about this error.
    subject: projects/t123
    type: PROJECT
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
