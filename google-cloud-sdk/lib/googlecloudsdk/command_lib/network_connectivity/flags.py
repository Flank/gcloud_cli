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
"""Common flags for network connectivity commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.network_connectivity import util
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.command_lib.util.concepts import presentation_specs

GLOBAL_ARGUMENT = '--global'
REGION_ARGUMENT = '--region'


def AddAsyncFlag(parser):
  """Add the --async argument to the given parser."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddGlobalFlag(parser):
  """Add the --global argument to the given parser."""
  parser.add_argument(
      GLOBAL_ARGUMENT,
      help='Specify if a resource is global.',
      hidden=True,
      action=util.StoreGlobalAction)


def AddRegionFlag(parser):
  """Add the --region argument to the given parser."""
  parser.add_argument(
      REGION_ARGUMENT,
      help=""" \
        A Google Cloud region. To see the names of regions, see [Viewing a list of available regions](https://cloud.google.com/compute/docs/regions-zones/viewing-regions-zones#viewing_a_list_of_available_regions).""")  # pylint: disable=line-too-long


def AddRegionGroup(parser):
  """Add a group which contains the global and region arguments to the given parser."""
  region_group = parser.add_group(required=False, mutex=True)
  AddGlobalFlag(region_group)
  AddRegionFlag(region_group)


def SpokeAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='spoke', help_text='The spoke Id.')


def LocationAttributeConfig(spoke_location_arguments):
  location_fallthroughs = [
      deps.ArgFallthrough(arg) for arg in spoke_location_arguments
  ]
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      help_text='The location Id.',
      fallthroughs=location_fallthroughs)


def GetSpokeResourceSpec(spoke_location_arguments):
  return concepts.ResourceSpec(
      'networkconnectivity.projects.locations.spokes',
      resource_name='spoke',
      spokesId=SpokeAttributeConfig(),
      locationsId=LocationAttributeConfig(spoke_location_arguments),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetSpokeLocationArguments(vpc_spoke_only_command):
  if not vpc_spoke_only_command:
    return [REGION_ARGUMENT]
  else:
    return [GLOBAL_ARGUMENT]


def AddSpokeResourceArg(parser, verb, vpc_spoke_only_command=False):
  """Add a resource argument for a spoke.

  NOTE: Must be used only if it's the only resource arg in the command.

  Args:
    parser: the parser for the command.
    verb: str, the verb to describe the resource, such as 'to update'.
    vpc_spoke_only_command: bool, if the spoke resource arg is for a VPC
      spoke-specific command.
  """
  spoke_location_arguments = GetSpokeLocationArguments(vpc_spoke_only_command)
  presentation_spec = presentation_specs.ResourcePresentationSpec(
      name='spoke',
      concept_spec=GetSpokeResourceSpec(spoke_location_arguments),
      required=True,
      flag_name_overrides={'location': ''},
      group_help='Name of the spoke {}.'.format(verb),
  )
  concept_parsers.ConceptParser([presentation_spec]).AddToParser(parser)
