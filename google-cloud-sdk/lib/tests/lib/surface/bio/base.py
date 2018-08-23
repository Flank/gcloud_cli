# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Base class for all bio tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.bio import bio
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error


class _Base(cli_test_base.CliTestBase):

  def RunBio(self, command):
    return self.Run(['alpha', 'bio'] + command)


class BioUnitTestBase(sdk_test_base.WithFakeAuth, _Base):
  """Base class for all Bio unit tests that use fake auth and mocks."""

  def SetUp(self):
    self.mock_client = mock.Client(
        bio.Bio.GetClientClass(),
        real_client=bio.Bio.GetClientInstance(no_http=True))
    self.mock_client.Mock()
    self.addCleanup(self.mock_client.Unmock)

    # Initialize the Bio endpoint after creating the mock, or else
    # the mock is not picked up.
    bio.Bio.Init()
    self.messages = bio.Bio(self.Project()).GetMessages()

  def MakeHttpError(self, status_code, message='', failing_url=''):
    """Returns a properly structured HttpError for testing."""
    # TODO(b/67435348): Remove this wrapper entirely
    return http_error.MakeHttpError(code=status_code, message=message,
                                    url=failing_url)


class BioIntegrationTest(_Base, e2e_base.WithServiceAuth):
  """Base class for all Bio integration tests."""

  def SetUp(self):
    bio.Bio.Init()
    self.messages = bio.Bio(self.Project()).GetMessages()
