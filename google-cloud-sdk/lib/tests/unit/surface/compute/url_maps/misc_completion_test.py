# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for autocompletion in url-maps subcommands."""
from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class UrlMapsCompletionTests(test_base.BaseTest,
                             completer_test_base.CompleterBase):

  def testUrlMapsInvalidateCdnCacheCompletion(self):
    lister_mock = self.StartPatch(
        'googlecloudsdk.api_lib.compute.lister.GetGlobalResourcesDicts',
        autospec=True)
    lister_mock.return_value = resource_projector.MakeSerializable(
        test_resources.URL_MAPS)
    self.RunCompletion('beta compute url-maps invalidate-cdn-cache u',
                       ['url-map-1', 'url-map-2', 'url-map-3', 'url-map-4'])


if __name__ == '__main__':
  test_case.main()
