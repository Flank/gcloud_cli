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
"""The command to delete Config Management Feature."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base
from surface.container.hub.config_management import unmanage

MEMBERSHIP_FLAG = '--membership'


@base.Deprecate(
    is_removed=False,
    warning=('This command has been deprecated. '
             'Please use `unmanage` instead.'),
    error=('This command has been removed.'
           'Please use `unmanage` instead.'))
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Delete(unmanage.Unmanage):
  """Remove the Config Management Feature Spec for the given membership.

  Remove the Config Management Feature Spec for the given membership. The
  existing ConfigManagement resources in the clusters will become unmanaged.

  ## EXAMPLES

  To remove the Config Management Feature spec for a Membership, run:

    $ {command} --membership=CLUSTER_NAME
  """
  # Intentionally left blank; until removed is an alias for `unmanage`.
  pass
