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
"""Flags for Eventarc commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope.concepts import concepts
from googlecloudsdk.calliope.concepts import deps
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from googlecloudsdk.core import properties

_IAM_API_VERSION = 'v1'


def LocationAttributeConfig():
  """Builds an AttributeConfig for the location resource."""
  return concepts.ResourceParameterAttributeConfig(
      name='location',
      fallthroughs=[
          deps.PropertyFallthrough(properties.FromString('eventarc/location'))
      ],
      help_text="The location for the Eventarc {resource}, which should be "
      "either ``global'' or one of the supported regions. Alternatively, set "
      "the [eventarc/location] property.")


def TriggerAttributeConfig():
  """Builds an AttributeConfig for the trigger resource."""
  return concepts.ResourceParameterAttributeConfig(name='trigger')


def TransportTopicAttributeConfig():
  """Builds an AttributeConfig for the transport topic resource."""
  return concepts.ResourceParameterAttributeConfig(name='transport-topic')


def AddTransportTopicResourceArg(parser, required=False):
  """Adds a resource argument for a customer-provided transport topic."""
  resource_spec = concepts.ResourceSpec(
      'pubsub.projects.topics',
      resource_name='Pub/Sub topic',
      topicsId=TransportTopicAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)
  concept_parser = concept_parsers.ConceptParser.ForResource(
      '--transport-topic',
      resource_spec,
      "The Cloud Pub/Sub topic to use for the trigger's transport "
      'intermediary. This feature is currently only available for triggers '
      "of event type ``google.cloud.pubsub.topic.v1.messagePublished''. "
      'The topic must be in the same project as the trigger. '
      'If not specified, a transport topic will be created.',
      required=required)
  concept_parser.AddToParser(parser)


def AddLocationResourceArg(parser, group_help_text, required=False):
  """Adds a resource argument for an Eventarc location."""
  resource_spec = concepts.ResourceSpec(
      'eventarc.projects.locations',
      resource_name='location',
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)
  concept_parser = concept_parsers.ConceptParser.ForResource(
      '--location', resource_spec, group_help_text, required=required)
  concept_parser.AddToParser(parser)


def AddTriggerResourceArg(parser, group_help_text, required=False):
  """Adds a resource argument for an Eventarc trigger."""
  resource_spec = concepts.ResourceSpec(
      'eventarc.projects.locations.triggers',
      resource_name='trigger',
      triggersId=TriggerAttributeConfig(),
      locationsId=LocationAttributeConfig(),
      projectsId=concepts.DEFAULT_PROJECT_ATTRIBUTE_CONFIG)
  concept_parser = concept_parsers.ConceptParser.ForResource(
      'trigger', resource_spec, group_help_text, required=required)
  concept_parser.AddToParser(parser)


def AddServiceAccountArg(parser, required=False):
  """Adds an argument for the trigger's service account."""
  parser.add_argument(
      '--service-account',
      required=required,
      help='The IAM service account email associated with the trigger.')


def AddEventFiltersArg(parser, release_track, required=False):
  """Adds an argument for the trigger's event filters."""
  if release_track == base.ReleaseTrack.GA:
    flag = '--event-filters'
    help_text = (
        "The trigger's list of filters that apply to CloudEvents attributes. "
        "This flag can be repeated to add more filters to the list. Only "
        "events that match all these filters will be sent to the destination. "
        "The filters must include the ``type'' attribute, as well as any other "
        "attributes that are expected for the chosen type.")
  else:
    flag = '--matching-criteria'
    help_text = (
        "The criteria by which events are filtered for the trigger, specified "
        "as a comma-separated list of CloudEvents attribute names and values. "
        "This flag can also be repeated to add more criteria to the list. Only "
        "events that match with this criteria will be sent to the destination. "
        "The criteria must include the ``type'' attribute, as well as any "
        "other attributes that are expected for the chosen type.")
  parser.add_argument(
      flag,
      action=arg_parsers.UpdateAction,
      type=arg_parsers.ArgDict(),
      required=required,
      help=help_text,
      metavar='ATTRIBUTE=VALUE')


def GetEventFiltersArg(args, release_track):
  """Gets the event filters from the arguments."""
  if release_track == base.ReleaseTrack.GA:
    return args.event_filters
  else:
    return args.matching_criteria


def AddDestinationArgs(parser, release_track, required=False):
  """Adds arguments related to trigger's destination."""
  dest_group = parser.add_mutually_exclusive_group(
      required=required,
      help='Flags for specifying the destination to which events should be sent.'
  )
  _AddCloudRunDestinationArgs(dest_group)
  if release_track == base.ReleaseTrack.GA:
    _AddGKEDestinationArgs(dest_group, hidden=True)


