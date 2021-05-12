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
"""Command to create Transfer jobs."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


class Create(base.Command):
  """Create a Transfer Service transfer job."""

  detailed_help = {
      'DESCRIPTION':
          """\
      Creates a Transfer Service transfer job, allowing you to transfer data to
      Google Cloud Storage on a one-time or recurring basis.
      """,
      'EXAMPLES':
          '$ {command}',
  }

  @staticmethod
  def Args(parser):
    pass

  def Run(self, args):
    raise NotImplementedError
