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
"""Tests for the target-grpc-proxies create subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class TargetGrpcProxiesCreateV1Test(test_base.BaseTest):

  def SetUp(self):
    self._api = 'v1'
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_v1.targetGrpcProxies

  def RunCreate(self, command):
    self.Run('compute target-grpc-proxies create %s' % command)

  def testSimpleCase(self):
    self.make_requests.side_effect = [[
        self.messages.TargetGrpcProxy(
            name='my-proxy',
            validateForProxyless=False,
            urlMap=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/global/urlMaps/my-map'.format(self.api)))
    ]]
    self.RunCreate("""
        my-proxy
          --description "My target gRPC proxy"
          --url-map my-map
        """)
    self.CheckRequests([
        (self._target_grpc_proxies_api, 'Insert',
         self.messages.ComputeTargetGrpcProxiesInsertRequest(
             project='my-project',
             targetGrpcProxy=self.messages.TargetGrpcProxy(
                 description='My target gRPC proxy',
                 name='my-proxy',
                 validateForProxyless=False,
                 urlMap=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/global/urlMaps/my-map'.format(self.api)))))
    ],)
    self.AssertOutputEquals(
        """\
      NAME      URL_MAP  VALIDATE_FOR_PROXYLESS
      my-proxy  my-map   False
      """,
        normalize_space=True)

  def testValidateForProxyless(self):
    self.make_requests.side_effect = [[
        self.messages.TargetGrpcProxy(
            name='my-proxy',
            validateForProxyless=True,
            urlMap=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/global/urlMaps/my-map'.format(self.api)))
    ]]
    self.RunCreate("""
        my-proxy
          --description "My target gRPC proxy"
          --url-map my-map
          --validate-for-proxyless
        """)
    self.CheckRequests([
        (self._target_grpc_proxies_api, 'Insert',
         self.messages.ComputeTargetGrpcProxiesInsertRequest(
             project='my-project',
             targetGrpcProxy=self.messages.TargetGrpcProxy(
                 description='My target gRPC proxy',
                 name='my-proxy',
                 validateForProxyless=True,
                 urlMap=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/global/urlMaps/my-map'.format(self.api)))))
    ],)
    self.AssertOutputEquals(
        """\
      NAME      URL_MAP  VALIDATE_FOR_PROXYLESS
      my-proxy  my-map   True
      """,
        normalize_space=True)

  def testUriSupport(self):
    self.RunCreate("""
          https://compute.googleapis.com/compute/{0}/projects/my-project/global/targetGrpcProxies/my-proxy
          --url-map https://compute.googleapis.com/compute/{0}/projects/my-project/global/urlMaps/my-map
        """.format(self.api))
    self.CheckRequests([
        (self._target_grpc_proxies_api, 'Insert',
         self.messages.ComputeTargetGrpcProxiesInsertRequest(
             project='my-project',
             targetGrpcProxy=self.messages.TargetGrpcProxy(
                 name='my-proxy',
                 validateForProxyless=False,
                 urlMap=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/global/urlMaps/my-map'.format(self.api)))))
    ],)

  def testWithoutUrlMap(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --url-map: Must be specified.'):
      self.RunCreate('my-proxy')
    self.CheckRequests()

  def testDefaultScope(self):
    self.make_requests.side_effect = [[
        self.messages.TargetGrpcProxy(
            name='my-proxy',
            validateForProxyless=False,
            urlMap=('https://compute.googleapis.com/compute/{0}/projects/'
                    'my-project/global/urlMaps/my-map'.format(self.api)))
    ]]

    # self.RunCreate('my-proxy'
    #          '--description "My target gRPC proxy with default scope" '
    #          '--url-map my-map')
    self.RunCreate("""
        my-proxy
          --description "My target gRPC proxy with default scope"
          --url-map my-map
        """)
    # self.Run('{0} compute target-grpc-proxies create my-proxy '
    #          '--description "My target gRPC proxy with default scope" '
    #          '--url-map my-map'.format(self._api))
    self.CheckRequests([
        (self._target_grpc_proxies_api, 'Insert',
         self.messages.ComputeTargetGrpcProxiesInsertRequest(
             project='my-project',
             targetGrpcProxy=self.messages.TargetGrpcProxy(
                 description='My target gRPC proxy with default scope',
                 name='my-proxy',
                 validateForProxyless=False,
                 urlMap=('https://compute.googleapis.com/compute/{0}/projects/'
                         'my-project/global/urlMaps/my-map'.format(self.api)))))
    ],)
    self.AssertOutputEquals(
        """\
      NAME      URL_MAP  VALIDATE_FOR_PROXYLESS
      my-proxy  my-map   False
      """,
        normalize_space=True)


class TargetGrpcProxiesCreateBetaTest(TargetGrpcProxiesCreateV1Test):

  def SetUp(self):
    self._api = 'beta'
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_beta.targetGrpcProxies

  def RunCreate(self, command):
    self.Run('beta compute target-grpc-proxies create %s' % command)


class TargetGrpcProxiesCreateAlphaTest(TargetGrpcProxiesCreateBetaTest):

  def SetUp(self):
    self._api = 'alpha'
    self.SelectApi(self._api)
    self._target_grpc_proxies_api = self.compute_alpha.targetGrpcProxies

  def RunCreate(self, command):
    self.Run('alpha compute target-grpc-proxies create %s' % command)


if __name__ == '__main__':
  test_case.main()
