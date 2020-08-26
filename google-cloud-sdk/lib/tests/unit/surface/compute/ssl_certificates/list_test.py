# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
from tests.lib.surface.compute.ssl_certificates import test_resources
import mock


class SslCertificatesListTest(test_base.BaseTest,
                              completer_test_base.CompleterBase):

  @property
  def _api(self):
    return 'v1'

  def SetUp(self):
    self.SelectApi(self._api)
    self.SetEncoding('utf-8')
    list_json_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.request_helper.ListJson')
    self.addCleanup(list_json_patcher.stop)
    self.list_json = list_json_patcher.start()
    self._resources = test_resources.MakeSslCertificates(
        self.messages, self._api)

  def RunVersioned(self, command):
    prefix = '' if self.api == 'v1' else self.api
    return self.Run('{prefix} {command}'.format(prefix=prefix, command=command))

  def testTableOutput(self):
    global_resources = [self._resources[0], self._resources[2]]
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(global_resources)
    ]
    self.RunVersioned("""
        compute ssl-certificates list --global
        """)
    self.list_json.assert_called_once_with(
        requests=[(self.compute.sslCertificates, 'List',
                   self.messages.ComputeSslCertificatesListRequest(
                       project='my-project'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME TYPE CREATION_TIMESTAMP EXPIRE_TIME MANAGED_STATUS
            ssl-cert-1 SELF_MANAGED 2017-12-18T11:11:11.000-07:00 2018-12-18T11:11:11.000-07:00
            ssl-cert-3 MANAGED 2017-12-17T10:00:00.000-07:00 2018-12-17T10:00:00.000-07:00 ACTIVE
            test1.certsbridge.com: ACTIVE
            xn--8a342mzfam5b18csni3w.certsbridge.com: FAILED_CAA_FORBIDDEN
            """),
        normalize_space=True)

  def testAggregateTableOutput(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self._resources)
    ]
    self.RunVersioned("""
        compute ssl-certificates list
        """)

    aggregated_list_request = self._getListRequestMessage('my-project')

    self.list_json.assert_called_once_with(
        requests=[(self.compute.sslCertificates, 'AggregatedList',
                   aggregated_list_request)],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME TYPE CREATION_TIMESTAMP EXPIRE_TIME MANAGED_STATUS
            ssl-cert-1 SELF_MANAGED 2017-12-18T11:11:11.000-07:00 2018-12-18T11:11:11.000-07:00
            ssl-cert-2 2014-10-04T07:56:33.679-07:00
            ssl-cert-3 MANAGED 2017-12-17T10:00:00.000-07:00 2018-12-17T10:00:00.000-07:00 ACTIVE
              test1.certsbridge.com: ACTIVE
              xn--8a342mzfam5b18csni3w.certsbridge.com: FAILED_CAA_FORBIDDEN
            """),
        normalize_space=True)

  def getUriOutput(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self._resources)
    ]
    self.RunVersioned("""
        compute ssl-certificates list --uri
        """)

    aggregated_list_request = self._getListRequestMessage('my-project')

    self.list_json.assert_called_once_with(
        requests=[(self.compute.sslCertificates, 'AggregatedList',
                   aggregated_list_request)],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def testUriOutput(self):
    self.getUriOutput()
    self.AssertOutputEquals(
        """\
{compute_uri}/projects/my-project/global/sslCertificates/ssl-cert-1
{compute_uri}/projects/my-project/regions/us-west-1/sslCertificates/ssl-cert-2
{compute_uri}/projects/my-project/global/sslCertificates/ssl-cert-3
""".format(compute_uri=self.compute_uri),
        normalize_space=True)

  def testRegionUriOutput(self):
    self.list_json.side_effect = [
        resource_projector.MakeSerializable(self._resources)
    ]
    self.RunVersioned("""
        compute ssl-certificates list --regions us-west-1 --uri
        """)

    self.list_json.assert_called_once_with(
        requests=[(self.compute.regionSslCertificates, 'List',
                   self.messages.ComputeRegionSslCertificatesListRequest(
                       project='my-project', region='us-west-1'))],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            {compute_uri}/projects/my-project/regions/us-west-1/sslCertificates/ssl-cert-2
            """.format(compute_uri=self.compute_uri)),
        normalize_space=True)

  def testSslCertificatesCompleter(self):
    # Completer always uses v1 API for List.
    self.SelectApi('v1')

    global_resources = [self._resources[0], self._resources[2]]
    regional_resources = [self._resources[1]]

    self.list_json.side_effect = [
        resource_projector.MakeSerializable(global_resources),
        resource_projector.MakeSerializable(regional_resources)
    ]
    self.RunCompleter(
        flags.SslCertificatesCompleterBeta,
        expected_command=[[
            'compute',
            'ssl-certificates',
            'list',
            '--global',
            '--uri',
            '--quiet',
            '--format=disable',
        ],
                          [
                              'compute',
                              'ssl-certificates',
                              'list',
                              '--filter=region:*',
                              '--uri',
                              '--quiet',
                              '--format=disable',
                          ]],
        expected_completions=[
            'ssl-cert-1',
            'ssl-cert-2',
            'ssl-cert-3',
        ],
        cli=self.cli,
    )

    aggregated_list_request = self._getListRequestMessage('my-project')

    self.list_json.assert_called_with(
        requests=[(self.compute.sslCertificates, 'AggregatedList',
                   aggregated_list_request)],
        http=self.mock_http(),
        batch_url=self.batch_url,
        errors=[])

  def _getListRequestMessage(self, project):
    return self.messages.ComputeSslCertificatesAggregatedListRequest(
        project=project, includeAllScopes=True)


class SslCertificatesListBetaTest(SslCertificatesListTest):

  @property
  def _api(self):
    return 'beta'


class SslCertificatesListAlphaTest(SslCertificatesListBetaTest):

  @property
  def _api(self):
    return 'alpha'

  def _getListRequestMessage(self, project):
    request_params = {'includeAllScopes': True}
    if hasattr(self.messages.ComputeSslCertificatesAggregatedListRequest,
               'returnPartialSuccess'):
      request_params['returnPartialSuccess'] = True

    return self.messages.ComputeSslCertificatesAggregatedListRequest(
        project=project, **request_params)


if __name__ == '__main__':
  test_case.main()
