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
"""compute snapshots set-iam-policy tests."""
import textwrap

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import yaml
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_resources


class SetIamPolicyTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):

  def SetUp(self):
    self.messages = apis.GetMessagesModule('compute', 'alpha')
    self.mock_client = mock.Client(
        apis.GetClientClass('compute', 'alpha'),
        real_client=apis.GetClientInstance('compute', 'alpha', no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)
    self.track = base.ReleaseTrack.ALPHA

  def testSimpleResponseCase(self):
    policy = test_resources.AlphaIamPolicyWithOneBindingAndDifferentEtag()
    self.mock_client.snapshots.SetIamPolicy.Expect(
        self.messages.ComputeSnapshotsSetIamPolicyRequest(
            resource='my-resource',
            project='fake-project',
            globalSetPolicyRequest=self.messages.GlobalSetPolicyRequest(
                policy=policy)),
        response=policy)

    policy_file = self.Touch(
        self.temp_path, 'iam.json', contents=encoding.MessageToJson(policy))

    self.Run(
        'compute snapshots set-iam-policy my-resource {}'.format(policy_file))

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            bindings:
            - members:
              - user:testuser@google.com
              role: owner
            etag: ZXRhZ1R3bw==
            """))

  def testBadlyFormattedPolicyFile(self):
    policy_file = self.Touch(self.temp_path, 'bad.json', contents='bad')

    with self.assertRaises(exceptions.BadFileException):
      self.Run(
          'compute snapshots set-iam-policy my-resource {}'.format(policy_file))

  def testMissingPolicyFile(self):
    with self.assertRaises(yaml.FileLoadError):
      self.Run('compute snapshots set-iam-policy my-resource missing-file')


if __name__ == '__main__':
  test_case.main()
