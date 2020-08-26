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
"""Tests for the public advertised prefix list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.public_prefixes import test_resources
import mock


class PublicAdvertisedPrefixesListTest(test_base.BaseTest,
                                       completer_test_base.CompleterBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA
    self.SelectApi('alpha')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts')
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(
            test_resources.PUBLIC_ADVERTISED_PREFIXES_ALPHA))

  def testTableOutput(self):
    self.Run('compute public-advertised-prefixes list')
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.publicAdvertisedPrefixes,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        """\
NAME     RANGE          DNS_VERIFICATION_IP  STATUS
my-pap1  1.2.3.0/24     1.2.3.4              VALIDATED
my-pap2  100.66.0.0/16  100.66.20.1          PTR_CONFIGURED
""",
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
