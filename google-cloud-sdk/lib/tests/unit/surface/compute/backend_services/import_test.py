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
"""Tests for the backend services import subcommand."""

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
from tests.lib.surface.compute import test_resources
from tests.lib.surface.compute.backend_services import backend_services_test_base


class BackendServiceImportTest(
    backend_services_test_base.BackendServicesTestBase):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.GA
    self._backend_services = test_resources.BACKEND_SERVICES_V1

  def RunImport(self, command):
    self.Run('compute backend-services import ' + command)

  def testImportBackendServiceFromStdIn(self):
    backend_service_ref = self.GetBackendServiceRef('my-backend-service')
    backend_service = copy.deepcopy(self._backend_services[0])

    self.ExpectGetRequest(
        backend_service_ref=backend_service_ref,
        exception=http_error.MakeHttpError(code=404))
    self.ExpectInsertRequest(
        backend_service_ref=backend_service_ref,
        backend_service=backend_service)

    self.WriteInput(export_util.Export(backend_service))

    self.RunImport('my-backend-service --global')

  def testImportBackendServiceFromFile(self):
    backend_service_ref = self.GetBackendServiceRef(
        'my-backend-service', region='alaska')
    backend_service = copy.deepcopy(self._backend_services[0])

    backend_service.description = 'changed'

    # Write the modified backend_service to a file.
    file_name = os.path.join(self.temp_path, 'temp-bs.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=backend_service, stream=stream)

    self.ExpectGetRequest(
        backend_service_ref=backend_service_ref,
        backend_service=self._backend_services[0])
    self.ExpectPatchRequest(
        backend_service_ref=backend_service_ref,
        backend_service=backend_service)

    self.WriteInput('y\n')

    self.RunImport('my-backend-service --region alaska '
                   '--source {0}'.format(file_name))

  def testImportBackendServiceInvalidSchema(self):
    # This test ensures that the schema files do not contain invalid fields.
    backend_service = copy.deepcopy(self._backend_services[0])

    # id and fingerprint fields should be removed from schema files manually.
    backend_service.id = 12345

    # Write the modified backend_service to a file.
    file_name = os.path.join(self.temp_path, 'temp-bs.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=backend_service, stream=stream)

    with self.AssertRaisesExceptionMatches(
        exceptions.Error, "Additional properties are not allowed "
        "('id' was unexpected)"):
      self.RunImport('my-backend-service --region alaska '
                     '--source {0}'.format(file_name))


class BackendServiceImportTestBeta(BackendServiceImportTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA
    self._backend_services = test_resources.BACKEND_SERVICES_BETA


class BackendServiceImportTestAlpha(BackendServiceImportTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
    self._backend_services = test_resources.BACKEND_SERVICES_ALPHA


if __name__ == '__main__':
  test_case.main()
