# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Package containing unit tests for fingerprinting module.
"""

from __future__ import absolute_import
from __future__ import unicode_literals
from googlecloudsdk.api_lib.app.ext_runtimes import fingerprinting
from googlecloudsdk.core import properties
from tests.lib import test_case


class TestFingerprinting(test_case.TestCase):

  def SetUp(self):
    properties.VALUES.core.disable_prompts.Set(False)

  def testGetNonInteractiveErrorMessage(self):
    self.assertEqual(fingerprinting.GetNonInteractiveErrorMessage(), '')
    properties.VALUES.core.disable_prompts.Set(True)
    self.assertEqual(fingerprinting.GetNonInteractiveErrorMessage(),
                     ' ' + fingerprinting._PROMPTS_DISABLED_ERROR_MESSAGE)


if __name__ == '__main__':
  test_case.main()
