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
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.code import flags
from tests.lib import test_case
from tests.lib.calliope import util


class FlagsValidateTest(test_case.TestCase):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    flags.CommonFlags(self.parser)

  def testSqlExistsServiceAccountMissing(self):
    with self.assertRaises(flags.InvalidFlagError):
      namespace = self.parser.parse_args(['--cloudsql-instances=blah'])
      flags.Validate(namespace)

  def testSqlExistsServiceAccountPresent(self):
    namespace = self.parser.parse_args(
        ['--cloudsql-instances=blah', '--service-account=alsoblah'])
    # No exception means everything is OK
    flags.Validate(namespace)

  def testSqlExistsADCPresent(self):
    namespace = self.parser.parse_args(
        ['--cloudsql-instances=blah', '--application-default-credential'])
    # No exception means everything is OK
    flags.Validate(namespace)

  def testSqlMissingServiceAccountPresent(self):
    namespace = self.parser.parse_args(['--service-account=alsoblah'])
    # No exception means everything is OK
    flags.Validate(namespace)

  def testSqlMissingADCtPresent(self):
    namespace = self.parser.parse_args(['--application-default-credential'])
    # No exception means everything is OK
    flags.Validate(namespace)
