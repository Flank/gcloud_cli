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
"""Tests for the images describe subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.util import apis as core_apis
from tests.lib import test_case
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources

messages = core_apis.GetMessagesModule('compute', 'v1')


class ImagesDescribeTest(test_base.BaseTest, test_case.WithOutputCapture):

  def testSimpleCase(self):
    self.make_requests.side_effect = iter([
        [test_resources.IMAGES[0]],
    ])

    self.Run("""
        compute images describe image-1
        """)

    self.CheckRequests(
        [(self.compute_v1.images,
          'Get',
          messages.ComputeImagesGetRequest(
              image='image-1',
              project='my-project'))],
    )
    self.assertMultiLineEqual(
        self.GetOutput(),
        textwrap.dedent("""\
            name: image-1
            selfLink: https://compute.googleapis.com/compute/v1/projects/my-project/global/images/image-1
            status: READY
            """))


if __name__ == '__main__':
  test_case.main()
