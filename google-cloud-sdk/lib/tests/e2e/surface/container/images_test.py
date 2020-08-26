# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Integration tests for container clusters."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import shutil

from googlecloudsdk.core import log
from googlecloudsdk.core.util import files
from tests.lib import e2e_base

from tests.lib import e2e_utils
from tests.lib import test_case


@test_case.Filters.skip('likely GCR related', 'b/163030401')
class ImagesTest(e2e_base.WithServiceAuth):

  _CREATE_CMD = 'builds submit {0} -q --tag={1}'

  def SetUp(self):
    self._test_app = self.Resource('tests', 'e2e', 'surface', 'container',
                                   'test_data', 'tiny_docker_image',
                                   'Dockerfile')
    self.images_to_delete = []

  def _BuildImage(self, full_image_name):
    # We have to copy the Dockerfile to a temporary directory, because Docker
    # doesn't deal with symlinks well
    with files.TemporaryDirectory() as temp_dir:
      # We intentionally use copyfile because it DOES NOT preserve permissions.
      # When this test is run in blaze, deleting the temporary directory will
      # fail if the Dockerfile is copied without write permissions.
      shutil.copyfile(self._test_app, os.path.join(temp_dir, 'Dockerfile'))
      build = self.Run(self._CREATE_CMD.format(temp_dir, full_image_name))
      for img in build.results.images:
        name_without_tag = img.name.split(':')[0]
        name_by_digest = '{0}@{1}'.format(name_without_tag,
                                          img.digest)
        self.images_to_delete.append(name_by_digest)
    self.ClearOutput()

  def testListTags(self):
    # Docker naming makes this way more confusing than it needs to be. This test
    # pushes images to locations formatted like:
    # gcr.io/$PROJECT/e2etest:images-test-$DATETIME.
    image_tag = next(e2e_utils.GetResourceNameGenerator(prefix='images-test'))
    image_name = 'gcr.io/{0}/e2etest/{1}'.format(self.Project(), image_tag)
    image_name_with_tag = '{0}:{1}'.format(image_name, image_tag)

    self._BuildImage(image_name_with_tag)

    self.Run('alpha container images '
             'list-tags {0} --limit=1000'.format(image_name))
    self.AssertOutputContains(image_tag)

  def testListImages(self):
    # Docker naming makes this way more confusing than it needs to be. This test
    # pushes images to locations formatted like:
    # gcr.io/$PROJECT/e2etest/images-test-$DATETIME:latest.
    image_name = next(e2e_utils.GetResourceNameGenerator(prefix='images-test'))
    repository = 'gcr.io/{0}/e2etest'.format(self.Project())
    full_image_name = '{0}/{1}'.format(repository, image_name)

    self._BuildImage(full_image_name)
    self.Run('alpha container images list --repository={0}'.format(repository))
    self.AssertOutputContains(full_image_name)

  def TearDown(self):
    for img in self.images_to_delete:
      try:
        self.Run(
            'container images delete -q --force-delete-tags {0}'.format(img))
      # Don't fail the test if deletion fails for any reason.
      # The cleanup script will remove undeleted images.
      except Exception as e:  # pylint: disable=broad-except
        log.error('Error deleting image: {0}. Error: {1}'.format(img, e))


if __name__ == '__main__':
  test_case.main()
