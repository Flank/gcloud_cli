# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Tests that ensure deserialization of server responses work properly."""

from __future__ import absolute_import
from __future__ import unicode_literals

from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base


class SignJwtTest(unit_test_base.BaseTest):

  def testSignJwtServiceAccount(self):
    test_key = '1234'
    self.client.projects_serviceAccounts.SignJwt.Expect(
        request=self.msgs.IamProjectsServiceAccountsSignJwtRequest(
            name=('projects/-/serviceAccounts/'
                  'test@test-project.iam.gserviceaccount.com'),
            signJwtRequest=self.msgs.SignJwtRequest(
                payload='{"jwt" : "to_sign"}')),
        response=self.msgs.SignJwtResponse(
            keyId=test_key, signedJwt=b'signed jwt'))

    in_file = self.Touch(self.temp_path, contents=b'{"jwt" : "to_sign"}')
    out_file = self.Touch(self.temp_path)
    self.Run('beta iam service-accounts sign-jwt '
             '--iam-account test@test-project.iam.gserviceaccount.com '
             '{0} {1}'.format(in_file, out_file))

    self.AssertErrContains(('signed jwt [{0}] as [{1}] for '
                            '[test@test-project.iam.gserviceaccount.com] '
                            'using key [{2}]').format(in_file, out_file,
                                                      test_key))
    self.AssertBinaryFileEquals(b'signed jwt', out_file)

  def testMissingInputFile(self):
    with self.assertRaises(files.Error):
      self.Run('beta iam service-accounts sign-jwt '
               '--iam-account=test@test-project.iam.gserviceaccount.com '
               '/file-does-not-exist /tmp/key')


if __name__ == '__main__':
  test_case.main()
