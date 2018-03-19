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
"""Tests that exercise IAM-related 'gcloud kms keyrings *' commands."""

from tests.lib import test_case
from tests.lib.surface.kms import base


class KeyringsIamTest(base.KmsMockTest):

  def SetUp(self):
    self.kr_name = self.project_name.Descendant('global/my_kr')

  def testGet(self):
    self.kms.projects_locations_keyRings.GetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsGetIamPolicyRequest(
            resource=self.kr_name.RelativeName()),
        self.messages.Policy(etag='foo'))

    self.Run('kms keyrings get-iam-policy --location={0} {1}'.format(
        self.kr_name.location_id, self.kr_name.key_ring_id))
    self.AssertOutputContains('etag: Zm9v')  # "foo" in b64

  def testListCommandFilter(self):
    self.kms.projects_locations_keyRings.GetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsGetIamPolicyRequest(
            resource=self.kr_name.RelativeName()),
        self.messages.Policy(etag='foo'))

    self.Run("""
        kms keyrings get-iam-policy
        --location={0} {1}
        --filter=etag:Zm9v
        --format=table[no-heading](etag:sort=1)
        """.format(self.kr_name.location_id, self.kr_name.key_ring_id))

    self.AssertOutputEquals('Zm9v\n')

  def testSetBindings(self):
    policy = self.messages.Policy(
        etag='foo',
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

    self.kms.projects_locations_keyRings.SetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsSetIamPolicyRequest(
            resource=self.kr_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy, updateMask='bindings,etag')), policy)

    self.Run('kms keyrings set-iam-policy '
             '--location={0} {1} {2}'.format(self.kr_name.location_id,
                                             self.kr_name.key_ring_id,
                                             policy_filename))
    self.AssertOutputContains("""bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
""")
    self.AssertErrContains('Updated IAM policy for keyring [my_kr].')

  def testSetBindingsAndAuditConfig(self):
    policy = self.messages.Policy(
        etag='foo',
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

    self.kms.projects_locations_keyRings.SetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsSetIamPolicyRequest(
            resource=self.kr_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy, updateMask='auditConfigs,bindings,etag')),
        policy)

    self.Run('kms keyrings set-iam-policy '
             '--location={0} {1} {2}'.format(self.kr_name.location_id,
                                             self.kr_name.key_ring_id,
                                             policy_filename))
    self.AssertOutputContains("""auditConfigs:
- auditLogConfigs:
  - logType: DATA_READ
bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
""")
    self.AssertErrContains('Updated IAM policy for keyring [my_kr].')

  def testAddBinding(self):
    self.kms.projects_locations_keyRings.GetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsGetIamPolicyRequest(
            resource=self.kr_name.RelativeName()),
        self.messages.Policy(etag='foo'))

    policy = self.messages.Policy(
        etag='foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    self.kms.projects_locations_keyRings.SetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsSetIamPolicyRequest(
            resource=self.kr_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy, updateMask='bindings,etag')), policy)
    self.Run('kms keyrings add-iam-policy-binding '
             '--location={0} {1} --member people --role roles/owner'.format(
                 self.kr_name.location_id, self.kr_name.key_ring_id))
    self.AssertOutputContains("""bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
""")

  def testRemoveBinding(self):
    policy_before = self.messages.Policy(
        etag='foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ])
    policy_after = self.messages.Policy(etag='foo', bindings=[])

    self.kms.projects_locations_keyRings.GetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsGetIamPolicyRequest(
            resource=self.kr_name.RelativeName()),
        policy_before)

    self.kms.projects_locations_keyRings.SetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsSetIamPolicyRequest(
            resource=self.kr_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy_after, updateMask='bindings,etag')), policy_after)
    self.Run('kms keyrings remove-iam-policy-binding '
             '--location={0} {1} --member people --role roles/owner'.format(
                 self.kr_name.location_id, self.kr_name.key_ring_id))
    self.AssertOutputContains('etag: Zm9v')


if __name__ == '__main__':
  test_case.main()
