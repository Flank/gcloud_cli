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

"""The super-group for the IAM CLI."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import base


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Beyondcorp(base.Group):
  """Manage secure access to applications with integrated threat and data protection.

     BeyondCorp Enterprise offers a zero trust solution that enables
     secure access with integrated threat and data protection.The solution
     enables secure access to both Google Cloud Platform and on-prem hosted
     apps. For remote apps that are not deployed in Google Cloud Platform,
     BeyondCorp Enterprise's App connector provides simplified
     connectivity and app publishing experience. The BeyondCorp Enterprise
     client connector extends support to non-web applications by creating a
     secure connection to applications running in both Google Cloud and
     non-Google Cloud environments with full context and identity aware access.


     More information on Beyondcorp can be found here:
     https://cloud.google.com/beyondcorp
  """

  category = base.SECURITY_CATEGORY

  def Filter(self, context, args):
    base.DisableUserProjectQuota()
