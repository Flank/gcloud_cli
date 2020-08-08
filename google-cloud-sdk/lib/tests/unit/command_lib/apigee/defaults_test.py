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
"""Tests for googlecloudsdk.command_lib.apigee.defaults."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import json

from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args
from tests.lib.calliope import util
from tests.lib.surface.apigee import base


class BrokenFallthrough(defaults.Fallthrough):
  _handled_fields = ["organization"]

  def __init__(self):
    super(BrokenFallthrough, self).__init__("panic")


class DefaultsTest(base.ApigeeSurfaceTest):

  def testFallthroughRequiresImplementation(self):
    parser = util.ArgumentParser()
    resource_args.AddSingleResourceArgument(
        parser,
        "organization",
        "The Apigee organization that will test fallback logic.",
        fallthroughs=[BrokenFallthrough()])
    with self.assertRaises(NotImplementedError):
      parser.parse_args([]).CONCEPTS.organization.Parse()

  def testAnomalousProjectMappings(self):
    canned_organization_response = {
        "organizations": [{
            "organization": "my-project",
            "projectIds": ["my-project"]
        },]
    }
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        body=json.dumps(canned_organization_response))
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/"
        "organizations/my-project/environments",
        body=json.dumps(["test"]))
    self.RunApigee("environments list --project=my-project")

    canned_organization_response = {
        "organizations": [
            {
                "organization": "my-project",
                "projectIds": ["new-project"]
            },
            {
                "organization": "my-project-changed",
                "projectIds": ["my-project"]
            },
        ]
    }
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/organizations",
        body=json.dumps(canned_organization_response))
    self.AddHTTPResponse(
        "https://apigee.googleapis.com/v1/"
        "organizations/my-project/environments",
        body=json.dumps(["test"]))
    self.RunApigee("environments list --project=new-project")
