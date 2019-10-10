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

"""Tests for gcloud ml translate batch-translate-text."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib.surface.ml.translate import base


class BatchTranslateTextBeta(base.MlTranslateTestBase):
  """Tests for gcloud ml translate batch-translate-text."""

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    self.SetUpForTrack(self.track)

  def _ExpectRequest(self, content=None, zone=None, models=None,
                     target_language=None, source_language=None, glossary=None,
                     destination=None):
    request = self.messages.TranslateProjectsLocationsBatchTranslateTextRequest(
        batchTranslateTextRequest=self.messages.BatchTranslateTextRequest(),
        parent='projects/fake-project/locations/{}'.format(zone)
    )
    request.batchTranslateTextRequest.sourceLanguageCode = source_language
    request.batchTranslateTextRequest.targetLanguageCodes = target_language
    request.batchTranslateTextRequest.inputConfigs = \
      [self.messages.InputConfig(gcsSource=self.messages.GcsSource(inputUri=k),
                                 mimeType=v if v else None)
       for k, v in content.items()]
    request.batchTranslateTextRequest.outputConfig = \
      self.messages.OutputConfig(
          gcsDestination=self.messages.GcsDestination(
              outputUriPrefix=destination))
    if models:
      request.batchTranslateTextRequest.models =\
        self.messages.BatchTranslateTextRequest.ModelsValue(
            additionalProperties=[
                self.messages.BatchTranslateTextRequest.ModelsValue.AdditionalProperty(
                    key=k, value='projects/fake-project/locations/{}/models/{}'.format(
                        zone, v)) for k, v in sorted(models.items())])
    if glossary:
      request.batchTranslateTextRequest.glossaries = \
      self.messages.BatchTranslateTextRequest.GlossariesValue(
          additionalProperties=[
              self.messages.BatchTranslateTextRequest.GlossariesValue.AdditionalProperty(
                  key=k, value=self.messages.TranslateTextGlossaryConfig(glossary='projects/fake-project/locations/{}/glossaries/{}'.format(
                      zone, v))) for k, v in sorted(glossary.items())])

    response = self.messages.Operation()

    self.client.projects_locations.BatchTranslateText.Expect(
        request,
        response=response,
        exception=None)

  def testBasicInvoke(self):
    self._ExpectRequest(content={'gs://test.txt': 'text/plain'}, zone='global',
                        target_language=['es-ES'], source_language='en-US',
                        destination='gs://test')
    self.Run('ml translate batch-translate-text --source '
             'gs://test.txt=text/plain'
             ' --target-language-codes es-ES --source-language en-US '
             '--destination gs://test')

  def testModels(self):
    self._ExpectRequest(content={'gs://test.txt': 'text/plain'}, zone='global',
                        target_language=['es-ES'], source_language='en-US',
                        destination='gs://test', models={'es-ES': 'TRL123',
                                                         'en-US': 'base/general'
                                                        })
    self.Run('ml translate batch-translate-text --source '
             'gs://test.txt=text/plain'
             ' --target-language-codes es-ES --source-language en-US '
             '--destination gs://test '
             '--models es-ES=TRL123,en-US=base/general')

  def testGlossaries(self):
    self._ExpectRequest(content={'gs://test.txt': 'text/plain'}, zone='global',
                        target_language=['es-ES'], source_language='en-US',
                        destination='gs://test', glossary={'es-ES': 'GLOS1',
                                                           'en-US': 'GLOS2'})
    self.Run('ml translate batch-translate-text --source '
             'gs://test.txt=text/plain'
             ' --target-language-codes es-ES --source-language en-US '
             '--destination gs://test '
             '--glossaries es-ES=GLOS1,en-US=GLOS2')
