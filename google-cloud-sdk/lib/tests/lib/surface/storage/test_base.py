# Lint as: python3
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
"""A base class for gcloud storage tests.

Similar to gsutil/gslib/tests/testcase/base.py
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib.e2e_utils import GetResourceNameGenerator


class StorageTestBase(cli_test_base.CliTestBase):
  """Base class for gcloud surface storage tests."""

  def SetUp(self):
    self.bucket_name_generator = GetResourceNameGenerator(prefix='bucket')
    self.object_name_generator = GetResourceNameGenerator(prefix='object')

    # In many cases, our Run functions return generators, which are only
    # readable once. Cloud SDK displays generator output to the user by
    # default, so our tests cannot read from the generators again. Therefore,
    # we turn the default off, so tests can run asserts on the output.
    properties.VALUES.core.user_output_enabled.Set(False)
