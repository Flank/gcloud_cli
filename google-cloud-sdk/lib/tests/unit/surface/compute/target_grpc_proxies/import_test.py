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
"""Tests for the target gRPC proxy import subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os

from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.load_balancing import test_resources


def _GetTargetGrpcProxyRef(self, name):
  """Returns the specified target grpc proxy reference."""
  params = {'project': self.Project()}
  collection = 'compute.targetGrpcProxies'
  return self.resources.Parse(name, params=params, collection=collection)


class TargetGrpcProxiesImportTestAlpha(test_base.BaseTest):

  def PreSetUp(self):
    self._api = 'alpha'

  def SetUp(self):
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_alpha.targetGrpcProxies
    self._resource_name = 'target-grpc-proxy-1'
    self._existing_target_grpc_proxy = test_resources.TARGET_GRPC_PROXIES_ALPHA[
        0]

  def RunImport(self, command):
    return self.Run('alpha compute target-grpc-proxies import ' + command)

  def testImportFromFile(self):
    target_grpc_proxy = copy.deepcopy(self._existing_target_grpc_proxy)
    target_grpc_proxy.description = 'changed'
    self.make_requests.side_effect = iter(
        [[test_resources.TARGET_GRPC_PROXIES_ALPHA[0]], [target_grpc_proxy]])

    # Write the modified target_grpc_proxies to a file
    file_name = os.path.join(self.temp_path, 'temp-tgp.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=target_grpc_proxy, stream=stream)
    self.WriteInput('y\n')

    response = self.RunImport('{0} --source {1}'.format(self._resource_name,
                                                        file_name))
    self.CheckRequests(
        [(self._target_grpc_proxies_api, 'Get',
          self.messages.ComputeTargetGrpcProxiesGetRequest(
              project='my-project', targetGrpcProxy='target-grpc-proxy-1'))],
        [(self._target_grpc_proxies_api, 'Patch',
          self.messages.ComputeTargetGrpcProxiesPatchRequest(
              project='my-project',
              targetGrpcProxy=self._resource_name,
              targetGrpcProxyResource=target_grpc_proxy))])
    self.assertEqual(response, target_grpc_proxy)

  def testImportFromStdin(self):
    target_grpc_proxy = copy.deepcopy(self._existing_target_grpc_proxy)
    target_grpc_proxy.description = 'changed'
    self.make_requests.side_effect = iter(
        [[test_resources.TARGET_GRPC_PROXIES_ALPHA[0]], [target_grpc_proxy]])

    # Write the modified target_grpc_proxies to stdin
    self.WriteInput(export_util.Export(target_grpc_proxy))

    response = self.RunImport(self._resource_name)
    self.CheckRequests(
        [(self._target_grpc_proxies_api, 'Get',
          self.messages.ComputeTargetGrpcProxiesGetRequest(
              project='my-project', targetGrpcProxy='target-grpc-proxy-1'))],
        [(self._target_grpc_proxies_api, 'Patch',
          self.messages.ComputeTargetGrpcProxiesPatchRequest(
              project='my-project',
              targetGrpcProxy=self._resource_name,
              targetGrpcProxyResource=target_grpc_proxy))])
    self.assertEqual(response, target_grpc_proxy)

  def testImportInvalidSchema(self):
    target_grpc_proxy = copy.deepcopy(self._existing_target_grpc_proxy)
    target_grpc_proxy.description = 'changed'

    # id and fingerprint fields should be removed from schema files
    target_grpc_proxy.id = 12345

    self.make_requests.side_effect = iter(
        [[test_resources.TARGET_GRPC_PROXIES_ALPHA[0]], [target_grpc_proxy]])

    # Write the modified target_grpc_proxies to a file
    file_name = os.path.join(self.temp_path, 'temp-tgp.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=target_grpc_proxy, stream=stream)
    self.WriteInput('y\n')

    with self.AssertRaisesExceptionMatches(
        exceptions.ToolException, 'Additional properties are not allowed '
        "('id' was unexpected)"):
      self.RunImport('{0} --source {1}'.format(self._resource_name, file_name))


if __name__ == '__main__':
  test_case.main()
