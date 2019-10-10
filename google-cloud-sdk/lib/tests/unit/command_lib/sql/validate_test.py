# -*- coding: utf-8 -*- #
# Copyright 2017 Google LLC. All Rights Reserved.
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
"""Unit tests for SQL validation methods."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.sql import validate
from tests.lib import test_case


class InstanceValidateTest(test_case.TestCase):
  """Tests that SQL instance names are validated correctly."""

  def testRegexpRejectsBadChars(self):
    validator = validate.InstanceNameRegexpValidator()
    with self.assertRaises(arg_parsers.ArgumentTypeError):
      validator("INVALID_CHARS")

  def testRegexpAcceptsGoodChars(self):
    validator = validate.InstanceNameRegexpValidator()
    validator("valid-instance5")

  def testShowHelpfulMessageForColon(self):
    validator = validate.InstanceNameRegexpValidator()
    with self.assertRaises(exceptions.ToolException):
      validator("my-project:instance-name")
