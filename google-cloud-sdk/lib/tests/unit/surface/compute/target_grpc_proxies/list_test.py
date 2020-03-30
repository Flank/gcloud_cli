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
"""Tests for the target-grpc-proxies list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

import mock


class TargetGrpcProxiesListAlphaTest(test_base.BaseTest,
                                     completer_test_base.CompleterBase):

  URI_PREFIX = 'https://compute.googleapis.com/compute/alpha/projects/my-project/'

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi('alpha')
    self._compute_api = self.compute_alpha

    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testSimpleCase(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(
            test_resources.TARGET_GRPC_PROXIES_ALPHA)
    ]
    self.Run(self._api + ' compute target-grpc-proxies list')
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME                URL_MAP VALIDATE_FOR_PROXYLESS
            target-grpc-proxy-1 url-map-1 False
            target-grpc-proxy-2 url-map-2 True
            target-grpc-proxy-3 url-map-3
            """),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
