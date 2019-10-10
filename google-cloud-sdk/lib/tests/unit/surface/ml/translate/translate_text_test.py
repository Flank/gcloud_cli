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

"""Tests for gcloud ml translate translate-text."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.ml.translate import base


class TranslateTextBeta(base.MlTranslateTestBase):
  """Tests for gcloud ml translate translate-text."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SetUpForTrack(self.track)

  def _ExpectRequest(self, content=None, zone=None, mime_type=None, model=None,
                     target_language=None, source_language=None, glossary=None):
    request = self.messages.TranslateProjectsLocationsTranslateTextRequest(
        translateTextRequest=self.messages.TranslateTextRequest(),
        parent='projects/fake-project/locations/{}'.format(zone)
    )
    if mime_type:
      request.translateTextRequest.mimeType = mime_type
    if model:
      request.translateTextRequest.model = ('projects/fake-project/locations/'
                                            '{}/models/{}'.format(zone, model))
    if source_language:
      request.translateTextRequest.sourceLanguageCode = source_language
    if glossary:
      request.translateTextRequest.glossaryConfig = \
        self.messages.TranslateTextGlossaryConfig(glossary=glossary)

    request.translateTextRequest.contents = [content]
    request.translateTextRequest.targetLanguageCode = target_language
    response = self.messages.TranslateTextResponse()

    self.client.projects_locations.TranslateText.Expect(
        request,
        response=response,
        exception=None)

  def testBasicInvoke(self):
    self._ExpectRequest(content='Hello', zone='global', target_language='en-US')
    self.Run('ml translate translate-text --content Hello '
             '--target-language en-US')

  def testModelSpecified(self):
    self._ExpectRequest(content='Hello', zone='global', model='model123',
                        target_language='en-US')
    self.Run('ml translate translate-text --content Hello --model model123 '
             '--target-language en-US --zone global')

  def testMimeTypeSpecified(self):
    self._ExpectRequest(content='Hello', zone='global', mime_type='text/html',
                        target_language='en-US')
    self.Run('ml translate translate-text --content Hello --mime-type '
             'text/html --target-language en-US --zone global')

  def testFileSpecified(self):
    data = 'Hello world'
    test_file = self.Touch(self.root_path, 'tmp.txt', contents=data)
    self._ExpectRequest(content='Hello world', zone='global',
                        target_language='en-US')
    self.Run('ml translate translate-text --target-language en-US '
             '--content-file {} --zone global'.format(test_file))
