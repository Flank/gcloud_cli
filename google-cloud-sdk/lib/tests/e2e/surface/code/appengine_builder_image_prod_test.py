# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import contextlib
import json

from googlecloudsdk.command_lib.code import local
from tests.lib import test_case
import six
import six.moves.urllib.request


class GaeBuilder(test_case.TestCase):
  """Verify that the builder image paths we generate are available in prod.

  The test shouldn't care if appengine adds a new runtime, and I also assume
  that appengine is consistent about making builder images for all their
  runtimes. What I want to catch here is appengine changing the name format of
  their builder images (including the 'argo_current' tag name) or dropping them
  altogether.
  """

  def testGeneratedImageExists(self):
    some_gae_supported_runtime = 'python37'
    gcr_path = local._GaeBuilder(some_gae_supported_runtime)
    image_path, requested_tag = gcr_path.split(':')
    tags_list = self._getImageTagsFromContainerRegistry(image_path)
    self.assertIn(requested_tag, tags_list['tags'])

  def _getImageTagsFromContainerRegistry(self, image_path):
    host, path = image_path.split('/', 1)
    # Docs at https://docs.docker.com/registry/spec/api/#listing-image-tags
    tags_list_api_url = 'https://%s/v2/%s/tags/list' % (host, path)
    with contextlib.closing(
        six.moves.urllib.request.urlopen(tags_list_api_url)) as response:
      return json.loads(
          six.ensure_text(
              response.read()
          )
      )


if __name__ == '__main__':
  test_case.main()
