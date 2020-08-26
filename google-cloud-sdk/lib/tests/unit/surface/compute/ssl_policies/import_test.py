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
"""Tests for the ssl policy import subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.apitools import http_error
from tests.lib.surface.compute import ssl_policies_test_base
from tests.lib.surface.compute.ssl_policies import test_resources


class SslPoliciesImportTestAlpha(ssl_policies_test_base.SslPoliciesTestBase):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
    self._existing_ssl_policy = test_resources.SSL_POLICIES_ALPHA[0]
    self._resource_name = 'ssl-policy-1'
    self._new_resource_name = 'ssl-policy-2'

  def SetUp(self):
    self._SetUp(self.track)

  def RunImport(self, command):
    return self.Run('compute ssl-policies import ' + command)

  def testImportFromFile(self):
    ssl_policy_ref = self.GetSslPolicyRef(self._resource_name)
    ssl_policy = copy.deepcopy(self._existing_ssl_policy)
    ssl_policy.description = 'changed'

    # Write the modified ssl_policies to a file.
    file_name = os.path.join(self.temp_path, 'temp-sp.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=ssl_policy, stream=stream)

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)
    self.ExpectGetRequest(ssl_policy_ref, self._existing_ssl_policy)
    self.ExpectPatchRequest(ssl_policy_ref, ssl_policy, response=operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, ssl_policy)

    self.WriteInput('y\n')
    response = self.RunImport('{0} --source {1}'.format(self._resource_name,
                                                        file_name))
    self.assertEqual(response, ssl_policy)

  def testImportFromStd(self):
    ssl_policy_ref = self.GetSslPolicyRef(self._new_resource_name)
    ssl_policy = copy.deepcopy(self._existing_ssl_policy)

    self.WriteInput(export_util.Export(ssl_policy))

    operation_ref = self.GetOperationRef('operation-1')
    operation = self.MakeOperationMessage(
        operation_ref, resource_ref=ssl_policy_ref)
    self.ExpectGetRequest(
        ssl_policy_ref, exception=http_error.MakeHttpError(code=404))
    self.ExpectInsertRequest(ssl_policy_ref, ssl_policy, operation)
    self.ExpectOperationPollingRequest(operation_ref, operation)
    self.ExpectGetRequest(ssl_policy_ref, ssl_policy)

    self.RunImport(self._new_resource_name)

  def testImportInvalidSchema(self):
    # This test ensures that the schema files do not contain invalid fields.
    ssl_policy = copy.deepcopy(self._existing_ssl_policy)

    # id and fingerprint fields should be removed from schema files manually.
    ssl_policy.id = 12345

    # Write the modified ssl_policy to a file.
    file_name = os.path.join(self.temp_path, 'temp-sp.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=ssl_policy, stream=stream)

    with self.AssertRaisesExceptionMatches(
        exceptions.Error, 'Additional properties are not allowed '
        "('id' was unexpected)"):
      self.RunImport('{0} --source {1}'.format(self._resource_name, file_name))


if __name__ == '__main__':
  test_case.main()
