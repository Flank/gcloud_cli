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
"""Tests for the backend services export subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import test_resources
from tests.lib.surface.compute.backend_services import backend_services_test_base


class BackendServiceExportTest(
    backend_services_test_base.BackendServicesTestBase):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.GA
    self._api = 'v1'
    self._backend_services = test_resources.BACKEND_SERVICES_V1

  def RunExport(self, command):
    self.Run('compute backend-services export ' + command)

  def testExportToStdOut(self):
    backend_service_ref = self.GetBackendServiceRef('my-backend-service')

    backend_service = test_resources.MakeBackendServiceWithOutlierDetection(
        self.messages, self._api)

    self.ExpectGetRequest(
        backend_service_ref=backend_service_ref,
        backend_service=backend_service)

    self.RunExport('my-backend-service --global')

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: my backend service
            healthChecks:
            - https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/httpHealthChecks/my-health-check
            name: backend-service-1
            outlierDetection:
              interval:
                seconds: 1500
            portName: http
            protocol: HTTP
            selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/backendServices/backend-service-1
            timeoutSec: 30
            """ % {'api': self._api}))

  def testExportToFile(self):
    backend_service_ref = self.GetBackendServiceRef(
        'my-backend-service', region='alaska')
    self.ExpectGetRequest(
        backend_service_ref=backend_service_ref,
        backend_service=self._backend_services[1])

    file_name = os.path.join(self.temp_path, 'export.yaml')

    self.RunExport('my-backend-service --region alaska'
                   ' --destination {0}'.format(file_name))

    data = console_io.ReadFromFileOrStdin(file_name or '-', binary=False)
    exported_backend_service = export_util.Import(
        message_type=self.messages.BackendService, stream=data)
    self.AssertMessagesEqual(self._backend_services[1],
                             exported_backend_service)


class BackendServiceExportTestBeta(BackendServiceExportTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.BETA
    self._api = 'beta'
    self._backend_services = test_resources.BACKEND_SERVICES_BETA


class BackendServiceExportTestAlpha(BackendServiceExportTest):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
    self._api = 'alpha'
    self._backend_services = test_resources.BACKEND_SERVICES_ALPHA


if __name__ == '__main__':
  test_case.main()
