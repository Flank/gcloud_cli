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
"""Command to get credentials of a GKE cluster on Azure."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.container import util
from googlecloudsdk.api_lib.container.azure import util as azure_api_util
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.container.azure import resource_args
from googlecloudsdk.command_lib.container.gkemulticloud import endpoint_util
from googlecloudsdk.command_lib.container.gkemulticloud import flags
from googlecloudsdk.command_lib.container.gkemulticloud import kubeconfig

import six


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class GetCredentials(base.Command):
  """Get credentials of a GKE cluster on Azure."""

  detailed_help = {
      'EXAMPLES': kubeconfig.COMMAND_EXAMPLE,
      'DESCRIPTION': kubeconfig.COMMAND_DESCRIPTION.format(kind='Azure'),
  }

  @staticmethod
  def Args(parser):
    resource_args.AddAzureClusterResourceArg(parser, 'to get credentials')
    flags.AddAuthProviderCmdPath(parser)

  def Run(self, args):
    """Runs the get-credentials command."""
    util.CheckKubectlInstalled()

    with endpoint_util.GkemulticloudEndpointOverride(
        resource_args.ParseAzureClusterResourceArg(args).locationsId,
        self.ReleaseTrack()):
      cluster_ref = resource_args.ParseAzureClusterResourceArg(args)
      client = azure_api_util.ClustersClient(track=self.ReleaseTrack())
      resp = client.Get(cluster_ref)
      context = kubeconfig.GenerateContext(
          'azure',
          cluster_ref.projectsId,
          cluster_ref.locationsId,
          cluster_ref.azureClustersId)
      cmd_args = kubeconfig.GenerateAuthProviderCmdArgs(
          six.text_type(self.ReleaseTrack()).lower(),
          'azure',
          cluster_ref.azureClustersId,
          cluster_ref.locationsId)
      kubeconfig.GenerateKubeconfig(
          resp,
          context,
          args.auth_provider_cmd_path,
          cmd_args)
