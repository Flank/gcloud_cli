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


class DetectObjectsCommonTestGA(vision_base.MlVisionTestBase):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.GA

  def __init__(self, *args, **kwargs):
    super(DetectObjectsCommonTestGA, self).__init__(*args, **kwargs)
    self.model = None

  def testDetectObjects_Success(self):
    """Test `gcloud vision detect-objects` runs & displays correctly."""
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.OBJECT_LOCALIZATION,
        'objectAnnotations',
        results=['animal', 'cat'],
        model=self.model)
    self.Run('ml vision detect-objects {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "objectAnnotations": [
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
          ]
        }
    """))

  def testDetectObjects_LocalPath(self):
    """Test `gcloud vision detect-objects` with a local image path."""
    tempdir = self.CreateTempDir()
    path_to_image = self.Touch(tempdir, name='imagefile', contents='image')
    self._ExpectEntityAnnotationRequest(
        None,
        self.messages.Feature.TypeValueValuesEnum.OBJECT_LOCALIZATION,
        'objectAnnotations',
        results=['animal', 'cat'],
        contents=b'image',
        model=self.model)
    self.Run('ml vision detect-objects {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent("""\
        {
          "responses": [
            {
              "objectAnnotations": [
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
          ]
        }
    """))

  def testDetectObjects_Error(self):
    """Test `gcloud vision detect-objects` when an error is returned."""
    path_to_image = 'gs://fake-bucket/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.OBJECT_LOCALIZATION,
        'objectAnnotations',
        error_message='Not found.',
        model=self.model)
    with self.AssertRaisesExceptionMatches(exceptions.Error,
                                           'Code: [400] Message: [Not found.]'):
      self.Run('ml vision detect-objects {path}'.format(path=path_to_image))


class DetectObjectsCommonTestBeta(DetectObjectsCommonTestGA):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def __init__(self, *args, **kwargs):
    super(DetectObjectsCommonTestBeta, self).__init__(*args, **kwargs)
    self.model = 'builtin/stable'

  def testDetectText_ModelVersion(self):
    path_to_image = 'https://example.com/fake-file'
    self._ExpectEntityAnnotationRequest(
        path_to_image,
        self.messages.Feature.TypeValueValuesEnum.OBJECT_LOCALIZATION,
        'objectAnnotations',
        results=['bonjour', 'adios'],
        model='builtin/latest')
    self.Run('ml vision detect-objects {path} --model-version builtin/latest'
             .format(path=path_to_image))


class DetectObjectsCommonTestAlpha(DetectObjectsCommonTestBeta):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def __init__(self, *args, **kwargs):
    super(DetectObjectsCommonTestAlpha, self).__init__(*args, **kwargs)
    self.model = 'builtin/stable'


if __name__ == '__main__':
  test_case.main()
