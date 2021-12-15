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
"""Bare Metal Solution volumes update command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.bms.bms_client import BmsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.bms import exceptions
from googlecloudsdk.command_lib.bms import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Update a Bare Metal Solution volume.

          This call returns immediately, but the update operation may take
          several minutes to complete. To check if the operation is complete,
          use the `describe` command for the volume.
        """,
    'EXAMPLES':
        """
          To update a volume called ``my-volume'' in region ``us-central1'' with
          a new snapshot schedule policy ``my-policy'' and snapshot auto delete
          behavior ``oldest-first'', run:

          $ {command} my-volume --region=us-central1 --snapshot-schedule-policy=my-policy --snapshot-auto-delete=oldest-first
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.GA)
class Update(base.UpdateCommand):
  """Update a Bare Metal Solution volume."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddVolumeSnapshotAutoDeleteBehaviorArgToParser(parser)
    flags.AddVolumeArgToParser(parser, positional=True)

    ssp_group = parser.add_mutually_exclusive_group()
    flags.AddSnapshotSchedulePolicyArgToParser(parser, required=False,
                                               group=ssp_group)
    ssp_group.add_argument('--remove-snapshot-schedule-policy',
                           action='store_true',
                           help='Remove any existing snapshot schedule policy.')

  def Run(self, args):
    volume = args.CONCEPTS.volume.Parse()
    policy = args.CONCEPTS.snapshot_schedule_policy.Parse()
    client = BmsClient()

    if (not policy and not args.snapshot_auto_delete
        and not args.remove_snapshot_schedule_policy):
      raise exceptions.NoConfigurationChangeError(
          'No configuration change was requested. Did you mean to include the '
          'flags `--snapshot-schedule-policy`, '
          '`--remove-snapshot-schedule-policy`, or `--snapshot-auto-delete`?')

    op_ref = client.UpdateVolume(
        volume_resource=volume,
        snapshot_schedule_policy_resource=policy,
        remove_snapshot_schedule_policy=args.remove_snapshot_schedule_policy,
        snapshot_auto_delete=flags
        .VOLUME_SNAPSHOT_AUTO_DELETE_BEHAVIOR_MAPPER.GetEnumForChoice(
            args.snapshot_auto_delete))

    log.status.Print('Update request issued for: [{}]\nThis may take several '
                     'minutes to complete.'.format(volume.Name()))

    return op_ref


Update.detailed_help = DETAILED_HELP
