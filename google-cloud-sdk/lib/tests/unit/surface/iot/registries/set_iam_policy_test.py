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

"""Tests that ensure setting an IAM policy works properly."""

from __future__ import absolute_import
from __future__ import unicode_literals

import base64
import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.cloudiot import base


_ETAG_CONFIRM_PROMPT = textwrap.dedent("""\
    The specified policy does not contain an "etag" field identifying a specific version to replace. Changing a policy without an "etag" can overwrite concurrent policy changes.

    Replace existing policy (Y/n)? """)


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class SetIamPolicy(base.CloudIotBase):

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)

  def _CreatePolicyAndFile(self, include_etag=False):
    etag_bin = b'abcde'
    if include_etag:
      etag_field = ''',
              "etag": "{}"'''.format(
                  base64.urlsafe_b64encode(etag_bin).decode())
    else:
      etag_field = ''
    policy = self.messages.Policy(
        version=1,
        bindings=[
            self.messages.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.messages.Binding(role='roles/viewer', members=['allUsers'])
        ],
        etag=(etag_bin if include_etag else None))
    f = self.Touch(self.temp_path, 'policy.yaml', contents='''\
        {{
          "version": 1,
          "bindings": [
            {{
              "role": "roles/owner",
              "members": ["user:test-user@gmail.com"]
            }},
            {{
              "role": "roles/viewer",
              "members": ["allUsers"]
            }}
          ]{}
        }}'''.format(etag_field))
    return policy, f

  def testSetIamPolicy(self, track):
    self.track = track
    policy, in_file = self._CreatePolicyAndFile()

    self.client.projects_locations_registries.SetIamPolicy.Expect(
        request=
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry'),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    result = self.Run('iot registries set-iam-policy my-registry --region '
                      'us-central1 {0}'.format(in_file))

    self.assertEqual(result, policy)
    self.AssertLogContains('Updated IAM policy for registry [my-registry].')

  def testSetIamPolicyYaml(self, track):
    self.track = track
    policy = self.messages.Policy(
        version=1,
        bindings=[
            self.messages.Binding(
                role='roles/owner', members=['user:test-user@gmail.com']),
            self.messages.Binding(role='roles/viewer', members=['allUsers'])
        ],
        etag=None)
    in_file = self.Touch(self.temp_path, 'in.yaml', contents=(
        'version: 1\n'
        'bindings:\n'
        '- members:\n'
        '  - user:test-user@gmail.com\n'
        '  role: roles/owner\n'
        '- members:\n'
        '  - allUsers\n'
        '  role: roles/viewer'))

    self.client.projects_locations_registries.SetIamPolicy.Expect(
        request=
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry'),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    result = self.Run('iot registries set-iam-policy my-registry --region '
                      'us-central1 {0}'.format(in_file))

    self.assertEqual(result, policy)

  def testMissingInputFile(self, track):
    self.track = track
    with self.assertRaises(exceptions.Error):
      self.Run('iot registries set-iam-policy my-registry --region us-central1 '
               '/file-does-not-exist')

  def testPromptNoEtagYesSucceeds(self, track):
    self.track = track
    policy, in_file = self._CreatePolicyAndFile()

    self.client.projects_locations_registries.SetIamPolicy.Expect(
        request=
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry'),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    self.WriteInput('y\n')
    self.Run('iot registries set-iam-policy my-registry --region us-central1 '
             '{0}'.format(in_file))
    self.AssertErrContains(_ETAG_CONFIRM_PROMPT)

  def testPromptNoEtagNoFails(self, track):
    self.track = track
    _, in_file = self._CreatePolicyAndFile()
    self.WriteInput('n\n')
    with self.assertRaises(console_io.OperationCancelledError):
      self.Run('iot registries set-iam-policy my-registry --region us-central1 '
               '{0}'.format(in_file))
    self.AssertErrContains(_ETAG_CONFIRM_PROMPT)

  def testNoPromptWithEtag(self, track):
    self.track = track
    policy, in_file = self._CreatePolicyAndFile(include_etag=True)

    self.client.projects_locations_registries.SetIamPolicy.Expect(
        request=
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource='projects/{}/locations/us-central1/registries/{}'.format(
                self.Project(), 'my-registry'),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)),
        response=policy)
    self.Run('iot registries set-iam-policy my-registry --region us-central1 '
             '{0}'.format(in_file))
    self.AssertErrNotContains(_ETAG_CONFIRM_PROMPT)

  def testSetIamPolicy_RelativeName(self, track):
    self.track = track
    policy, in_file = self._CreatePolicyAndFile()

    registry_name = 'projects/{}/locations/us-central1/registries/{}'.format(
        self.Project(), 'my-registry')
    self.client.projects_locations_registries.SetIamPolicy.Expect(
        request=
        self.messages.CloudiotProjectsLocationsRegistriesSetIamPolicyRequest(
            resource=registry_name,
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy)),
        response=policy)

    self.Run('iot registries set-iam-policy {0} {1}'
             .format(registry_name, in_file))


if __name__ == '__main__':
  test_case.main()
