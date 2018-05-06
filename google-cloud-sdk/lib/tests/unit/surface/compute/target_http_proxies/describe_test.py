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
"""Tests for the url-maps describe subcommand."""
from __future__ import absolute_import
from __future__ import unicode_literals
import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class TargetHttpProxiesDescribeTest(test_base.BaseTest,
                                    completer_test_base.CompleterBase,
                                    test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.TARGET_HTTP_PROXIES[0]],
    ])

    self.Run("""
        compute target-http-proxies describe target-http-proxy-1
        """)

    self.CheckRequests(
        [(self.compute_v1.targetHttpProxies,
          'Get',
          messages.ComputeTargetHttpProxiesGetRequest(
              project='my-project',
              targetHttpProxy='target-http-proxy-1'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            description: My first proxy
            name: target-http-proxy-1
            selfLink: https://www.googleapis.com/compute/v1/projects/my-project/global/targetHttpProxies/target-http-proxy-1
            urlMap: https://www.googleapis.com/compute/v1/projects/my-project/global/urlMaps/url-map-1
            """))

  class MockTransformUri(object):

    def __init__(self, uri_list):
      self.original_uri_list = uri_list[:]
      self.Reset()

    def Reset(self):
      self.uri_list = self.original_uri_list[:]

    def Transform(self, *args, **kwargs):  # pylint: disable=unused-argument
      url_map = self.uri_list.pop()
      return ('https://www.googleapis.com/compute/v1/projects/my-project'
              '/global/targetHttpProxies/{0}').format(url_map)

  def testDesribeCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.TARGET_HTTP_PROXIES)
    uri_list = ['target-http-proxy-1', 'target-http-proxy-2',
                'target-http-proxy-3']
    self.RunCompletion('compute target-http-proxies describe t', uri_list)


if __name__ == '__main__':
  test_case.main()
