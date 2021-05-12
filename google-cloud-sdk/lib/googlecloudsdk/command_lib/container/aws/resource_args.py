# -*- coding: utf-8 -*- #
# Copyright 2021 Google LLC. All Rights Reserved.
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
"""Shared resource flags for GKE Multi-cloud for AWS commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties
from googlecloudsdk.core import resources


def GetOperationResource(op):
  return resources.REGISTRY.ParseRelativeName(
      op.name, collection='gkemulticloud.projects.locations.operations')


def AwsClusterAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='cluster', help_text='AWS cluster of the {resource}.')


def AwsNodePoolAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='node_pool', help_text='AWS node pool of the {resource}.')


def RegionAttributeConfig():
  return concepts.ResourceParameterAttributeConfig(
      name='region',
      help_text='Google Cloud region for the {resource}.',
      fallthroughs=[deps.PropertyFallthrough(properties.VALUES.aws.region)])


def GetAwsClusterResourceSpec():
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations.awsClusters',
      resource_name='cluster',
      awsClustersId=AwsClusterAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetAwsNodePoolResourceSpec():
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations.awsClusters.awsNodePools',
      resource_name='node_pool',
      awsNodePoolsId=AwsNodePoolAttributeConfig(),
      awsClustersId=AwsClusterAttributeConfig(),
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def GetRegionResourceSpec():
  return concepts.ResourceSpec(
      'gkemulticloud.projects.locations',
      resource_name='region',
      locationsId=RegionAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)


def AddAwsClusterResourceArg(parser, verb, positional=True):
  """Add a resource argument for an AWS cluster.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'cluster' if positional else '--cluster'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAwsClusterResourceSpec(),
      'AWS cluster {}.'.format(verb),
      required=True).AddToParser(parser)


def AddAwsNodePoolResourceArg(parser, verb, positional=True):
  """Add a resource argument for an AWS node pool.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
    positional: bool, whether the argument is positional or not.
  """
  name = 'node_pool' if positional else '--node-pool'
  concept_parsers.ConceptParser.ForResource(
      name,
      GetAwsNodePoolResourceSpec(),
      'AWS node pool {}.'.format(verb),
      required=True).AddToParser(parser)


def AddRegionResourceArg(parser, verb):
  """Add a resource argument for GKE Multi-cloud region.

  Args:
    parser: The argparse parser to add the resource arg to.
    verb: str, the verb to describe the resource, such as 'to update'.
  """
  concept_parsers.ConceptParser.ForResource(
      '--region',
      GetRegionResourceSpec(),
      'Google Cloud region {}.'.format(verb),
      required=True).AddToParser(parser)
