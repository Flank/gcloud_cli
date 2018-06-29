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
"""Tests for api_lib.container.images.container_data_util."""

from __future__ import absolute_import
from __future__ import unicode_literals
from containerregistry.client import docker_name

from googlecloudsdk.api_lib.container.images import container_data_util

from tests.lib import test_case

_IMAGE_STR = (
    'gcr.io/foobar/baz@sha256:'
    '0422a02d982780308b998f12f9235d1afb26a3e736cafc04adb44c71a612d921')


class ContainerDataUtilTest(test_case.TestCase):

  def testContainerData(self):
    img_name = docker_name.Digest(_IMAGE_STR)
    cdata = container_data_util.ContainerData(
        img_name.registry, img_name.repository, img_name.digest)

    # Assert that ContainerData's __str__ contains the starting digest.
    self.assertEqual(_IMAGE_STR, cdata.image_summary.fully_qualified_digest)


if __name__ == '__main__':
  test_case.main()
