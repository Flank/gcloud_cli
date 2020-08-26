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
"""Tests for the public delegated prefix list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.public_prefixes import test_resources
import mock


class PublicDelegatedPrefixesListTest(test_base.BaseTest,
                                      completer_test_base.CompleterBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson', autospec=True)
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()

  def testTableOutput(self):
    self.list_json.side_effect = iter(
        [test_resources.PUBLIC_DELEGATED_PREFIXES_ALPHA])
    self.Run('compute public-delegated-prefixes list')

    request_params = {'includeAllScopes': True}
    if hasattr(
        self.messages.ComputePublicDelegatedPrefixesAggregatedListRequest,
        'returnPartialSuccess'):
      request_params['returnPartialSuccess'] = True

    aggregated_list_request = self.messages.ComputePublicDelegatedPrefixesAggregatedListRequest(
        project='my-project', **request_params)

    self.list_json.assert_called_once_with(
        requests=[(self.compute.publicDelegatedPrefixes, 'AggregatedList',
                   aggregated_list_request)],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        """\
NAME     LOCATION     PARENT_PREFIX  RANGE
my-pdp1  global       my-pap1        1.2.3.128/25
my-pdp2  us-central1  my-pap1        1.2.3.12/30
my-pdp3  us-east1     my-pap1        1.2.3.40/30
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
