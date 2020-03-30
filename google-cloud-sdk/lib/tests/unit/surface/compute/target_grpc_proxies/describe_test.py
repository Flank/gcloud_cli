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
"""Tests for the target gRPC proxy describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class TargetGrpcProxiesDescribeAlphaTest(test_base.BaseTest):

  URI_PREFIX = 'https://compute.googleapis.com/compute/v1/projects/my-project/'

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_alpha.targetGrpcProxies

  def RunDescribe(self, command):
    self.Run('alpha compute target-grpc-proxies describe %s' % command)

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_GRPC_PROXIES_ALPHA[0]],
    ])
    self.RunDescribe('target-grpc-proxy-1')
    self.CheckRequests(
        [(self._target_grpc_proxies_api, 'Get',
          self.messages.ComputeTargetGrpcProxiesGetRequest(
              project='my-project', targetGrpcProxy='target-grpc-proxy-1'))],)
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
