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


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core import config
from googlecloudsdk.core import execution_utils
from tests.lib import sdk_test_base
from tests.lib import test_case


@test_case.Filters.SkipOnWindows('Need to enable completion tests on Windows',
                                 'b/24905560')
# requires gcloud to run
@sdk_test_base.Filters.RunOnlyInBundle
class CompletionBundle(sdk_test_base.BundledBase):
  """Bundle tests to ensure completion_test.sh script works in a bundle."""

  def SetUp(self):
    pass

  def testPythonArgComplete(self):
    gcloud_py_dir = os.path.dirname(config.GcloudPath())
    compdir = os.path.dirname(gcloud_py_dir)
    prog_dir = os.path.dirname(__file__)
    testfile = os.path.join(prog_dir, 'completion_test.sh')
    exitval = execution_utils.Exec([testfile, compdir], no_exit=True)
    self.assertTrue(exitval == 0)
    # Testing /bin/zsh requires running in a local environment that has zsh
    # installed.
    if os.path.isfile('/bin/zsh') and os.access('/bin/zsh', os.X_OK):
      exitval = execution_utils.Exec([testfile, '--shell=/bin/zsh', compdir],
                                     no_exit=True)
      self.assertTrue(exitval == 0)


if __name__ == '__main__':
  sdk_test_base.main()

