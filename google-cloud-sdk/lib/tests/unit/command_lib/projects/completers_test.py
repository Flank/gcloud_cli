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

"""Unit tests for the compute.completers module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.resource_manager import completers
from tests.lib import completer_test_base


class ProjectsCompletersTest(completer_test_base.CompleterBase):

  def testProjectCompleter(self):
    completer = self.Completer(completers.ProjectCompleter)
    self.assertEqual(
        ['my-project', 'my_x_project', 'their_y_project', 'your_z_project'],
        completer.Complete('', self.parameter_info))
    self.assertEqual(
        ['their_y_project'],
        completer.Complete('t', self.parameter_info))
    self.assertEqual(
        ['your_z_project'],
        completer.Complete('*z*', self.parameter_info))
    self.assertEqual(
        [],
        completer.Complete('q', self.parameter_info))


if __name__ == '__main__':
  completer_test_base.main()
