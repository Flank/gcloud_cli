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
"""ai-platform jobs cancel tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import parameterized
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


@parameterized.parameters('ml-engine', 'ai-platform')
class CancelTestGA(base.MlGaPlatformTestBase):

  def testCancel(self, module_name):
    self.client.projects_jobs.Cancel.Expect(
        self.msgs.MlProjectsJobsCancelRequest(
            name='projects/{}/jobs/opId'.format(self.Project())),
        self.msgs.GoogleProtobufEmpty()
    )

    self.Run('{} jobs cancel opId'.format(module_name))

    self.AssertOutputEquals('')


class CancelTestBeta(base.MlBetaPlatformTestBase, CancelTestGA):
  pass


class CancelTestAlpha(base.MlAlphaPlatformTestBase, CancelTestBeta):
  pass


if __name__ == '__main__':
  test_case.main()
