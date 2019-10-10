# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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
"""Tests for the images describe-from-family subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.compute import test_base


class ImagesDescribeFromFamilyTest(test_base.BaseTest):

  def SetUp(self):
    self.SelectApi('v1')

  def testSimpleCase(self):
    image = self.messages.Image(
        name='image-1',
        selfLink=('https://compute.googleapis.com/compute/beta/projects/my-project/'
                  'global/images/image-1'))
    self.make_requests.side_effect = iter([
        [image],
    ])

    self.Run("""
        compute images describe-from-family family-1
        """)

    self.CheckRequests(
        [(self.compute.images,
          'GetFromFamily',
          self.messages.ComputeImagesGetFromFamilyRequest(
              family='family-1',
              project='my-project'))],
    )

  def testURI(self):
    image = self.messages.Image(
        name='image-1',
        selfLink=('https://compute.googleapis.com/compute/beta/projects/my-project/'
                  'global/images/image-1'))
    self.make_requests.side_effect = iter([
        [image],
    ])

    self.Run("""
        compute images describe-from-family
        https://compute.googleapis.com/compute/beta/projects/my-project/global/images/family/family-1
        """)

    self.CheckRequests(
        [(self.compute.images,
          'GetFromFamily',
          self.messages.ComputeImagesGetFromFamilyRequest(
              family='family-1',
              project='my-project'))],
    )


if __name__ == '__main__':
  test_case.main()
