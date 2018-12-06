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

"""This is a command for testing deprecation."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import log


@calliope_base.Deprecate(is_removed=False)
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.ALPHA)
class DeprecationWarningCommandSharedDescriptionAlpha(calliope_base.Command):
  """Test deprecation with shared description and release tracks."""

  def Run(self, args):
    log.status.Print('Deprecation with shared description command complete.')


@calliope_base.Deprecate(is_removed=False)
@calliope_base.ReleaseTracks(calliope_base.ReleaseTrack.GA)
class DeprecationWarningCommandSharedDescriptionGA(calliope_base.Command):
  """Test deprecation with shared description and release tracks."""

  def Run(self, args):
    log.status.Print('Deprecation with shared description command complete.')


_DESCRIPTION = {
    'DESCRIPTION': """\
        Test deprecation with shared description and release tracks.

        *{command}*  also contains a shared docstring to see if auto-genrated
        deprecation warnings across multiple --help commands in the same
        session accumulate.
        """
}

DeprecationWarningCommandSharedDescriptionAlpha.detailed_help = _DESCRIPTION
DeprecationWarningCommandSharedDescriptionGA.detailed_help = _DESCRIPTION
