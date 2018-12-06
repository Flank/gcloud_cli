# -*- coding: utf-8 -*- #
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
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.resource_manager import liens
from googlecloudsdk.api_lib.util import exceptions as api_exceptions
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.resource_manager import testbase


class LiensDeleteTest(testbase.LiensUnitTestBase):

  def testDeleteLien(self):
    self.mock_liens.Delete.Expect(
        liens.LiensMessages().CloudresourcemanagerLiensDeleteRequest(
            liensId='pt123-abc'),
        liens.LiensMessages().Empty())
    self.RunLiens('delete', 'pt123-abc')
    self.AssertErrContains('Deleted [liens/pt123-abc].')

  def testDeleteMissingId(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument LIEN_ID: Must be specified.'):
      self.RunLiens('delete')

  def testDeleteFails(self):
    self.mock_liens.Delete.Expect(
        liens.LiensMessages().CloudresourcemanagerLiensDeleteRequest(
            liensId='l1234'),
        exception=http_error.MakeDetailedHttpError(
            url='https://cloudresourcemanager.googleapis.com/v1/liens/l1234',
            reason='INTERNAL',
            message=':/',
            details=[{
                '@type':
                    'type.googleapis.com/google.rpc.PreconditionFailure',
                'violations': [{
                    'type': 'LIEN',
                    'subject': 'liens/l1234',
                    'description': 'Useful details about this error.'
                }]
            }]))
    with self.assertRaises(api_exceptions.HttpException):
      self.RunLiens('delete', 'l1234')
    self.AssertErrEquals(
        """ERROR: (gcloud.alpha.resource-manager.liens.delete) INTERNAL: :/
- '@type': type.googleapis.com/google.rpc.PreconditionFailure
  violations:
  - description: Useful details about this error.
    subject: liens/l1234
    type: LIEN
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
