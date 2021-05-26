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
"""'vmware privateclouds create' command."""


from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals


from googlecloudsdk.api_lib.vmware.privateclouds import PrivateCloudsClient
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.command_lib.vmware import flags
from googlecloudsdk.core import log

DETAILED_HELP = {
    'DESCRIPTION':
        """
          Create a VMware Engine private cloud.
        """,
    'EXAMPLES':
        """
          To create a private cloud called ``my-privatecloud'' in project
          ``my-project'' with zone ``us-west2-a'', cluster id ``cluster-for-account-department''
          node type ``standard-72'' node count ``3'' cpu cores per node ``36'' in vpc network ``default-vpc''
          , run:

            $ {command} my-privatecloud --location=us-west2-a
                                        --project=my-project
                                        --cluster=cluster-for-account-department
                                        --node-type=standard-72
                                        --node-count=3
                                        --node-custom-virtual-cpu-count=36
                                        --network-cidr=192.168.0.0/20
                                        --network=default-vpc
                                        --network-project=network-project
    """,
}


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a VMware Engine private cloud."""

  @staticmethod
  def Args(parser):
    """Register flags for this command."""
    flags.AddPrivatecloudArgToParser(parser, positional=True)
    flags.AddClusterArgToParser(parser, positional=False)
    flags.AddNodeTypeArgToParser(parser)
    parser.add_argument(
        '--description',
        help="""\
        Text describing the private cloud
        """)
    parser.add_argument(
        '--node-count',
        required=True,
        type=int,
        help="""\
        Nodes count for management cluster
        """)
    parser.add_argument(
        '--network-cidr',
        required=True,
        help="""\
        Management subnet CIDR
        For example, `--network-cidr=192.0.1.1/29`.
        """)
    parser.add_argument(
        '--network',
        required=True,
        help="""\
        VPC network
        """)
    parser.add_argument(
        '--network-project',
        required=False,
        help="""\
        VPC network project
        """)
    labels_util.AddCreateLabelsFlags(parser)

  def Run(self, args):
    privatecloud = args.CONCEPTS.privatecloud.Parse()
    client = PrivateCloudsClient()
    operation = client.Create(privatecloud, args.labels, args.description,
                              args.cluster, args.node_type, args.node_count,
                              args.network_cidr, args.network,
                              args.network_project)
    log.CreatedResource(operation.name, kind='private cloud', is_async=True)

Create.detailed_help = DETAILED_HELP
