# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests that exercise IAM-related 'gcloud kms import-jobs *' commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.iam import iam_util
from tests.lib import test_case
from tests.lib.surface.kms import base


class ImportJobsGetIamTestGA(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def SetUp(self):
    self.import_job_name = self.project_name.ImportJob(
        'global/my_kr/my_import_job')

  def testGet(self):
    self.kms.projects_locations_keyRings_importJobs.GetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsImportJobsGetIamPolicyRequest(
            resource=self.import_job_name.RelativeName(),
            options_requestedPolicyVersion=
            iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION),
        self.messages.Policy(
            etag=b'foo',
            version=iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION))

    self.Run('kms import-jobs get-iam-policy '
             '--location={0} --keyring={1} {2}'.format(
                 self.import_job_name.location_id,
                 self.import_job_name.key_ring_id,
                 self.import_job_name.import_job_id))
    self.AssertOutputContains('etag: Zm9v')  # "foo" in b64

  def testListCommandFilter(self):
    self.kms.projects_locations_keyRings_importJobs.GetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsImportJobsGetIamPolicyRequest(
            resource=self.import_job_name.RelativeName(),
            options_requestedPolicyVersion=
            iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION),
        self.messages.Policy(
            etag=b'foo',
            version=iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION))

    self.Run("""
        kms import-jobs get-iam-policy
        --location={0} --keyring={1} {2}
        --filter=etag:Zm9v
        --format=table[no-heading](etag:sort=1)
        """.format(self.import_job_name.location_id,
                   self.import_job_name.key_ring_id,
                   self.import_job_name.import_job_id))

    self.AssertOutputEquals('Zm9v\n')


class ImportjobsSetIamTestALPHA(base.KmsMockTest):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.import_job_name = self.project_name.ImportJob(
        'global/my_kr/my_import_job')

  def testSetBindings(self):
    policy = self.messages.Policy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ],
        version=iam_util.MAX_LIBRARY_IAM_SUPPORTED_VERSION)
    policy_filename = self.Touch(
        self.temp_path,
        contents="""
{
  "etag": "Zm9v",
  "bindings": [ { "members": ["people"], "role": "roles/owner" } ]
}
""")

    self.kms.projects_locations_keyRings_importJobs.SetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsImportJobsSetIamPolicyRequest(
            resource=self.import_job_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy, updateMask='bindings,etag,version')), policy)

    self.Run('kms import-jobs set-iam-policy '
             '--location={0} --keyring={1} {2} {3}'.format(
                 self.import_job_name.location_id,
                 self.import_job_name.key_ring_id,
                 self.import_job_name.import_job_id, policy_filename))
    self.AssertOutputContains("""bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
""")
    self.AssertErrContains('Updated IAM policy for import job [my_import_job].')

  def testSetBindingsAndAuditConfig(self):
    policy = self.messages.Policy(
        etag=b'foo',
        bindings=[
            self.messages.Binding(members=['people'], role='roles/owner')
        ],
        version=3,
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

    self.kms.projects_locations_keyRings_importJobs.SetIamPolicy.Expect(
        self.messages.
        CloudkmsProjectsLocationsKeyRingsImportJobsSetIamPolicyRequest(
            resource=self.import_job_name.RelativeName(),
            setIamPolicyRequest=self.messages.SetIamPolicyRequest(
                policy=policy,
                # NB: auditConfigs is present here, but not in testSetBindings,
                # since its policy JSON does not have an auditConfigs key.
                updateMask='auditConfigs,bindings,etag,version')),
        policy)

    self.Run('kms import-jobs set-iam-policy '
             '--location={0} --keyring={1} {2} {3}'.format(
                 self.import_job_name.location_id,
                 self.import_job_name.key_ring_id,
                 self.import_job_name.import_job_id, policy_filename))
    self.AssertOutputContains("""auditConfigs:
- auditLogConfigs:
  - logType: DATA_READ
bindings:
- members:
  - people
  role: roles/owner
etag: Zm9v
""")
    self.AssertErrContains('Updated IAM policy for import job [my_import_job].')


class ImportJobsGetIamTestBeta(ImportJobsGetIamTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA


class ImportJobsGetIamTestAlpha(ImportJobsGetIamTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA


if __name__ == '__main__':
  test_case.main()
