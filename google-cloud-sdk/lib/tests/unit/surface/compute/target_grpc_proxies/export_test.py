# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the target-grpc-proxies export subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.load_balancing import test_resources


class TargetGrpcProxiesExportAlphaTest(test_base.BaseTest):

  def PreSetUp(self):
    self._api = 'alpha'

  def SetUp(self):
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_alpha.targetGrpcProxies
    self._resource_name = 'target-grpc-proxy-1'
    self._existing_target_grpc_proxy = test_resources.TARGET_GRPC_PROXIES_ALPHA[
        0]

  def RunExport(self, command):
    self.Run('alpha compute target-grpc-proxies export ' + command)

  def testExportToFile(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_GRPC_PROXIES_ALPHA[0]],
    ])

    file_name = os.path.join(self.temp_path, 'export.yaml')
    self.RunExport('{0} --destination {1}'.format(self._resource_name,
                                                  file_name))

    data = console_io.ReadFromFileOrStdin(file_name or '-', binary=False)
    exported_target_grpc_proxy = export_util.Import(
        message_type=self.messages.TargetGrpcProxy, stream=data)
    self.assertEqual(self._existing_target_grpc_proxy,
                     exported_target_grpc_proxy)

  def testExportToStdOut(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_GRPC_PROXIES_ALPHA[0]],
    ])
    self.RunExport(self._resource_name)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: My first proxy
            name: target-grpc-proxy-1
            selfLink: https://compute.googleapis.com/compute/alpha/projects/my-project/global/targetGrpcProxies/target-grpc-proxy-1
            urlMap: https://compute.googleapis.com/compute/alpha/projects/my-project/global/urlMaps/url-map-1
            validateForProxyless: false
            """))


if __name__ == '__main__':
  test_case.main()
