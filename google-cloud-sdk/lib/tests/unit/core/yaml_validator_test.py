# -*- coding: utf-8 -*- #
# Copyright 2013 Google Inc. All Rights Reserved.
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

"""Tests for core yaml_validator module."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os
import tempfile

from googlecloudsdk.core import yaml_validator
from googlecloudsdk.core.util import files
from tests.lib import test_case


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


class ValidatorBase(test_case.Base):

  def _CreateSchema(self, name, contents):
    schema_path = os.path.join(self.schema_dir, '{}.yaml'.format(name))
    files.WriteFileContents(schema_path, contents)
    self.schema_path[name] = schema_path
    return schema_path

  def _GetSchemaPath(self, name):
    return self.schema_path.get(name)

  def _GetValidateFunction(self, name):
    return yaml_validator.Validator(self._GetSchemaPath(name)).Validate

  def SetUp(self):
    self.schema_path = {}
    self.schema_dir = tempfile.mkdtemp()


class ValidatorSchemaTest(ValidatorBase):

  def testSchemaNotFound(self):
    schema_path = os.path.join(self.schema_dir, 'Oops.yaml')
    with self.assertRaisesRegex(
        yaml_validator.InvalidSchemaError,
        'File not found .*Oops.yaml'):
      yaml_validator.Validator(schema_path)

  def testEmptySchemaCaught(self):
    self._CreateSchema('Invalid', '')
    with self.assertRaisesRegex(
        yaml_validator.InvalidSchemaVersionError,
        r'Schema .*Invalid.yaml\] version \[None\] is invalid. Expected '
        r'"\$schema: http://json-schema.org/\*/schema#".',
    ):
      self._GetValidateFunction('Invalid')

  def testStringSchemaCaught(self):
    self._CreateSchema('Invalid', 'oops')
    with self.assertRaisesRegex(
        yaml_validator.InvalidSchemaVersionError,
        r'Schema .*Invalid.yaml\] version \[None\] is invalid. Expected '
        r'"\$schema: http://json-schema.org/\*/schema#".',
    ):
      self._GetValidateFunction('Invalid')

  def testInvalidObjectSchemaCaught(self):
    self._CreateSchema('Invalid', 'foo: bar')
    with self.assertRaisesRegex(
        yaml_validator.InvalidSchemaVersionError,
        r'Schema .*Invalid.yaml\] version \[None\] is invalid. Expected '
        r'"\$schema: http://json-schema.org/\*/schema#".',
    ):
      self._GetValidateFunction('Invalid')


class ValidatorTest(ValidatorBase):

  def SetUp(self):
    for name, contents in (
        ('main', MAIN_SCHEMA),
        ('Job', JOB_SCHEMA),
        ('Status', STATUS_SCHEMA),
    ):
      self._CreateSchema(name, contents)
    self.validate = self._GetValidateFunction('main')

  def testMainNone(self):
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        "None is not of type 'object'"):
      self.validate(None)

  def testMainEmptyDict(self):
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        "'jobs' is a required property"):
      self.validate({})

  def testMainEmptyList(self):
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        r"\[\] is not of type 'object'"):
      self.validate([])

  def testMainInvalidKey(self):
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        'Additional properties are not allowed'):
      self.validate({'jobs': [], 'foo': 'bar'})

  def testMainJobsNotArray(self):
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        "'foo' is not of type 'array'"):
      self.validate({'jobs': 'foo'})

  def testMainJobsNoStatus(self):
    with self.assertRaisesRegex(
        yaml_validator.ValidationError,
        "'status' is a required property"):
      self.validate({'jobs': [{'priority': 'P1'}]})

  def testMainJobSchemaNotFound(self):
    # This confirms that the $ref schemas are lazy loaded.
    os.remove(self._GetSchemaPath('Job'))
    with self.assertRaisesRegex(
        yaml_validator.RefError,
        'File not found .*Job.yaml'):
      self.validate({'jobs': [{'priority': 'P1', 'status': 'active'}]})

  def testMainStatusSchemaNotFound(self):
    # This confirms that the $ref schemas are lazy loaded.
    os.remove(self._GetSchemaPath('Status'))
    with self.assertRaisesRegex(
        yaml_validator.RefError,
        'File not found .*Status.yaml'):
      self.validate({'jobs': [{'priority': 'P1', 'status': 'active'}]})

  def testMainJobsOK(self):
    self.validate({'jobs': [{'priority': 'P1', 'status': 'active'}]})


if __name__ == '__main__':
  test_case.main()
