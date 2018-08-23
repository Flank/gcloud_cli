# -*- coding: utf-8 -*- #
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

"""Bundle tests for the lookup module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import gcloud
from googlecloudsdk.command_lib.static_completion import lookup
from googlecloudsdk.core.util import encoding
from tests.lib import sdk_test_base


class LookupBundleTests(sdk_test_base.BundledBase):
  """Bundle tests to ensure completion lookup works in a bundle."""

  def SetUp(self):
    class _FakeStream(object):

      @staticmethod
      def close():
        self.completions_closed = True

      @staticmethod
      def write(s):
        self.completions_value = encoding.Decode(s)

    self.StartObjectPatch(lookup, '_OpenCompletionsOutputStream',
                          return_value=_FakeStream())

    env = {lookup.IFS_ENV_VAR: ' ',
           lookup.LINE_ENV_VAR: 'gcloud --he',
           lookup.POINT_ENV_VAR: '11',
           '_ARGCOMPLETE': '1'}
    self.StartDictPatch('os.environ', env)

  def testLookupCompletion(self):
    lookup.Complete()
    self.assertEqual('--help', self.completions_value)

  def testGcloudPyCompletionEntryPoint(self):
    gcloud.main()
    self.assertEqual('--help', self.completions_value)


if __name__ == '__main__':
  sdk_test_base.main()
