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
"""AI Platform Tensorboard time series create command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding
from googlecloudsdk.api_lib.ai.tensorboard_time_series import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags
from googlecloudsdk.command_lib.ai import tensorboards_util
from googlecloudsdk.command_lib.ai import validation
from googlecloudsdk.core import log


def _Run(args, version):
  """Create a new AI Platform Tensorboard time series."""
  validation.ValidateDisplayName(args.display_name)

  tensorboard_run_ref = args.CONCEPTS.tensorboard_run.Parse()
  region = tensorboard_run_ref.AsDict()['locationsId']
  with endpoint_util.AiplatformEndpointOverrides(version, region=region):
    tensorboard_runs_client = client.TensorboardTimeSeriesClient(
        version=version)
    response = tensorboard_runs_client.Create(tensorboard_run_ref, args)
    response_msg = encoding.MessageToPyValue(response)
    if 'name' in response_msg:
      log.status.Print(
          ('Created AI Platform Tensorboard time series: {}.').format(
              response_msg['name']))
    return response


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a new AI Platform Tensorboard time series."""

  @staticmethod
  def Args(parser):
    flags.AddTensorboardRunResourceArg(parser,
                                       'to create a Tensorboard time series')
    flags.GetDisplayNameArg(
        'tensorboard-time-series', required=True).AddToParser(parser)
    flags.GetDescriptionArg('tensorboard-time-series').AddToParser(parser)
    tensorboards_util.GetTensorboardTimeSeriesTypeArg(
        'tensorboard-time-series').choice_arg.AddToParser(parser)
    flags.GetPluginNameArg('tensorboard-time-series').AddToParser(parser)
    flags.GetPluginDataArg('tensorboard-time-series').AddToParser(parser)

  def Run(self, args):
    return _Run(args, constants.ALPHA_VERSION)
