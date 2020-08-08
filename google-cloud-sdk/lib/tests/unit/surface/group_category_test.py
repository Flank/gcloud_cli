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
"""Tests for googlecloudsdk.core.configurations.properties_file."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk import gcloud_main
from googlecloudsdk.calliope import walker
from tests.lib import sdk_test_base
from tests.lib import test_case

import six

CHILD_THRESHOLD = 10


class GroupCategoryTest(sdk_test_base.SdkBase):
  """Tests each Command Group in the CLI tree for gcloud has a category.

  if any of the following conditions are met :
  1. The node(Command Group)'s parent has more than CHILD_THRESHOLD children
  2. Any of the node's parent's child has category assigned.
  """

  def GetFailureListAsString(self, failure_list, indentation=2):
    return '\n'.join([
        ' ' * indentation + six.text_type(idx + 1) + '. ' + failure
        for idx, failure in enumerate(failure_list)
    ])

  def SetUp(self):
    self.cli = gcloud_main.CreateCLI([])
    self.failure_list = []
    self.missing_command_group_help_text = (
        'Failure indicates '
        'a missing category in the __init__.py for the following command '
        'group(s):\n{}\nTo add categories for this missing list, please add '
        'a class level category variable to the command group module\'s '
        '__init__.py.')

  def testCommandEachGroupHasCategory(self):
    GroupWalker(self.cli, self).Walk(hidden=False)
    self.assertFalse(
        self.failure_list,
        msg=self.missing_command_group_help_text.format(
            self.GetFailureListAsString(self.failure_list)))


class GroupWalker(walker.Walker):

  def __init__(self, cli, test):
    self.test = test
    super(GroupWalker, self).__init__(cli)

  def Visit(self, node, parent, is_group):

    def GetNonHiddenGroupCount(vertex):
      return len([
          group for group in vertex.groups
          if not vertex.groups[group].IsHidden()
      ])

    if not parent:
      return node
    enforce_category = False
    if is_group:
      if GetNonHiddenGroupCount(parent) > CHILD_THRESHOLD:
        enforce_category = True
      for _, group in six.iteritems(parent.groups):
        enforce_category = True if group.category else enforce_category
    if enforce_category and not node.category:
      self.test.failure_list.append(' '.join(node._path))
    return node


if __name__ == '__main__':
  test_case.main()
