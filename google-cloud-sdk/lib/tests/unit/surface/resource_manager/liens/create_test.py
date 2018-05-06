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

from googlecloudsdk.api_lib.resource_manager import liens
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from googlecloudsdk.core import properties
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.resource_manager import testbase


class LiensCreateTest(testbase.LiensUnitTestBase):

  def testCreateLien(self):
    self.mock_liens.Create.Expect(liens.LiensMessages().Lien(
        parent='projects/t123',
        origin='unittest.googlecloudsdk',
        reason='player\'s gotta play',
        restrictions=['resourcemanager.projects.delete']), self.test_lien)

    args = [
        '--project', 't123', '--origin', 'unittest.googlecloudsdk', '--reason',
        'player\'s gotta play', '--restrictions',
        'resourcemanager.projects.delete'
    ]
    self.assertEqual(self.RunLiens('create', *args), self.test_lien)

  def testCreateMissingReason(self):
    args = [
        '--project', 't123', '--origin', 'unittest.googlecloudsdk',
        '--restrictions', 'resourcemanager.projects.delete'
    ]
    with self.AssertRaisesArgumentErrorMatches(
        'argument --reason: Must be specified.'):
      self.RunLiens('create', *args)

  def testCreateMissingRestriction(self):
    args = [
        '--project', 't123', '--origin', 'unittest.googlecloudsdk', '--reason',
        'player\'s gotta play'
    ]
    with self.AssertRaisesArgumentErrorMatches(
        'argument --restrictions: Must be specified.'):
      self.RunLiens('create', *args)

  def testCreateMissingOrigin(self):
    args = [
        '--project', 't123', '--reason', 'player\'s gotta play',
        '--restrictions', 'resourcemanager.projects.delete'
    ]
    self.mock_liens.Create.Expect(liens.LiensMessages().Lien(
        parent='projects/t123',
        origin='fake_account',
        reason='player\'s gotta play',
        restrictions=['resourcemanager.projects.delete']), self.test_lien)
    self.assertEqual(self.RunLiens('create', *args), self.test_lien)

  def testCreateMissingProject(self):
    args = [
        '--origin', 'unittest.googlecloudsdk', '--reason',
        'player\'s gotta play', '--restrictions',
        'resourcemanager.projects.delete'
    ]
    regex = (r'The required property \[project\] is not currently set')
    with self.assertRaisesRegex(properties.RequiredPropertyError, regex):
      self.RunLiens('create', *args)

  def testCreateLienFails400(self):
    self.mock_liens.Create.Expect(
        liens.LiensMessages().Lien(
            parent='projects/t123',
            origin='unittest.googlecloudsdk',
            reason='player\'s gotta play',
            restrictions=['resourcemanager.projects.delete']),
        exception=http_error.MakeDetailedHttpError(
            url=u'https://cloudresourcemanager.googleapis.com/v1/liens',
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

    args = [
        '--project', 't123', '--origin', 'unittest.googlecloudsdk', '--reason',
        'player\'s gotta play', '--restrictions',
        'resourcemanager.projects.delete'
    ]
    with self.assertRaises(api_exceptions.HttpException):
      self.RunLiens('create', *args)
    self.AssertErrEquals(
        """ERROR: (gcloud.alpha.resource-manager.liens.create) INTERNAL: :/
- '@type': type.googleapis.com/google.rpc.PreconditionFailure
  violations:
  - description: Useful details about this error.
    subject: projects/t123
    type: PROJECT
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
