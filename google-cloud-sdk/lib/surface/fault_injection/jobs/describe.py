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
"""Describe Command for Job."""
from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.fault_injection import jobs
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.fault_injection import flags


_DETAILED_HELP = {
    'DESCRIPTION': '{description}',
    'EXAMPLES': """ \
        To describe a job with the id `my-job`, run:

          $ {command} my-job
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Describe(base.DescribeCommand):
  """Describe job."""

  detailed_help = _DETAILED_HELP

  @staticmethod
  def Args(parser):
    flags.AddDescribeJobFlags(parser)

  def Run(self, args):
    """Run the describe command."""
    client = jobs.JobsClient()
    job_ref = args.CONCEPTS.job.Parse()
    if not job_ref.Name():
      raise exceptions.InvalidArgumentException(
          'job', 'job id must be non-empty.'
      )
    return client.Describe(job=job_ref.RelativeName())
