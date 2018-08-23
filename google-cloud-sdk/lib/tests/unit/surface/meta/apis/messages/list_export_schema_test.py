# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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

"""Tests of the 'gcloud meta apis messages list-export-schema' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class ListTest(base.Base, cli_test_base.CliTestBase):

  def SetUp(self):
    # Override the API discovery JSON directory. This points to a test data
    # dir that contains a fixed copy of cloudresourcemanager_v1.json.
    self.testdata_dir = self.Resource(
        'tests', 'unit', 'surface', 'meta', 'apis', 'testdata')

  def testListExportSchema(self):
    self.Run('meta apis messages list-export-schema '
             '--api=cloudresourcemanager --api-version=v1 Constraint')
    self.AssertOutputEquals("""\
$schema: "http://json-schema.org/draft-06/schema#"

title: cloudresourcemanager v1 Constraint export schema
description: A gcloud export/import command YAML validation schema.
type: object
additionalProperties: false
properties:
  COMMENT:
    type: object
    description: User specified info ignored by gcloud import.
    additionalProperties: false
    properties:
      template-id:
        type: string
      region:
        type: string
      description:
        type: string
      date:
        type: string
      version:
        type: string
  UNKNOWN:
    type: array
    description: Unknown API fields that cannot be imported.
    items:
      type: string
  booleanConstraint:
    description: Defines this constraint as being a BooleanConstraint.
    type: boolean
  constraintDefault:
    description: |-
      The evaluation behavior of this constraint in the absense of 'Policy'.
    type: string
    enum:
    - ALLOW
    - CONSTRAINT_DEFAULT_UNSPECIFIED
    - DENY
  description:
    description: |-
      Detailed description of what this `Constraint` controls as well as how and
      where it is enforced.  Mutable.
    type: string
  displayName:
    description: The human readable name.  Mutable.
    type: string
  listConstraint:
    description: Defines this constraint as being a ListConstraint.
    type: object
    additionalProperties: false
    properties:
      suggestedValue:
        description: |-
          The Google Cloud Console will try to default to a configuration that
          matches the value specified in this `Constraint`.
        type: string
  name:
    description: |-
      Immutable value, required to globally be unique. For example,
      `constraints/serviceuser.services`
    type: string
  version:
    description: Version of the `Constraint`. Default version is 0;
    type: integer
""")


if __name__ == '__main__':
  cli_test_base.main()
