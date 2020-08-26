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
"""Tests for the ssl policy export subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import textwrap

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core.console import console_io
from tests.lib import test_case
from tests.lib.surface.compute import ssl_policies_test_base
from tests.lib.surface.compute.ssl_policies import test_resources


class SslPoliciesExportTestAlpha(ssl_policies_test_base.SslPoliciesTestBase):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
    self._api = 'alpha'
    self._existing_ssl_policy = test_resources.SSL_POLICIES_ALPHA[0]
    self._resource_name = 'ssl-policy-1'

  def SetUp(self):
    self._SetUp(self.track)

  def RunExport(self, command):
    self.Run('compute ssl-policies export ' + command)

  def testExportToStdOut(self):
    ssl_policy_ref = self.GetSslPolicyRef(self._resource_name)
    self.ExpectGetRequest(ssl_policy_ref, self._existing_ssl_policy)

    self.RunExport(self._resource_name)

    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            minTlsVersion: TLS_1_0
            name: %(name)s
            profile: COMPATIBLE
            selfLink: https://compute.googleapis.com/compute/%(api)s/projects/my-project/global/sslPolicies/%(name)s
            """ % {
                'api': self._api,
                'name': self._resource_name
            }))

  def testExportToFile(self):
    ssl_policy_ref = self.GetSslPolicyRef(self._resource_name)
    self.ExpectGetRequest(ssl_policy_ref, self._existing_ssl_policy)

    file_name = os.path.join(self.temp_path, 'export.yaml')

    self.RunExport('{0} --destination {1}'.format(self._resource_name,
                                                  file_name))

    data = console_io.ReadFromFileOrStdin(file_name or '-', binary=False)
    exported_ssl_policy = export_util.Import(
        message_type=self.messages.SslPolicy, stream=data)
    self.assertEqual(self._existing_ssl_policy, exported_ssl_policy)


if __name__ == '__main__':
  test_case.main()
