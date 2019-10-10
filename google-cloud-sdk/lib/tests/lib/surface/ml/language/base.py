# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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

"""Base class for all ml language tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py.testing import mock

from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml.language import util
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base


class MlLanguageTestBase(sdk_test_base.WithFakeAuth,
                         cli_test_base.CliTestBase, parameterized.TestCase):
  """Base class for ml language command unit tests."""
  TRACKS = {
      calliope_base.ReleaseTrack.ALPHA: 'v1beta2',
      calliope_base.ReleaseTrack.BETA: 'v1beta2',
      calliope_base.ReleaseTrack.GA: 'v1',
  }

  def SetUp(self):
    # Test data
    self.data = 'Hello world'
    self.test_file = self.Touch(self.root_path, 'tmp.txt', contents=self.data)

  def SetTrack(self, track):
    self.track = track
    api_version = MlLanguageTestBase.TRACKS.get(track)
    self.messages = apis.GetMessagesModule(
        'language', api_version)
    self.client = mock.Client(
        apis.GetClientClass(util.LANGUAGE_API, api_version))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    # Shorten message names for convenience
    self.content_enum = self.messages.Document.TypeValueValuesEnum
    self.entity_encoding_enum = (self.messages.AnalyzeEntitiesRequest
                                 .EncodingTypeValueValuesEnum)
    self.sentiment_encoding_enum = (self.messages.AnalyzeSentimentRequest
                                    .EncodingTypeValueValuesEnum)
    self.syntax_encoding_enum = (self.messages.AnalyzeSyntaxRequest
                                 .EncodingTypeValueValuesEnum)
    self.entity_sentiment_encoding_enum = (self.messages
                                           .AnalyzeEntitySentimentRequest
                                           .EncodingTypeValueValuesEnum)

  def _CreateEntitiesResponse(self, entities, language, with_sentiment=False):
    entity_responses = []
    for entity in entities:
      response = {
          'mentions': [
              {
                  'text': {
                      'beginOffset': 0,
                      'content': entity
                  },
                  'type': 'COMMON'
              }
          ],
          'metadata': {},
          'name': entity,
          'salience': 1.0,
          'type': 'OTHER'
      }
      if with_sentiment:
        response['mentions'][0].update(
            {'sentiment': {'magnitude': 0.7, 'score': 0.7}})
        response.update({'sentiment': {'magnitude': 0.7, 'score': 0.7}})
      entity_responses.append(response)
    return {'entities': entity_responses, 'language': language}
