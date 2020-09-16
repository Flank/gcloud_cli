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
"""Command to list all API products in the relevant Apigee organization."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib import apigee
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.apigee import defaults
from googlecloudsdk.command_lib.apigee import resource_args


class List(base.ListCommand):
  """List Apigee API products."""

  detailed_help = {
      "DESCRIPTION":
          "{description}",
      "EXAMPLES":
          """
          To list all API products for the active Cloud Platform project, run:

              $ {command}

          To get a JSON array of all the API products in an organization named
          ``my-org'', run:

              $ {command} --organization=my-org --format=json
          """
  }

  @staticmethod
  def Args(parser):
    resource_args.AddSingleResourceArgument(
        parser,
        "organization",
        "Apigee organization whose products should be listed.",
        positional=False,
        required=True,
        fallthroughs=[defaults.GCPProductOrganizationFallthrough()])
    parser.display_info.AddFormat("list(name)")

  def Run(self, args):
    """Run the list command."""
    identifiers = args.CONCEPTS.organization.Parse().AsDict()
    return apigee.ProductsClient.List(identifiers)
