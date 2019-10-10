# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import test_case
from tests.lib.surface.kms import base


class KeyringsGetSetIamTestGA(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.kr_name = self.project_name.KeyRing('global/my_kr')

  def testGet(self):
    self.kms.projects_locations_keyRings.GetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsGetIamPolicyRequest(
            options_requestedPolicyVersion=
            iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION,
            resource=self.kr_name.RelativeName()),
        self.messages.Policy(etag=b'foo'))

    self.Run('kms keyrings get-iam-policy --location={0} {1}'.format(
        self.kr_name.location_id, self.kr_name.key_ring_id))
    self.AssertOutputContains('etag: Zm9v')  # "foo" in b64

  def testListCommandFilter(self):
    self.kms.projects_locations_keyRings.GetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsGetIamPolicyRequest(
            options_requestedPolicyVersion=
            iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION,
            resource=self.kr_name.RelativeName()),
        self.messages.Policy(etag=b'foo'))

    self.Run("""
        kms keyrings get-iam-policy
        --location={0} {1}
        --filter=etag:Zm9v
        --format=table[no-heading](etag:sort=1)
        """.format(self.kr_name.location_id, self.kr_name.key_ring_id))

    self.AssertOutputEquals('Zm9v\n')

  def testSetBindings(self):
    policy = self.messages.Policy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ],
        version=3)
    policy_filename = self.Touch(
        self.temp_path,
        contents="""
{
  "etag": "Zm9v",
  "bindings": [ { "members": ["people"], "role": "roles/owner" } ],
}
""")

    self.kms.projects_locations_keyRings.SetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsSetIamPolicyRequest(
            resource=self.kr_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy, updateMask='bindings,etag,version')), policy)

    self.Run('kms keyrings set-iam-policy '
             '--location={0} {1} {2}'.format(self.kr_name.location_id,
                                             self.kr_name.key_ring_id,
                                             policy_filename))
    self.AssertOutputContains("""bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
version: 3
""")
    self.AssertErrContains('Updated IAM policy for keyring [my_kr].')

  def testSetBindingsAndAuditConfig(self):
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
        ],
        version=3)
    policy_filename = self.Touch(
        self.temp_path,
        contents="""
{
  "etag": "Zm9v",
  "auditConfigs": [ { "auditLogConfigs": [ { "logType": "DATA_READ" } ] } ],
  "bindings": [ { "members": ["people"], "role": "roles/owner" } ],
}
""")

    self.kms.projects_locations_keyRings.SetIamPolicy.Expect(
        self.messages.CloudkmsProjectsLocationsKeyRingsSetIamPolicyRequest(
            resource=self.kr_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy,
                updateMask='auditConfigs,bindings,etag,version')), policy)

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
version: 3
""")
    self.AssertErrContains('Updated IAM policy for keyring [my_kr].')


class KeyringsGetSetIamTestBeta(KeyringsGetSetIamTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class KeyringsGetSetIamTestAlpha(KeyringsGetSetIamTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
