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

"""Module containing a base class for Cloud SDK diagnostics tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import cli_test_base

from six.moves import zip  # pylint: disable=redefined-builtin


class DiagnosticTestBase(cli_test_base.CliTestBase):
  """A base class for Cloud SDK diagnostics tests."""

  def AssertResultEqual(self, result_a, result_b):
    self.assertEqual(result_a.passed, result_b.passed)
    self.assertEqual(result_a.message, result_b.message)
    self.AssertFailuresEqual(result_a.failures, result_b.failures)

  def AssertFailuresEqual(self, failures_a, failures_b):
    for a, b in zip(failures_a, failures_b):
      self.assertEqual(a.message, b.message)
      self.assertIsInstance(a.exception, type(b.exception))
