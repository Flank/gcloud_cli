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

from googlecloudsdk.core.credentials import store
from tests.lib import cli_test_base
from tests.lib import test_case


class DescribeTest(cli_test_base.CliTestBase):

  def SetUp(self):
    def _Refresh(cred):
      cred.access_token = 'test-access-token-25'
    self.StartObjectPatch(store, 'Refresh', side_effect=_Refresh)

  def _GetTestDataPathFor(self, filename):
    return self.Resource(
        'tests', 'unit', 'surface', 'auth', 'test_data', filename)

  def Account(self):
    return 'inactive@developer.gserviceaccount.com'

  def testPrint(self):
    json_key_file = self._GetTestDataPathFor('inactive_service_account.json')
    self.Run(
        'auth activate-service-account {0} --key-file={1}'
        .format(self.Account(), json_key_file))

    credentials = self.Run('auth describe {0} --format=disable'
                           .format(self.Account()))
    self.assertEquals('999999999999999999999', credentials['client_id'])
    self.assertEquals('test-access-token-25', credentials['access_token'])


if __name__ == '__main__':
  test_case.main()
