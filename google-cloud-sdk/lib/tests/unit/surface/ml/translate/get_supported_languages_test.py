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

"""Tests for gcloud ml translate get-supported-languages."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.ml.translate import base


class GetSupportedLanguagesBeta(base.MlTranslateTestBase):
  """Tests for gcloud ml translate get-supported-languages."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SetUpForTrack(self.track)

  def _ExpectRequest(self, zone=None, display_code=None, model=None):
    request = self.messages.TranslateProjectsLocationsGetSupportedLanguagesRequest(
        displayLanguageCode=None,
        model=None,
        parent='projects/fake-project/locations/{}'.format(zone)
    )
    if display_code:
      request.displayLanguageCode = display_code
    if model:
      request.model = ('projects/fake-project/locations/'
                       '{}/models/{}'.format(zone, model))
    response = self.messages.SupportedLanguages(
        languages=[self.messages.SupportedLanguage()])

    self.client.projects_locations.GetSupportedLanguages.Expect(
        request,
        response=response,
        exception=None)

  def testBasicInvoke(self):
    self._ExpectRequest(zone='global')
    self.Run('ml translate get-supported-languages')

  def testModelSpecified(self):
    self._ExpectRequest(zone='us-central1', model='model123')
    self.Run('ml translate get-supported-languages --zone us-central1 '
             '--model model123')

  def testDisplaySpecified(self):
    self._ExpectRequest(zone='global', display_code='en_US')
    self.Run('ml translate get-supported-languages --zone global '
             '--display-language-code en_US')

