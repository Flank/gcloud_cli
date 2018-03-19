# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Tests for the target-http-proxies update subcommand."""

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetHTTPProxiesUpdateTest(test_base.BaseTest):

  def testSimpleCase(self):
    self.Run("""
        compute target-http-proxies update target-http-proxy-1
          --url-map my-map
        """)

    self.CheckRequests(
        [(self.compute_v1.targetHttpProxies,
          'SetUrlMap',
          messages.ComputeTargetHttpProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpProxy='target-http-proxy-1',
              urlMapReference=messages.UrlMapReference(
                  urlMap=('https://www.googleapis.com/compute/v1/projects/'
                          'my-project/global/urlMaps/my-map'))))],
    )

  def testUriSupport(self):
    self.Run("""
        compute target-http-proxies update
          https://www.googleapis.com/compute/v1/projects/my-project/global/targetHttpProxies/target-http-proxy-1
          --url-map https://www.googleapis.com/compute/v1/projects/my-project/global/urlMaps/my-map
        """)

    self.CheckRequests(
        [(self.compute_v1.targetHttpProxies,
          'SetUrlMap',
          messages.ComputeTargetHttpProxiesSetUrlMapRequest(
              project='my-project',
              targetHttpProxy='target-http-proxy-1',
              urlMapReference=messages.UrlMapReference(
                  urlMap=('https://www.googleapis.com/compute/v1/projects/'
                          'my-project/global/urlMaps/my-map'))))],
    )

  def testWithoutURLMap(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --url-map: Must be specified.'):
      self.Run("""
          compute target-http-proxies update my-proxy
          """)

    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
