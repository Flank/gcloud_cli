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

"""Tests of the 'gcloud meta apis collections list' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import exceptions
from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class LintTest(base.Base, cli_test_base.CliTestBase):

  def testList(self):
    """Just make sure it doesn't crash and that it prints something."""
    self.Run('meta apis collections lint')
    self.AssertOutputNotEquals('')

  def testListVersionNoAPI(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--api]: The --api-version flag can only be '
        'specified when using the --api flag.'):
      self.Run('meta apis collections lint --api-version=v12345')

  def testCompletion(self):
    self.MockAPIs(
        ('foo', 'v1', True),
        ('bar', 'v1', True),
        ('baz', 'v1', True))
    self.RunCompletion('meta apis collections lint --api b', ['bar', 'baz'])


if __name__ == '__main__':
  cli_test_base.main()
