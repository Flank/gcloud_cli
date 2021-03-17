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
"""Command to get a Tensorboard experiment in AI platform."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.ai.tensorboard_experiments import client
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import constants
from googlecloudsdk.command_lib.ai import endpoint_util
from googlecloudsdk.command_lib.ai import flags


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Get detailed Tensorboard experiment information about the given Tensorboard experiment id."""

  @staticmethod
  def Args(parser):
    flags.AddTensorboardExperimentResourceArg(parser, 'to describe')

  def _Run(self, args, version):
    tensorboard_exp_ref = args.CONCEPTS.tensorboard_experiment.Parse()
    region = tensorboard_exp_ref.AsDict()['locationsId']
    with endpoint_util.AiplatformEndpointOverrides(
        version=version, region=region):
      response = client.TensorboardExperimentsClient(version=version).Get(
          tensorboard_exp_ref)
      return response

  def Run(self, args):
    return self._Run(args, constants.ALPHA_VERSION)
