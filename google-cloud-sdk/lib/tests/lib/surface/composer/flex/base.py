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
"""Base classes for Composer tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock as api_mock
from googlecloudsdk.api_lib.composer.flex import base as api_base
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class _ComposerFlexBase(cli_test_base.CliTestBase):
  """Base class for all Composer tests."""

  def SetTrack(self, track):
    self.track = track
    self.messages = apis.GetMessagesModule(
        api_base.API, api_base.GetApiVersion(release_track=track))


class ComposerFlexUnitTestBase(sdk_test_base.WithFakeAuth, _ComposerFlexBase):
  """Base for Composer Flex unit tests."""

  def SetTrack(self, track):
    super(ComposerFlexUnitTestBase, self).SetTrack(track)

    self.mock_context_service_client = api_mock.Client(
        apis.GetClientClass(api_base.API,
                            api_base.GetApiVersion(release_track=track)))
    self.mock_context_service_client.Mock()
    self.addCleanup(self.mock_context_service_client.Unmock)


class ComposerFlexContextsUnitTestBase(ComposerFlexUnitTestBase):
  """Base for Composer Flex Contexts unit tests."""

  def RunContextsCommand(self, *args):
    return self.Run(['composer', 'flex', 'contexts'] + list(args))

  def GetContextName(self, project, location, context_id):
    return 'projects/{0}/locations/{1}/contexts/{2}'.format(
        project, location, context_id)

  def ExpectContextDelete(self,
                          project,
                          location,
                          context_id,
                          response=None,
                          exception=None):
    if response is None and exception is None:
      response = self.messages.Operation(
      )  # Equivalent to google.protobuf.Empty
    self.mock_context_service_client.projects_locations_contexts.Delete.Expect(
        self.messages.ComposerflexProjectsLocationsContextsDeleteRequest(
            name=self.GetContextName(project, location, context_id)),
        response=response,
        exception=exception)
