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
"""anthos checkout tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import test_case
from tests.lib.surface.anthos import test_base as anthos_test_base


class GetTest(anthos_test_base.PackageUnitTestBase):

  def testGet(self):
    self.Run('anthos packages get '
             'git@github.com:/testuser/packages.git/my_package@v123 '
             '--local-dir my-package-dir '
             '--pattern "%n_%k_%s.yaml"')
    self.AssertValidBinaryCall(
        env={'COBRA_SILENCE_USAGE': 'true', 'GCLOUD_AUTH_PLUGIN': 'true'},
        command_args=[
            anthos_test_base._MOCK_ANTHOS_BINARY,
            'get',
            'git@github.com:/testuser/packages.git/my_package@v123',
            'my-package-dir',
            '--pattern',
            '%n_%k_%s.yaml'])


if __name__ == '__main__':
  test_case.main()
