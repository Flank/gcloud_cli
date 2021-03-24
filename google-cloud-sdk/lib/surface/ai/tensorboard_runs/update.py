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
"""Command to update a Tensorboard run in AI platform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.tensorboard_runs import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import errors
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import log


def _Run(args, version):
  """Update an existing AI Platform Tensorboard run."""
  tensorboard_run_ref = args.CONCEPTS.tensorboard_run.Parse()
  args.region = tensorboard_run_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=args.region):
    try:
      op = client.TensorboardRunsClient(version=version).Patch(
          tensorboard_run_ref, args)
    except errors.NoFieldsSpecifiedError:
      available_update_args = [
          'display_name',
          'update_labels',
          'clear_labels',
          'remove_labels',
          'description'
      ]
      if not any(args.IsSpecified(arg) for arg in available_update_args):
        raise
      log.status.Print('No update to perform.')
      return None
    else:
      log.UpdatedResource(op.name, kind='AI Platform Tensorboard run')
      return op


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Update(base.UpdateCommand):
  """Update an existing AI Platform Tensorboard run."""

  @staticmethod
  def Args(parser):
    flags.AddTensorboardRunResourceArg(parser, 'to update')
    flags.GetDisplayNameArg(
        'tensorboard run', required=False).AddToParser(parser)
    flags.GetDescriptionArg('tensorboard run').AddToParser(parser)
    labels_util.AddUpdateLabelsFlags(parser)

  def Run(self, args):
    return _Run(args, constants.ALPHA_VERSION)
