# -*- coding: utf-8 -*- #
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
"""Tests for the SSL certificates list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.ssl_certificates import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources
import mock


class SslCertificatesListTest(test_base.BaseTest,
                              completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts')
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    resources = test_resources.SSL_CERTIFICATES
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(resources))
    self.prefix = ''

  def RunVersioned(self, command):
    return self.Run('{prefix} {command}'.format(
        prefix=self.prefix, command=command))

  def testTableOutput(self):
    self.RunVersioned("""
        compute ssl-certificates list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.sslCertificates,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME       CREATION_TIMESTAMP
            ssl-cert-1 2014-09-04T09:56:33.679-07:00
            ssl-cert-2 2014-10-04T07:56:33.679-07:00
            """),
        normalize_space=True)

  def getUriOutput(self):
    self.RunVersioned("""
        compute ssl-certificates list --uri
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.sslCertificates,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])

  def testUriOutput(self):
    self.getUriOutput()
    self.AssertOutputEquals(
        """\
https://www.googleapis.com/compute/v1/projects/my-project/global/sslCertificates/ssl-cert-1
https://www.googleapis.com/compute/v1/projects/my-project/global/sslCertificates/ssl-cert-2
""",
        normalize_space=True)

  def testSslCertificatesCompleter(self):
    self.RunCompleter(
        flags.SslCertificatesCompleter,
        expected_command=[
            'compute',
            'ssl-certificates',
            'list',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
        expected_completions=[
            'ssl-cert-1',
            'ssl-cert-2',
        ],
        cli=self.cli,
    )
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.sslCertificates,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])


class SslCertificatesListBetaTest(SslCertificatesListTest):

  def SetUp(self):
    self.SelectApi('beta')
    self.SetEncoding('utf8')
    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    resources = test_resources.BETA_SSL_CERTIFICATES
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(resources))
    self.prefix = 'beta'

  def testTableOutput(self):
    self.RunVersioned("""
        compute ssl-certificates list
        """)
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.sslCertificates,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME TYPE CREATION_TIMESTAMP EXPIRE_TIME MANAGED_STATUS
            ssl-cert-1 SELF_MANAGED 2017-12-18T11:11:11.000-07:00 2018-12-18T11:11:11.000-07:00
            ssl-cert-2 MANAGED 2017-12-17T10:00:00.000-07:00 2018-12-17T10:00:00.000-07:00 ACTIVE
            test1.certsbridge.com: ACTIVE
            xn--8a342mzfam5b18csni3w.certsbridge.com: FAILED_CAA_FORBIDDEN
            """),
        normalize_space=True)

  def testUriOutput(self):
    self.getUriOutput()
    self.AssertOutputEquals(
        """\
https://www.googleapis.com/compute/beta/projects/my-project/global/sslCertificates/ssl-cert-1
https://www.googleapis.com/compute/beta/projects/my-project/global/sslCertificates/ssl-cert-2
""",
        normalize_space=True)


class SslCertificatesListAlphaTest(test_base.BaseTest,
                                   completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('alpha')
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()
    self.SetEncoding('utf8')

  def testTableOutput(self):
    resources = test_resources.ALPHA_SSL_CERTIFICATES
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(resources)
    ]
    self.Run('alpha compute ssl-certificates list --global')

    self.list_json.assert_called_once_with(
        requests=[(self.compute_alpha.sslCertificates, 'List',
                   self.messages.ComputeSslCertificatesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME TYPE CREATION_TIMESTAMP EXPIRE_TIME MANAGED_STATUS
            ssl-cert-1 SELF_MANAGED 2017-12-18T11:11:11.000-07:00 2018-12-18T11:11:11.000-07:00
            ssl-cert-2 MANAGED 2017-12-17T10:00:00.000-07:00 2018-12-17T10:00:00.000-07:00 ACTIVE
            test1.certsbridge.com: ACTIVE
            xn--8a342mzfam5b18csni3w.certsbridge.com: FAILED_CAA_FORBIDDEN
            """),
        normalize_space=True)

  def testUriOutput(self):
    resources = test_resources.ALPHA_SSL_CERTIFICATES
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(resources)
    ]
    self.Run('alpha compute ssl-certificates list --global --uri')

    self.list_json.assert_called_once_with(
        requests=[(self.compute_alpha.sslCertificates, 'List',
                   self.messages.ComputeSslCertificatesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/alpha/projects/my-project/global/sslCertificates/ssl-cert-1
            https://www.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/sslCertificates/ssl-cert-2
            """),
        normalize_space=True)

  def testRegionUriOutput(self):
    resources = test_resources.ALPHA_SSL_CERTIFICATES
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(resources)
    ]
    self.Run('alpha compute ssl-certificates list --regions us-west-1 --uri')

    self.list_json.assert_called_once_with(
        requests=[(self.compute_alpha.regionSslCertificates, 'List',
                   self.messages.ComputeRegionSslCertificatesListRequest(
                       project='my-project', region='us-west-1'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            https://www.googleapis.com/compute/alpha/projects/my-project/regions/us-west-1/sslCertificates/ssl-cert-2
            """),
        normalize_space=True)

  def testAggregateTableOutput(self):
    resources = test_resources.ALPHA_SSL_CERTIFICATES
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(resources)
    ]
    self.Run('alpha compute ssl-certificates list')

    self.list_json.assert_called_once_with(
        requests=[(self.compute_alpha.sslCertificates, 'AggregatedList',
                   self.messages.ComputeSslCertificatesAggregatedListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME TYPE CREATION_TIMESTAMP EXPIRE_TIME MANAGED_STATUS
            ssl-cert-1 SELF_MANAGED 2017-12-18T11:11:11.000-07:00 2018-12-18T11:11:11.000-07:00
            ssl-cert-2 MANAGED 2017-12-17T10:00:00.000-07:00 2018-12-17T10:00:00.000-07:00 ACTIVE
              test1.certsbridge.com: ACTIVE
              xn--8a342mzfam5b18csni3w.certsbridge.com: FAILED_CAA_FORBIDDEN
            """),
        normalize_space=True)


if __name__ == '__main__':
  test_case.main()