def _AddCloudRunDestinationArgs(parser, required=False):
  """Adds arguments related to trigger's Cloud Run fully-managed service destination."""
  run_group = parser.add_group(
      required=required,
      help='Flags for specifying a Cloud Run fully-managed service destination.'
  )
  AddDestinationRunServiceArg(run_group, required=True)
  AddDestinationRunPathArg(run_group)
  AddDestinationRunRegionArg(run_group)


def _AddGKEDestinationArgs(parser, required=False, hidden=False):
  """Adds arguments related to trigger's GKE service destination."""
  gke_group = parser.add_group(
      required=required,
      hidden=hidden,
      help='Flags for specifying a GKE service destination.')
  _AddDestinationGKEClusterArg(gke_group, required=True)
  _AddDestinationGKELocationArg(gke_group)
  _AddDestinationGKENamespaceArg(gke_group)
  _AddDestinationGKEServiceArg(gke_group, required=True)
  _AddDestinationGKEPathArg(gke_group)


def AddDestinationRunServiceArg(parser, required=False):
  """Adds an argument for the trigger's destination Cloud Run service."""
  parser.add_argument(
      '--destination-run-service',
      required=required,
      help='Name of the Cloud Run fully-managed service that receives the '
      'events for the trigger. The service must be in the same project as the '
      'trigger.')


def AddDestinationRunPathArg(parser, required=False):
  """Adds an argument for the trigger's destination path on the Cloud Run service."""
  parser.add_argument(
      '--destination-run-path',
      required=required,
      help='Relative path on the destination Cloud Run service to which '
      "the events for the trigger should be sent. Examples: ``/route'', "
      "``route'', ``route/subroute''.")


def AddDestinationRunRegionArg(parser, required=False):
  """Adds an argument for the trigger's destination Cloud Run service's region."""
  parser.add_argument(
      '--destination-run-region',
      required=required,
      help='Region in which the destination Cloud Run service can be '
      'found. If not specified, it is assumed that the service is in the same '
      'region as the trigger.')


def _AddDestinationGKEClusterArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's cluster."""
  parser.add_argument(
      '--destination-gke-cluster',
      required=required,
      help='Name of the GKE cluster that the destination GKE service is '
      'running in.')


def _AddDestinationGKELocationArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's location."""
  parser.add_argument(
      '--destination-gke-location',
      required=required,
      help='Location of the GKE cluster that the destination GKE service '
      'is running in. If not specified, it is assumed that the cluster is a '
      'regional cluster and is in the same region as the trigger.')


def _AddDestinationGKENamespaceArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's namespace."""
  parser.add_argument(
      '--destination-gke-namespace',
      required=required,
      help='Namespace that the destination GKE service is running in. If '
      "not specified, it defaults to the ``default'' namespace.")


def _AddDestinationGKEServiceArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's name."""
  parser.add_argument(
      '--destination-gke-service',
      required=required,
      help='Name of the destination GKE service that receives the events '
      'for the trigger. The service must be in the same project as the trigger.'
  )


def _AddDestinationGKEPathArg(parser, required=False):
  """Adds an argument for the trigger's destination GKE service's name."""
  parser.add_argument(
      '--destination-gke-path',
      required=required,
      help='Relative path on the destination GKE service to which '
      "the events for the trigger should be sent. Examples: ``/route'', "
      "``route'', ``route/subroute''.")


def AddClearServiceAccountArg(parser):
  """Adds an argument for clearing the trigger's service account."""
  parser.add_argument(
      '--clear-service-account',
      action='store_true',
      help='Clear the IAM service account associated with the trigger.')


def AddClearDestinationRunPathArg(parser):
  """Adds an argument for clearing the trigger's destination path."""
  parser.add_argument(
      '--clear-destination-run-path',
      action='store_true',
      help='Clear the relative path on the destination Cloud Run service to '
      'which the events for the trigger should be sent.')


def AddTypePositionalArg(parser, help_text):
  """Adds a positional argument for the event type."""
  parser.add_argument('type', help=help_text)


def AddTypeArg(parser, required=False):
  """Adds an argument for the event type."""
  parser.add_argument('--type', required=required, help='The event type.')


def AddServiceNameArg(parser, required=False):
  """Adds an argument for the value of the serviceName CloudEvents attribute."""
  parser.add_argument(
      '--service-name',
      required=required,
      help='The value of the serviceName CloudEvents attribute.')
