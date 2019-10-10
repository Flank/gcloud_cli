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

"""Tests of the 'gcloud meta apis messages generate-export-schemas' command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.core.util import files
from tests.lib import cli_test_base
from tests.lib.command_lib.util.apis import base


class GenerateTest(base.Base, cli_test_base.CliTestBase):

  def SetUp(self):
    # Override the API discovery JSON directory. This points to a test data
    # dir that contains a fixed copy of cloudresourcemanager_v1.json.
    self.testdata_dir = self.Resource(
        'tests', 'unit', 'surface', 'meta', 'apis', 'testdata')
    self.temp_dir = os.path.join(self.temp_path, 'schemas')
    files.MakeDir(self.temp_dir)

  def testListExportSchema(self):
    self.Run('meta apis messages generate-export-schemas --verbosity=info '
             '--api=cloudresourcemanager --api-version=v1 Constraint '
             '--directory={}'.format(self.temp_dir))

    self.AssertFileEquals("""\
$schema: "http://json-schema.org/draft-06/schema#"

title: cloudresourcemanager v1 ListConstraint export schema
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
  suggestedValue:
    description: |-
      The Google Cloud Console will try to default to a configuration that
      matches the value specified in this `Constraint`.
    type: string
  supportsUnder:
    description: |-
      Indicates whether subtrees of Cloud Resource Manager resource hierarchy
      can be used in `Policy.allowed_values` and `Policy.denied_values`. For
      example, `"under:folders/123"` would match any resource under the
      'folders/123' folder.
    type: boolean
""", os.path.join(self.temp_dir, 'ListConstraint.yaml'))

    self.AssertFileEquals("""\
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
    type: booleanconstraint
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
    $ref: ListConstraint.yaml
  name:
    description: |-
      Immutable value, required to globally be unique. For example,
      `constraints/serviceuser.services`
    type: string
  version:
    description: Version of the `Constraint`. Default version is 0;
    type: integer
""", os.path.join(self.temp_dir, 'Constraint.yaml'))

    self.AssertErrEquals("""\
INFO: Generating JSON schema [{temp_dir}ListConstraint.yaml].
INFO: Generating JSON schema [{temp_dir}Constraint.yaml].
INFO: Display format: "none"
""".format(temp_dir=self.temp_dir + os.path.sep))


if __name__ == '__main__':
  cli_test_base.main()
