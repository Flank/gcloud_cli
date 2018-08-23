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

"""Module for test base classes."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import logging

from apitools.base.py import exceptions
from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
import httplib2


class BaseTest(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase):
  """Base class for gcloud iam.tests.unit."""

  def Project(self):
    """The project to use for this test."""
    return 'test-project'

  def SetUp(self):
    self.msgs = apis.GetMessagesModule('iam', 'v1')
    self.sample_unique_id = '123456789876543212345'

    properties.VALUES.core.project.Set(self.Project())
    self.client = mock.Client(client_class=apis.GetClientClass('iam', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    log.SetVerbosity(logging.INFO)

  def MockHttpError(self, status, reason, body=None, url=None):
    """Creates a mock HTTP error.

    Useful to mock client interactions with missing resources.

    Args:
      status: The HTTP status.
      reason: Why the error occurred.
      body: The body of the response.
      url: The URL this error occurred at.

    Returns:
      An HttpError object.
    """
    if body is None:
      body = ''
    response = httplib2.Response({'status': status, 'reason': reason})
    return exceptions.HttpError(response, body, url)
