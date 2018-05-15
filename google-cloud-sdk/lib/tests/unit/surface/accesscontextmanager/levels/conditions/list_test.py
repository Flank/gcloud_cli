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
"""Tests for `gcloud access-context-manager levels conditions list`."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface import accesscontextmanager


@parameterized.parameters((base.ReleaseTrack.ALPHA,))
class LevelConditionsListTest(accesscontextmanager.Base):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(True)

  def _ExpectGet(self, level, policy):
    level_name = 'accessPolicies/{}/accessLevels/{}'.format(policy, level.name)
    m = self.messages
    request_type = m.AccesscontextmanagerAccessPoliciesAccessLevelsGetRequest
    level_format = request_type.AccessLevelFormatValueValuesEnum.AS_DEFINED
    self.client.accessPolicies_accessLevels.Get.Expect(
        request_type(
            name=level_name,
            accessLevelFormat=level_format
        ),
        level)

  def testList_MissingRequired(self, track):
    self.SetUpForTrack(track)
    with self.AssertRaisesExceptionMatches(cli_test_base.MockArgumentError,
                                           'must be specified'):
      self.Run('access-context-manager levels conditions list '
               '    --policy my_policy')

  def _MakeBasicLevel(self, name):
    m = self.messages
    combining_function_enum = m.BasicLevel.CombiningFunctionValueValuesEnum
    combining_function = combining_function_enum.AND
    return self.messages.AccessLevel(
        basic=self.messages.BasicLevel(
            combiningFunction=combining_function,
            conditions=[
                self.messages.Condition(
                    ipSubnetworks=['127.0.0.1/24', '10.0.0.0/8'],
                    members=['user:a@example.com', 'user:b@example.com']),
                self.messages.Condition(
                    requiredAccessLevels=[
                        'accessPolicies/my_policy/accessLevels/other_level',
                        'accessPolicies/my_policy/accessLevels/other_level2'],
                    negate=True)

            ]
        ),
        name=name)

  def testList(self, track):
    self.SetUpForTrack(track)
    level = self._MakeBasicLevel('my_level')
    self._ExpectGet(level, 'my_policy')

    self.Run('access-context-manager levels conditions list '
             '    --level my_level --policy my_policy')

    self.AssertOutputContains("""\
        Conditions are joined with AND operator.

        +------------------------------------------------------------------------+
        |                          ACCESS LEVEL CONDITIONS                       |
        +---------+----------------+--------------------+------------------------+
        | NEGATED | IP_SUBNETWORKS |      MEMBERS       | REQUIRED_ACCESS_LEVELS |
        +---------+----------------+--------------------+------------------------+
        |         | 127.0.0.1/24   | user:a@example.com |                        |
        |         | 10.0.0.0/8     | user:b@example.com |                        |
        +---------+----------------+--------------------+------------------------+
        | True    |                |                    | other_level            |
        |         |                |                    | other_level2           |
        +---------+----------------+--------------------+------------------------+
        """, normalize_space=True)


if __name__ == '__main__':
  test_case.main()
