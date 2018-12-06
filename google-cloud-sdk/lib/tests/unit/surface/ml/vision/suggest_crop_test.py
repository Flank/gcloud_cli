# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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

from apitools.base.py import encoding
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml.vision import base as vision_base


RESPONSE = """\
{
  "responses": [
    {
      "cropHintsAnnotation": {
        "cropHints": [
          {
            "boundingPoly": {
              "vertices": [
                {},
                {
                  "x": 1023
                },
                {
                  "x": 1023,
                  "y": 1023
                },
                {
                  "y": 1023
                }
              ]
            },
            "confidence": 0.79999995,
            "importanceFraction": 1.0
          }
        ]
      }
    }
  ]
}
"""


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA, 'builtin/stable'),
    ('Beta', calliope_base.ReleaseTrack.BETA, 'builtin/stable'),
    ('GA', calliope_base.ReleaseTrack.GA, None))
class SuggestCropCommonTest(vision_base.MlVisionTestBase):

  def testDetectCropRemotePath(self, track, model):
    """Test `vision detect-image-properties` runs & outputs correctly."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[self.messages.AnnotateImageRequest(
            features=[
                self.messages.Feature(
                    type=self.messages.Feature.TypeValueValuesEnum.CROP_HINTS,
                    model=model)],
            image=self.messages.Image(
                source=self.messages.ImageSource(imageUri=path_to_image)))])
    response = encoding.JsonToMessage(
        self.messages.BatchAnnotateImagesResponse, RESPONSE)
    self.client.images.Annotate.Expect(request, response=response)

    self.Run('ml vision suggest-crop {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent(RESPONSE))

  def testDetectCropWithAspectRatios(self, track, model):
    """Test `vision detect-image-properties` runs & outputs correctly."""
    self.track = track
    path_to_image = 'gs://fake-bucket/fake-file'
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[self.messages.AnnotateImageRequest(
            features=[
                self.messages.Feature(
                    type=self.messages.Feature.TypeValueValuesEnum.CROP_HINTS,
                    model=model)],
            image=self.messages.Image(
                source=self.messages.ImageSource(imageUri=path_to_image)),
            imageContext=self.messages.ImageContext(
                cropHintsParams=self.messages.CropHintsParams(
                    aspectRatios=[1.0, 2.0])))])
    response = encoding.JsonToMessage(
        self.messages.BatchAnnotateImagesResponse, RESPONSE)
    self.client.images.Annotate.Expect(request, response=response)

    self.Run('ml vision suggest-crop {path} --aspect-ratios 1.0,2:1'
             .format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent(RESPONSE))

  def testDetectCropLocalPath(self, track, model):
    """Test `detect-image-properties` with a local image path."""
    self.track = track
    path_to_image = self.Touch(self.root_path, contents='image')
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[self.messages.AnnotateImageRequest(
            features=[
                self.messages.Feature(
                    type=self.messages.Feature.TypeValueValuesEnum.CROP_HINTS,
                    model=model)],
            image=self.messages.Image(content=b'image'))])
    response = encoding.JsonToMessage(
        self.messages.BatchAnnotateImagesResponse, RESPONSE)
    self.client.images.Annotate.Expect(request, response=response)

    self.Run('ml vision suggest-crop {path}'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent(RESPONSE))


@parameterized.named_parameters(
    ('Alpha', calliope_base.ReleaseTrack.ALPHA),
    ('Beta', calliope_base.ReleaseTrack.BETA))
class SuggestCropAlphaBetaTest(vision_base.MlVisionTestBase):

  def testDetectCrop_ModelVersion(self, track):

    self.track = track
    path_to_image = self.Touch(self.root_path, contents='image')
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[self.messages.AnnotateImageRequest(
            features=[
                self.messages.Feature(
                    type=self.messages.Feature.TypeValueValuesEnum.CROP_HINTS,
                    model='builtin/latest')],
            image=self.messages.Image(content=b'image'))])
    response = encoding.JsonToMessage(
        self.messages.BatchAnnotateImagesResponse, RESPONSE)
    self.client.images.Annotate.Expect(request, response=response)

    self.Run('ml vision suggest-crop {path} '
             '--model-version builtin/latest'.format(path=path_to_image))
    self.AssertOutputEquals(textwrap.dedent(RESPONSE))


if __name__ == '__main__':
  test_case.main()
