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
"""beta ml vision tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import exceptions
from tests.lib import test_case
from tests.lib.surface.ml.vision import base as vision_base


class DetectTextPDFCommonTestGA(vision_base.MlVisionTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def __init__(self, *args, **kwargs):
    super(DetectTextPDFCommonTestGA, self).__init__(*args, **kwargs)
    self.model = None

  def testDetectTextPdf_Success(self):
    """Test `gcloud vision detect-text-pdf` runs & displays correctly."""
    input_file = 'gs://fake-bucket/fake-file'
    output_path = 'gs://fake-bucket/'
    self._ExpectAsyncBatchAnnotationRequest(
        input_file=input_file,
        output_path=output_path,
        feature_type=self.messages.Feature.\
          TypeValueValuesEnum.DOCUMENT_TEXT_DETECTION,
        mime_type='application/pdf',
        entity_field_name='textAnnotations',
        results=['animal', 'cat'],
        model=self.model)
    self.Run('ml vision detect-text-pdf {input_file} {output_path}'
             .format(input_file=input_file, output_path=output_path))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "response": {
            "textAnnotations": [
              {
                "confidence": 0.5,
                "description": "animal"
              },
              {
                "confidence": 0.5,
                "description": "cat"
              }
            ]
          }
        }
    """))

  def testDetectTextPdf_Error(self):
    """Test `gcloud vision detect-text-pdf` when an error is returned."""
    input_file = 'gs://fake-bucket/fake-file'
    output_path = 'gs://fake-bucket/'
    self._ExpectAsyncBatchAnnotationRequest(
        input_file=input_file,
        output_path=output_path,
        feature_type=self.messages.Feature.TypeValueValuesEnum.\
          DOCUMENT_TEXT_DETECTION,
        entity_field_name='textAnnotations',
        mime_type='application/pdf',
        error_message='Not found.',
        model=self.model)
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-text-pdf {input_file} {output_path}'
               .format(input_file=input_file, output_path=output_path))


class DetectTextPDFCommonTestBeta(DetectTextPDFCommonTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def __init__(self, *args, **kwargs):
    super(DetectTextPDFCommonTestBeta, self).__init__(*args, **kwargs)
    self.model = 'builtin/stable'

  def testDetectTextPdf_ModelVersion(self):
    input_file = 'gs://fake-bucket/fake-file'
    output_path = 'gs://fake-bucket/'
    self._ExpectAsyncBatchAnnotationRequest(
        input_file=input_file,
        output_path=output_path,
        feature_type=self.messages.Feature.TypeValueValuesEnum. \
          DOCUMENT_TEXT_DETECTION,
        entity_field_name='textAnnotations',
        mime_type='application/pdf',
        results=['bonjour', 'adios'],
        model='builtin/latest')
    self.Run('ml vision detect-text-pdf {input_file} {output_path} '
             '--model-version builtin/latest'
             .format(input_file=input_file, output_path=output_path))


class DetectTextPDFCommonTestAlpha(DetectTextPDFCommonTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def __init__(self, *args, **kwargs):
    super(DetectTextPDFCommonTestAlpha, self).__init__(*args, **kwargs)
    self.model = 'builtin/stable'


if __name__ == '__main__':

  test_case.main()
