# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Unit tests for kuberuncli module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.kuberun import kuberuncli
from googlecloudsdk.core.util import files
from tests.lib import sdk_test_base
from tests.lib import test_case


class KubeRuncliTest(sdk_test_base.SdkBase):

  def SetUp(self):
    find_exec = self.StartObjectPatch(files, 'FindExecutableOnPath')
    find_exec.return_value = '/path/to/kuberun'

  def test_GetEnvArgsForCommand(self):
    self.StartEnvPatch({'foo': 'foo-value', 'excl': 'excl-value'}, clear=True)
    actual = kuberuncli.GetEnvArgsForCommand(
        extra_vars={'extra': 'extra-value'}, exclude_vars=['excl'])
    expected = {'foo': 'foo-value', 'extra': 'extra-value'}
    self.assertDictEqual(expected, actual)


if __name__ == '__main__':
  test_case.main()
