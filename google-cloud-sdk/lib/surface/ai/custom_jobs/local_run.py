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
"""Command to run a training application locally."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.ai import flags


# TODO(b/176214485): Keep this hidden until public preview
@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Run a custom training locally.

  Packages your training code into a Docker image and executes it locally.
  """
  detailed_help = {
      'DESCRIPTION':
          '{description}',
      'EXAMPLES':
          """\
          To execute an python module with required dependencies, run:

            $ {command} --python-module=my_training.task --base-image=gcr.io/my/image --requirements=pandas,scipy>=1.3.0

          To execute a python script using local GPU, run:

            $ {command} --script=my_training/task.py --base-image=gcr.io/my/image --gpu

          To execute an arbitrary script with custom arguments, run:

            $ {command} --script=my_run.sh --base-image=gcr.io/my/image -- --my-arg bar --enable_foo
          """,
  }

  @staticmethod
  def Args(parser):
    flags.AddLocalRunCustomJobFlags(parser)

  def Run(self, args):
    # TODO(b/177787597): implementation
    pass
