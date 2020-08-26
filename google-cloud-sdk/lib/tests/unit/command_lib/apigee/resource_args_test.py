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
"""Tests for googlecloudsdk.command_lib.apigee.resource_args."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.command_lib.apigee import resource_args
from tests.lib import cli_test_base
from tests.lib.calliope import util
from tests.lib.surface.apigee import base


class ResourceArgsTest(base.ApigeeIsolatedTest):

  def testResourceArgumentValidationFails(self):
    parser = util.ArgumentParser()
    resource_args.AddSingleResourceArgument(
        parser,
        "organization",
        "The Apigee organization that will test name validation logic.",
        validate=True)
    with self.assertRaises(cli_test_base.MockArgumentError):
      parser.parse_args(["invalid*org*name"]).CONCEPTS.organization.Parse()

  def testResourceArgumentValidationSucceeds(self):
    parser = util.ArgumentParser()
    resource_args.AddSingleResourceArgument(
        parser,
        "organization",
        "The Apigee organization that will test name validation logic.",
        validate=True)
    args = parser.parse_args(["valid-org1-name1"]).CONCEPTS.organization.Parse()
    self.assertEqual(args.organizationsId, "valid-org1-name1")

  def testResourceArgumentValidationDisabled(self):
    parser = util.ArgumentParser()
    resource_args.AddSingleResourceArgument(
        parser,
        "organization",
        "The Apigee organization that will test name validation logic.",
        validate=False)
    args = parser.parse_args(["invalid*org*name"]).CONCEPTS.organization.Parse()
    self.assertEqual(args.organizationsId, "invalid*org*name")

  def testResourceArgumentValidationUnneeded(self):
    parser = util.ArgumentParser()
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.developer.app",
        "The application that will test name validation logic.")
    weird_name = "\0invalid/nonsense"
    unparsed_args = ["--organization=oo", "--developer=" + weird_name, "a"]
    args = parser.parse_args(unparsed_args).CONCEPTS.app.Parse()
    self.assertEqual(args.developersId, weird_name)

  def testResourceArgumentValidationPermissive(self):
    parser = util.ArgumentParser()
    resource_args.AddSingleResourceArgument(
        parser,
        "organization.developer.app",
        "The application that will test name validation logic.",
        validate=True)
    weird_name = "\0invalid/nonsense"
    unparsed_args = ["--organization=oo", "--developer=" + weird_name, "a"]
    args = parser.parse_args(unparsed_args).CONCEPTS.app.Parse()
    self.assertEqual(args.developersId, weird_name)
