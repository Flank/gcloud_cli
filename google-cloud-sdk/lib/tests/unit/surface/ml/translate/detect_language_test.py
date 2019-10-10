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

"""Tests for gcloud ml translate detect-language."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.ml.translate import base


class DetectLanguageBeta(base.MlTranslateTestBase):
  """Tests for gcloud ml translate detect-language."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SetUpForTrack(self.track)

  def _ExpectRequest(self, content=None, zone=None, mime_type=None, model=None):
    request = self.messages.TranslateProjectsLocationsDetectLanguageRequest(
        detectLanguageRequest=self.messages.DetectLanguageRequest(),
        parent='projects/fake-project/locations/{}'.format(zone)
    )
    if mime_type:
      request.detectLanguageRequest.mimeType = mime_type
    if model:
      request.detectLanguageRequest.model = ('projects/fake-project/locations/'
                                             '{}/models/language-detection/'
                                             '{}'.format(zone, model))
    request.detectLanguageRequest.content = content
    response = self.messages.DetectLanguageResponse()

    self.client.projects_locations.DetectLanguage.Expect(
        request,
        response=response,
        exception=None)

  def testBasicInvoke(self):
    self._ExpectRequest(content='Hello', zone='global')
    self.Run('ml translate detect-language --content Hello')

  def testModelSpecified(self):
    self._ExpectRequest(content='Hello', zone='global', model='model123')
    self.Run('ml translate detect-language --content Hello --model model123'
             ' --zone global')

  def testMimeTypeSpecified(self):
    self._ExpectRequest(content='Hello', zone='global', mime_type='text/html')
    self.Run('ml translate detect-language --content Hello --mime-type '
             'text/html')

  def testFileSpecified(self):
    data = 'Hello world'
    test_file = self.Touch(self.root_path, 'tmp.txt', contents=data)
    self._ExpectRequest(content='Hello world', zone='global')
    self.Run('ml translate detect-language --content-file {} --zone global'.
             format(test_file))
