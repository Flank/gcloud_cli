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
"""Tests for disk type completers for miscellaneous commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import completer_test_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class DiskTypesCompletionTest(test_base.BaseTest,
                              completer_test_base.CompleterBase):

  def testDiskTypesDescribeCompletion(self):
    self.AssertCommandArgCompleter(
        command='compute disk-types describe',
        arg='DISK_TYPE',
        module_path='command_lib.compute.completers.DiskTypesCompleter')

  def testDisksCreateCompletion(self):
    self.AssertCommandArgCompleter(
        command='compute disks create',
        arg='--type',
        module_path='command_lib.compute.completers.DiskTypesCompleter')


if __name__ == '__main__':
  test_case.main()
