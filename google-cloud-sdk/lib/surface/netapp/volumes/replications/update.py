# -*- coding: utf-8 -*- #
# Copyright 2023 Google LLC. All Rights Reserved.
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
"""Update a Cloud NetApp Volume Replication."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.netapp.volumes.replications import client as replications_client
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.netapp import flags
from googlecloudsdk.command_lib.netapp.volumes.replications import flags as replications_flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.util.concepts import concept_parsers

from googlecloudsdk.core import log


# TODO(b/239613419):
# Keep gcloud beta netapp group hidden until v1beta1 API stable
# also restructure release tracks that GA \subset BETA \subset ALPHA once
# BETA is public.
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA)
class UpdateBeta(base.UpdateCommand):
  """Update a Cloud NetApp Volume Replication."""

  _RELEASE_TRACK = base.ReleaseTrack.BETA

  @staticmethod
  def Args(parser):
    """Add args for updating a Replication."""
    concept_parsers.ConceptParser(
        [flags.GetReplicationPresentationSpec('The Replication to update.')]
    ).AddToParser(parser)
    replications_flags.AddReplicationVolumeArg(parser)
    replications_flags.AddReplicationReplicationScheduleArg(
        parser, required=False
    )
    flags.AddResourceAsyncFlag(parser)
    flags.AddResourceDescriptionArg(parser, 'Replication')
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    """Update a Cloud NetApp Volume Replication in the current project."""
    replication_ref = args.CONCEPTS.replication.Parse()

    if args.CONCEPTS.volume.Parse() is None:
      raise exceptions.RequiredArgumentException(
          '--volume', 'Requires a volume to update replication of'
      )

    client = replications_client.ReplicationsClient(self._RELEASE_TRACK)
    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    original_replication = client.GetReplication(replication_ref)

    # Update labels
    if labels_diff.MayHaveUpdates():
      labels = labels_diff.Apply(
          client.messages.Replication.LabelsValue, original_replication.labels
      ).GetOrNone()
    else:
      labels = None

    replication_schedule_enum = (
        replications_flags.GetReplicationReplicationScheduleEnumFromArg(
            args.replication_schedule, client.messages
        )
    )

    replication = client.ParseUpdatedReplicationConfig(
        original_replication, description=args.description, labels=labels,
        replication_schedule=replication_schedule_enum,
    )

    updated_fields = []
    # add possible updated replication fields
    # TODO(b/243601146) add config mapping and separate config file for update
    if args.IsSpecified('description'):
      updated_fields.append('description')
    if (
        args.IsSpecified('update_labels')
        or args.IsSpecified('remove_labels')
        or args.IsSpecified('clear_labels')
    ):
      updated_fields.append('labels')
    if args.IsSpecified('replication_schedule'):
      updated_fields.append('replication_schedule')
    update_mask = ','.join(updated_fields)

    result = client.UpdateReplication(
        replication_ref, replication, update_mask, args.async_
    )
    if args.async_:
      command = 'gcloud {} netapp volumes replications list'.format(
          self.ReleaseTrack().prefix
      )
      log.status.Print(
          'Check the status of the updated replication by listing all'
          ' replications:\n  $ {} '.format(command)
      )
    return result
