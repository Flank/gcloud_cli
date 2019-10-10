# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Describe autoscaling policy command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import flags


def _Run(dataproc, args):
  """Run command."""

  messages = dataproc.messages

  policy_ref = args.CONCEPTS.autoscaling_policy.Parse()

  request = messages.DataprocProjectsRegionsAutoscalingPoliciesGetRequest(
      name=policy_ref.RelativeName())
  return dataproc.client.projects_regions_autoscalingPolicies.Get(request)


@base.ReleaseTracks(base.ReleaseTrack.GA)
class Describe(base.DescribeCommand):
  """Describe an autoscaling policy.

  ## EXAMPLES

  The following command prints out the autoscaling policy
  `example-autoscaling-policy`:

    $ {command} example-autoscaling-policy
  """

  @staticmethod
  def Args(parser):
    flags.AddAutoscalingPolicyResourceArg(parser, 'describe', 'v1')

  def Run(self, args):
    return _Run(dp.Dataproc(self.ReleaseTrack()), args)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA, base.ReleaseTrack.BETA)
class DescribeBeta(base.DescribeCommand):
  """Describe an autoscaling policy.

  ## EXAMPLES

  The following command prints out the autoscaling policy
  `example-autoscaling-policy`:

    $ {command} example-autoscaling-policy
  """

  @staticmethod
  def Args(parser):
    flags.AddAutoscalingPolicyResourceArg(parser, 'describe', 'v1beta2')

  def Run(self, args):
    return _Run(dp.Dataproc(self.ReleaseTrack()), args)
