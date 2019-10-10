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

"""Base for Life Sciences gcloud unit tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import cli_test_base
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib.apitools import http_error


class _Base(cli_test_base.CliTestBase):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.messages = core_apis.GetMessagesModule('lifesciences', 'v2beta')

  def RunLifeSciences(self, command, gcloud_args=None):
    gcloud_args = gcloud_args or []
    return super(_Base, self).Run(gcloud_args + ['lifesciences'] + command)


class LifeSciencesUnitTest(sdk_test_base.WithFakeAuth, _Base):
  """Base class for Life Sciences unit tests."""

  def SetUp(self):
    self.mocked_client = mock.Client(
        core_apis.GetClientClass('lifesciences', 'v2beta'),
        real_client=core_apis.GetClientInstance(
            'lifesciences', 'v2beta', no_http=True))
    self.mocked_client.Mock()
    self.addCleanup(self.mocked_client.Unmock)

  def MakeHttpError(self, status_code, message='', failing_url=''):
    return http_error.MakeHttpError(code=status_code, message=message,
                                    url=failing_url)
