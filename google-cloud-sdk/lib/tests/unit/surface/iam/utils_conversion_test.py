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
"""Tests that the enum manipulation functions behave well."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import test_case
from tests.lib.surface.iam import unit_test_base

msgs = core_apis.GetMessagesModule('iam', 'v1')
CREATE_KEY_TYPES = (
    msgs.CreateServiceAccountKeyRequest.PrivateKeyTypeValueValuesEnum)
KEY_TYPES = (msgs.ServiceAccountKey.PrivateKeyTypeValueValuesEnum)


class ConversionTest(unit_test_base.BaseTest):

  def testRoundTripKeyType(self):
    key_types = [KEY_TYPES.TYPE_PKCS12_FILE,
                 KEY_TYPES.TYPE_GOOGLE_CREDENTIALS_FILE,
                 KEY_TYPES.TYPE_UNSPECIFIED]
    for key_type in key_types:
      round_trip_key_type = iam_util.KeyTypeFromCreateKeyType(
          iam_util.KeyTypeToCreateKeyType(key_type))
      self.assertEqual(key_type, round_trip_key_type)

  def testRoundTripKeyTypeString(self):
    key_types = ['p12', 'json', 'unspecified']
    for key_type in key_types:
      round_trip_key_type = iam_util.KeyTypeToString(iam_util.KeyTypeFromString(
          key_type))
      self.assertEqual(key_type, round_trip_key_type)


if __name__ == '__main__':
  test_case.main()
