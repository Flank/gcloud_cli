# -*- coding: utf-8 -*- # Lint as: python3
# Copyright 2020 Google Inc. All Rights Reserved.
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
"""Command to list all Apigee API proxies in the relevant organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class List(base.ListCommand):
  """List Apigee API proxies."""

  detailed_help = {
      "EXAMPLES": """\
  To list all API proxies for the active Cloud Platform project, run:

      $ {command}

  To list all API proxies in an Apigee organization called ``my-org'', run:

      $ {command} --organization=my-org
  """}

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser, "organization",
        "The organization whose API proxies should be listed.",
        positional=False, required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])
    parser.display_info.AddFormat("list")

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.organization.Parse().AsDict()
    result = apigee.APIsClient.List(identifiers)
    return [item["name"] for item in result["proxies"]]
