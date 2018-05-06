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

"""Base class for all ml vision tests."""

from __future__ import absolute_import
from __future__ import unicode_literals

from apitools.base.py import encoding
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.command_lib.ml.vision import util
from tests.lib import cli_test_base
from tests.lib import sdk_test_base


class MlVisionTestBase(sdk_test_base.WithFakeAuth,
                       cli_test_base.CliTestBase):
  """Base class for ml vision command unit tests."""

  def SetUp(self):
    """Creates mock client and adds Unmock on cleanup."""
    self.track = calliope_base.ReleaseTrack.BETA
    self.client = mock.Client(client_class=apis.GetClientClass('vision', 'v1'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.messages = apis.GetMessagesModule(
        util.VISION_API, util.VISION_API_VERSION)

  def _ExpectEntityAnnotationRequest(self, image_path, feature_type,
                                     entity_field_name, max_results=None,
                                     results=None, error_message=None,
                                     language_hints=None, contents=None,
                                     model=None):
    """Expect requests that lead to EntityAnnotations.

    Args:
      image_path: str, the path to the image.
      feature_type: Feature, the message for the feature being requested.
      entity_field_name: str, the field name of the entity to annotate, e.g.
          logoAnnotations.
      max_results: int, the max results requested by the caller.
      results: [str], the list of entities to return.
      error_message: str, the error message to be given if an error is desired.
      language_hints: [str], the list of hints given by the caller.
      contents: bytes, the contents of the Image message if desired.
      model: str, the model version to use for the feature.
    """
    feature = self.messages.Feature(type=feature_type, model=model)
    if max_results:
      feature.maxResults = max_results
    image = self.messages.Image()
    if image_path:
      image.source = self.messages.ImageSource(imageUri=image_path)
    elif contents:
      image.content = contents
    annotate_request = self.messages.AnnotateImageRequest(
        features=[feature],
        image=image)
    if language_hints:
      annotate_request.imageContext = self.messages.ImageContext(
          languageHints=language_hints)
    request = self.messages.BatchAnnotateImagesRequest(
        requests=[annotate_request])
    responses = []
    if results:
      entities = [{'confidence': 0.5, 'description': r} for r in results]
      response = encoding.PyValueToMessage(
          self.messages.AnnotateImageResponse,
          {entity_field_name: entities})
      responses.append(response)
    if error_message:
      response = encoding.PyValueToMessage(
          self.messages.AnnotateImageResponse,
          {'error': {'code': 400,
                     'details': [],
                     'message': error_message}})
      responses.append(response)
    response = self.messages.BatchAnnotateImagesResponse(responses=responses)
    self.client.images.Annotate.Expect(request,
                                       response=response)
