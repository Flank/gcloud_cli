# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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

"""Tests for the `gcloud meta validate-yaml` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import tempfile

from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.util import files
from tests.lib import cli_test_base


MAIN_SCHEMA = """
$schema: "http://json-schema.org/draft-06/schema#"

title: test main schema
description: A test main schema.
type: object
required:
  - jobs
additionalProperties: false
properties:
  jobs:
    description: Active jobs.
    type: array
    items: {$ref: "Job.yaml"}
  labels:
    description: |-
      Some name=value labels.
    type: object
    additionalProperties:
      description: Additional junk we didn't plan for.
      type: string
"""

JOB_SCHEMA = """
$schema: "http://json-schema.org/draft-06/schema#"

title: test job schema
description: A test job schema.
type: object
required:
- status
additionalProperties: false
properties:
  labels:
    description: |-
      Some name=value labels.
    type: object
    additionalProperties:
      description: More junk we forgot.
      type: string
  priority:
    description: The job priority.
    type: string
  status: {$ref: "Status.yaml"}
"""

STATUS_SCHEMA = """
$schema: "http://json-schema.org/draft-06/schema#"

title: test job schema
description: A test job status.
type: string
"""


class ValidateBase(cli_test_base.CliTestBase):

  def _CreateSchema(self, name, contents):
    schema_path = os.path.join(self.schema_dir, '{}.yaml'.format(name))
    files.WriteFileContents(schema_path, contents)
    self.schema_path[name] = schema_path
    return schema_path

  def _GetSchemaPath(self, name):
    return self.schema_path.get(name)

  def SetUp(self):
    self.schema_path = {}
    self.schema_dir = tempfile.mkdtemp()


class ValidateYAMLSchemaTest(ValidateBase):

  def testSchemaNotFound(self):
    schema_path = os.path.join(self.schema_dir, 'Oops.yaml')
    with self.assertRaisesRegex(
        yaml_validator.InvalidSchemaError,
        'File not found .*Oops.yaml'):
      self.Run('meta validate-yaml {} {}'.format(schema_path, os.devnull))

  def testEmptySchemaCaught(self):
    schema_path = self._CreateSchema('Invalid', '')
    with self.assertRaisesRegex(
        yaml_validator.InvalidSchemaVersionError,
        r'Schema .*Invalid.yaml\] version \[None\] is invalid. Expected '
        r'"\$schema: http://json-schema.org/\*/schema#".',
    ):
      self.Run('meta validate-yaml {} {}'.format(schema_path, os.devnull))

  def testStringSchemaCaught(self):
    schema_path = self._CreateSchema('Invalid', 'oops')
    with self.assertRaisesRegex(
        yaml_validator.InvalidSchemaVersionError,
        r'Schema .*Invalid.yaml\] version \[None\] is invalid. Expected '
        r'"\$schema: http://json-schema.org/\*/schema#".',
    ):
      self.Run('meta validate-yaml {} {}'.format(schema_path, os.devnull))

  def testInvalidObjectSchemaCaught(self):
    schema_path = self._CreateSchema('Invalid', 'foo: bar')
    with self.assertRaisesRegex(
        yaml_validator.InvalidSchemaVersionError,
        r'Schema .*Invalid.yaml\] version \[None\] is invalid. Expected '
        r'"\$schema: http://json-schema.org/\*/schema#".',
    ):
      self.Run('meta validate-yaml {} {}'.format(schema_path, os.devnull))


class ValidateYAMLTest(ValidateBase):

  def SetUp(self):
    for name, contents in (
        ('main', MAIN_SCHEMA),
        ('Job', JOB_SCHEMA),
        ('Status', STATUS_SCHEMA),
    ):
      self._CreateSchema(name, contents)

  def _CreateYAMLData(self, contents):
    data_path = os.path.join(self.schema_dir, 'data.yaml')
    files.WriteFileContents(data_path, contents)
    return data_path

  def testMainEmptyDict(self):
    data_path = self._CreateYAMLData('{}\n')
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        "'jobs' is a required property"):
      self.Run('meta validate-yaml {} {}'.format(
          self._GetSchemaPath('main'), data_path))

  def testMainEmptyList(self):
    data_path = self._CreateYAMLData('[]\n')
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        r"\[\] is not of type 'object'"):
      self.Run('meta validate-yaml {} {}'.format(
          self._GetSchemaPath('main'), data_path))

  def testMainInvalidKey(self):
    data_path = self._CreateYAMLData('jobs: []\nfoo: bar\n')
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        'Additional properties are not allowed'):
      self.Run('meta validate-yaml {} {}'.format(
          self._GetSchemaPath('main'), data_path))

  def testMainJobsNotArray(self):
    data_path = self._CreateYAMLData('jobs: foo\n')
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        "'foo' is not of type 'array'"):
      self.Run('meta validate-yaml {} {}'.format(
          self._GetSchemaPath('main'), data_path))

  def testMainJobsNoStatus(self):
    data_path = self._CreateYAMLData('jobs:\n  - priority: P1\n')
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        "'status' is a required property"):
      self.Run('meta validate-yaml {} {}'.format(
          self._GetSchemaPath('main'), data_path))

  def testMainJobSchemaNotFound(self):
    # This confirms that the $ref schemas are lazy loaded.
    data_path = self._CreateYAMLData(
        'jobs:\n  - priority: P1\n    status: active\n')
    os.remove(self._GetSchemaPath('Job'))
    with self.assertRaisesRegex(
        yaml_validator.RefError,
        'File not found .*Job.yaml'):
      self.Run('meta validate-yaml {} {}'.format(
          self._GetSchemaPath('main'), data_path))

  def testMainStatusSchemaNotFound(self):
    # This confirms that the $ref schemas are lazy loaded.
    data_path = self._CreateYAMLData(
        'jobs:\n  - priority: P1\n    status: active\n')
    os.remove(self._GetSchemaPath('Status'))
    with self.assertRaisesRegex(
        yaml_validator.RefError,
        'File not found .*Status.yaml'):
      self.Run('meta validate-yaml {} {}'.format(
          self._GetSchemaPath('main'), data_path))

  def testMainJobsOK(self):
    data_path = self._CreateYAMLData(
        'jobs:\n  - priority: P1\n    status: active\n')
    self.Run('meta validate-yaml {} {}'.format(
        self._GetSchemaPath('main'), data_path))


if __name__ == '__main__':
  cli_test_base.main()
