# -*- coding: utf-8 -*- #

# Copyright 2017 Google LLC. All Rights Reserved.
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

"""e2e tests for ml vision command group."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_base
from tests.lib import test_case


class VisionTests(e2e_base.WithServiceAuth):
  """E2E tests for ml vision command group."""

  def SetUp(self):
    self.image = self.Resource('tests', 'e2e', 'surface', 'ml', 'vision',
                               'testdata', 'face-input.png')
    self.track = calliope_base.ReleaseTrack.GA

  def _RunTest(self, command, resource):
    result = self.Run(
        'ml vision {command} {resource}'.format(command=command,
                                                resource=resource))
    # Check that there is at least one response and that there are no errors.
    self.assertTrue(result.responses)
    self.assertFalse(any([r.error for r in result.responses]))

  def testDetectFaces(self):
    self._RunTest('detect-faces', self.image)

  def testDetectText(self):
    self._RunTest('detect-text', self.image)

  def testDetectDocument(self):
    self._RunTest('detect-document', self.image)

  def testDetectLabels(self):
    self._RunTest('detect-labels', self.image)

  def testDetectLandmarks(self):
    self._RunTest('detect-landmarks', self.image)

  def testDetectLogos(self):
    self._RunTest('detect-logos', self.image)

  def testDetectWeb(self):
    self._RunTest('detect-web', self.image)

  def testDetectSafeSearch(self):
    self._RunTest('detect-safe-search', self.image)

  def testDetectImageProperties(self):
    self._RunTest('detect-image-properties', self.image)

  def testSuggestCrop(self):
    self._RunTest('suggest-crop', self.image)

  def testDetectObjects(self):
    self._RunTest('detect-objects', self.image)

if __name__ == '__main__':
  test_case.main()
