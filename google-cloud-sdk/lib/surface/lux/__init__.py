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
"""The super-group for the Lux CLI.

The fact that this is a directory with
an __init__.py in it makes it a command group. The methods written below will
all be called by calliope (though they are all optional).
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base

DETAILED_HELP = {
    'DESCRIPTION': """
        The gcloud lux command group lets you create and manage Google Cloud Lux
        databases.

        Lux is a fully-managed database service that makes it easy to set
        up, maintain, manage, and administer your Lux databases in
        the cloud.

        More information on Lux can be found here at go/luxdb
        """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Lux(base.Group):
  """Create and manage Lux databases."""

  category = base.DATABASES_CATEGORY

  detailed_help = DETAILED_HELP

  def Filter(self, context, args):
    del context, args
    base.DisableUserProjectQuota()
