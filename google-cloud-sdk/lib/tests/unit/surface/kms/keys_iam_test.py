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
"""Tests that exercise IAM-related 'gcloud kms keys *' commands."""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.kms import base


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CryptokeysGetIamTest(base.KmsMockTest):

  def SetUp(self):
    self.key_name = self.project_name.Descendant('global/my_kr/my_key')

  def testGet(self, track):
    self.track = track
    self.kms.projects_locations_keyRings_cryptoKeys.GetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
            resource=self.key_name.RelativeName()),
        self.messages.Policy(etag=b'foo'))

    self.Run('kms keys get-iam-policy '
             '--location={0} --keyring={1} {2}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))
    self.AssertOutputContains('etag: Zm9v')  # "foo" in b64

  def testListCommandFilter(self, track):
    self.track = track
    self.kms.projects_locations_keyRings_cryptoKeys.GetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
            resource=self.key_name.RelativeName()),
        self.messages.Policy(etag=b'foo'))

    self.Run("""
        kms keys get-iam-policy
        --location={0} --keyring={1} {2}
        --filter=etag:Zm9v
        --format=table[no-heading](etag:sort=1)
        """.format(self.key_name.location_id, self.key_name.key_ring_id,
                   self.key_name.crypto_key_id))

    self.AssertOutputEquals('Zm9v\n')


@parameterized.parameters(calliope_base.ReleaseTrack.ALPHA,
                          calliope_base.ReleaseTrack.BETA,
                          calliope_base.ReleaseTrack.GA)
class CryptokeysIamTest(base.KmsMockTest):

  def SetUp(self):
    self.key_name = self.project_name.Descendant('global/my_kr/my_key')

  def testSetBindings(self, track):
    self.track = track
    policy = self.messages.Policy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    policy_filename = self.Touch(
        self.temp_path,
        contents="""
{
  "etag": "Zm9v",
  "bindings": [ { "members": ["people"], "role": "roles/owner" } ]
}
""")

    self.kms.projects_locations_keyRings_cryptoKeys.SetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysSetIamPolicyRequest(
            resource=self.key_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy, updateMask='bindings,etag')), policy)

    self.Run('kms keys set-iam-policy '
             '--location={0} --keyring={1} {2} {3}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, policy_filename))
    self.AssertOutputContains("""bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
""")
    self.AssertErrContains('Updated IAM policy for key [my_key].')

  def testSetBindingsAndAuditConfig(self, track):
    self.track = track
    policy = self.messages.Policy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ],
        auditConfigs=[
            self.messages.AuditConfig(auditLogConfigs=[
                self.messages.AuditLogConfig(
                    logType=self.messages.AuditLogConfig.LogTypeValueValuesEnum.
                    DATA_READ),
            ])
        ])
    policy_filename = self.Touch(
        self.temp_path,
        contents="""
{
  "etag": "Zm9v",
  "auditConfigs": [ { "auditLogConfigs": [ { "logType": "DATA_READ" } ] } ],
  "bindings": [ { "members": ["people"], "role": "roles/owner" } ]
}
""")

    self.kms.projects_locations_keyRings_cryptoKeys.SetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysSetIamPolicyRequest(
            resource=self.key_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy,
                # NB: auditConfigs is present here, but not in testSetBindings,
                # since its policy JSON does not have an auditConfigs key.
                updateMask='auditConfigs,bindings,etag')),
        policy)

    self.Run('kms keys set-iam-policy '
             '--location={0} --keyring={1} {2} {3}'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id, policy_filename))
    self.AssertOutputContains("""auditConfigs:
- auditLogConfigs:
  - logType: DATA_READ
bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
""")
    self.AssertErrContains('Updated IAM policy for key [my_key].')

  def testAddBinding(self, track):
    self.track = track
    self.kms.projects_locations_keyRings_cryptoKeys.GetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
            resource=self.key_name.RelativeName()),
        self.messages.Policy(etag=b'foo'))

    policy = self.messages.Policy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    self.kms.projects_locations_keyRings_cryptoKeys.SetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysSetIamPolicyRequest(
            resource=self.key_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy, updateMask='bindings,etag')), policy)
    self.Run('kms keys add-iam-policy-binding '
             '--location={0} --keyring={1} {2} '
             '--member people --role roles/owner'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))
    self.AssertOutputContains("""bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
""")

  def testRemoveBinding(self, track):
    self.track = track
    policy_before = self.messages.Policy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    policy_after = self.messages.Policy(etag=b'foo', bindings=[])

    self.kms.projects_locations_keyRings_cryptoKeys.GetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysGetIamPolicyRequest(
            resource=self.key_name.RelativeName()),
        policy_before)

    self.kms.projects_locations_keyRings_cryptoKeys.SetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsCryptoKeysSetIamPolicyRequest(
            resource=self.key_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy_after, updateMask='bindings,etag')), policy_after)
    self.Run('kms keys remove-iam-policy-binding '
             '--location={0} --keyring={1} {2} '
             '--member people --role roles/owner'.format(
                 self.key_name.location_id, self.key_name.key_ring_id,
                 self.key_name.crypto_key_id))
    self.AssertOutputContains('etag: Zm9v')


if __name__ == '__main__':
  test_case.main()
