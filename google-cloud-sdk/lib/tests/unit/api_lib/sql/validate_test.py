# -*- coding: utf-8 -*- #
# Copyright 2017 Google Inc. All Rights Reserved.
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
"""Tests for googlecloudsdk.api_lib.sql.validate."""
from __future__ import absolute_import
from __future__ import division

from __future__ import unicode_literals
from googlecloudsdk.api_lib.sql import validate
from tests.lib import test_case
from tests.lib.surface.sql import base

INSTANCE_NAME_VALIDATION_ERROR = (
    "Instance names cannot contain the ':' character. If you meant to "
    'indicate the\nproject for \\[{instance}\\], use only '
    "'{instance}' for the argument, and either add\n"
    "'--project {project}' to the command line or first run\n"
    '  \\$ gcloud config set project {project}')


class ValidateInstanceNameTest(base.SqlMockTestBeta):
  """Tests validate.ValidateInstanceName."""

  def testValidInstanceNames(self):
    validate.ValidateInstanceName('someinstance')
    validate.ValidateInstanceName('some-other-instance-1')

  def testInstanceNameWithOneColon(self):
    name = 'cool-project:good-instance'
    with self.AssertRaisesToolExceptionRegexp(
        INSTANCE_NAME_VALIDATION_ERROR.format(
            project='cool-project', instance='good-instance')):
      validate.ValidateInstanceName(name)

  def testInstanceNameWithTwoColons(self):
    name = 'cool-project:us-east1:good-instance'
    with self.AssertRaisesToolExceptionRegexp(
        INSTANCE_NAME_VALIDATION_ERROR.format(
            project='cool-project', instance='good-instance')):
      validate.ValidateInstanceName(name)

  def testInstanceNameWithMultipleColons(self):
    name = 'cool-project:something:else:entirely:good-instance'
    with self.AssertRaisesToolExceptionRegexp(
        INSTANCE_NAME_VALIDATION_ERROR.format(
            project='cool-project', instance='good-instance')):
      validate.ValidateInstanceName(name)


if __name__ == '__main__':
  test_case.main()
