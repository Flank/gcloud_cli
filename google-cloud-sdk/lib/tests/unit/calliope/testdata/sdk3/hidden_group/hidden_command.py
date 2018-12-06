# -*- coding: utf-8 -*- #
# Copyright 2015 Google Inc. All Rights Reserved.
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
"""Markdown test command with underscore in source name."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base


class HiddenCommand(calliope_base.Command):
  """Hidden command docstring index.

  Hidden docstring description.

    builtin-docstring-expand("{command}")
    builtin-docstring-literal("{{command}}")
    detailed-docstring-expand("{nested}")
    detailed-docstring-literal("{{nested}}")
  """

  detailed_help = {
      'DESCRIPTION': '{description}',
      'nested': "nested-expand('{command}')` or nested-literal('{{command}}')",
  }

  @staticmethod
  def Args(parser):
    """Sets args for the command group."""
    pass

  def Run(self, unused_args):
    return 'Hidden_command.Run'
