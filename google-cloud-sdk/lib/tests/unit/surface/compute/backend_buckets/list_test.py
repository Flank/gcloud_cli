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
"""Tests for the backend-buckets list subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.command_lib.compute.backend_buckets import flags
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.backend_buckets import test_resources
import mock


class BackendBucketsListGaTest(test_base.BaseTest,
                               completer_test_base.CompleterBase):

  def SetUp(self):
    self.SelectApi('v1')
    self._backend_buckets = test_resources.BACKEND_BUCKETS

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts')
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(self._backend_buckets))

  def RunList(self, command):
    self.Run('compute backend-buckets list ' + command)

  def testTableOutput(self):
    self.RunList('')
    self.mock_get_global_resources.assert_called_once_with(
        service=self.compute.backendBuckets,
        project='my-project',
        http=self.mock_http(),
        filter_expr=None,
        batch_url=self.batch_url,
        errors=[])
    self.AssertOutputEquals(
        textwrap.dedent("""\
            NAME GCS_BUCKET_NAME ENABLE_CDN
            backend-bucket-1-enable-cdn-false gcs-bucket-1 False
            backend-bucket-2-enable-cdn-true gcs-bucket-2 True
            backend-bucket-3-enable-cdn-false gcs-bucket-3
            """), normalize_space=True)

  def testBackendBucketsCompleter(self):
    completer = self.Completer(flags.BackendBucketsCompleter, cli=self.cli)
    self.assertEqual(['backend-bucket-1-enable-cdn-false',
                      'backend-bucket-2-enable-cdn-true',
                      'backend-bucket-3-enable-cdn-false'],
                     completer.Complete('', self.parameter_info))


class BackendBucketsListAlphaTest(BackendBucketsListGaTest):

  def SetUp(self):
    self.SelectApi('alpha')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_ALPHA

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(self._backend_buckets))

  def RunList(self, command):
    self.Run('alpha compute backend-buckets list ' + command)

  def testBackendBucketsCompleter(self):
    completer = self.Completer(flags.BackendBucketsCompleter, cli=self.cli)
    self.assertEqual(['backend-bucket-1-enable-cdn-false',
                      'backend-bucket-2-enable-cdn-true',
                      'backend-bucket-3-enable-cdn-false'],
                     completer.Complete('', self.parameter_info))


class BackendBucketsListBetaTest(BackendBucketsListGaTest):

  def SetUp(self):
    self.SelectApi('beta')
    self._backend_buckets = test_resources.BACKEND_BUCKETS_BETA

    lister_patcher = mock.patch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    self.addCleanup(lister_patcher.stop)
    self.mock_get_global_resources = lister_patcher.start()
    self.mock_get_global_resources.return_value = (
        resource_projector.MakeSerializable(self._backend_buckets))

  def RunList(self, command):
    self.Run('beta compute backend-buckets list ' + command)

  def testBackendBucketsCompleter(self):
    completer = self.Completer(flags.BackendBucketsCompleter, cli=self.cli)
    self.assertEqual(['backend-bucket-1-enable-cdn-false',
                      'backend-bucket-2-enable-cdn-true',
                      'backend-bucket-3-enable-cdn-false'],
                     completer.Complete('', self.parameter_info))


if __name__ == '__main__':
  test_case.main()
