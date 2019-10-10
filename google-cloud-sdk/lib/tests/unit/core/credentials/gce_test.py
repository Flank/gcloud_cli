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
"""Tests for googlecloudsdk.core.credentials.gce."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core.credentials import gce
from tests.lib import test_case


class TestGCEMetaData(test_case.Base):

  def SetUp(self):
    self.metadata = gce.Metadata()
    self.metadata.connected = True

  def testGetIdToken(self):
    mock_ReadNoProxyWithCleanFailures = self.StartObjectPatch(  # pylint: disable=invalid-name
        gce, '_ReadNoProxyWithCleanFailures')

    self.metadata.GetIdToken(
        '32555940559.apps.googleusercontent.com')
    mock_ReadNoProxyWithCleanFailures.assert_called_once_with(
        'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=32555940559.apps.googleusercontent.com&format=standard&licenses=FALSE',
        http_errors_to_ignore=(404,)
    )

  def testGetIdToken_FullFormat_IncludeLicense(self):
    mock_ReadNoProxyWithCleanFailures = self.StartObjectPatch(  # pylint: disable=invalid-name
        gce, '_ReadNoProxyWithCleanFailures')

    self.metadata.GetIdToken(
        '32555940559.apps.googleusercontent.com',
        token_format='full',
        include_license=True)
    mock_ReadNoProxyWithCleanFailures.assert_called_once_with(
        'http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/identity?audience=32555940559.apps.googleusercontent.com&format=full&licenses=TRUE',
        http_errors_to_ignore=(404,)
    )

if __name__ == '__main__':
  test_case.main()
