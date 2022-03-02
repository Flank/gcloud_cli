# -*- coding: utf-8 -*- #
# Copyright 2022 Google LLC. All Rights Reserved.
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
"""Get a Workflow."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.cloudbuild.v2 import client_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.cloudbuild import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.Command):
  """Get a Workflow."""

  @staticmethod
  def Args(parser):
    """Register flags for this command.

    Args:
      parser: An argparse.ArgumentParser-like object. It is mocked out in order
        to capture some information, but behaves like an ArgumentParser.
    """
    concept_parsers.ConceptParser.ForResource(
        'WORKFLOW_ID',
        resource_args.GetWorkflowResourceSpec(),
        'Workflow.',
        required=True).AddToParser(parser)

  def Run(self, args):
    """This is what gets called when the user runs this command."""
    client = client_util.GetClientInstance()
    messages = client_util.GetMessagesModule()

    project = properties.VALUES.core.project.Get(required=True)
    parent = 'projects/%s/locations/%s' % (project, args.region)
    workflow_name = '%s/workflows/%s' % (parent, args.WORKFLOW_ID)

    workflow = client.projects_locations_workflows.Get(
        messages.CloudbuildProjectsLocationsWorkflowsGetRequest(
            name=workflow_name))
    return workflow
