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
"""Create GKE-based virtual cluster command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from apitools.base.py import encoding

from googlecloudsdk.api_lib.dataproc import dataproc as dp
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.dataproc import clusters
from googlecloudsdk.command_lib.dataproc import flags
from googlecloudsdk.command_lib.dataproc import gke_clusters
from googlecloudsdk.command_lib.dataproc.gke_clusters import GkeNodePoolTargetsParser


@base.Hidden
@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Create(base.CreateCommand):
  """Create a GKE-based virtual cluster."""

  detailed_help = {
      'EXAMPLES':
          """\
          Create a Dataproc on GKE Cluster in us-central1 on a GKE cluster in
          the same project and region with default values:

            $ {command} my-cluster --region=us-central1 --gke-cluster=my-gke-cluster --image-version=spark-1.5.75

          Create a Dataproc on GKE Cluster in us-central1 on a GKE cluster in
          the same project and zone us-central1-f with default values:

            $ {command} my-cluster --region=us-central1 --gke-cluster=my-gke-cluster --gke-cluster-location=us-central1-f --image-version=spark-1.5.75

          Create a Dataproc on GKE Cluster in us-central1 with machine type
          'e2-standard-4', autoscaling 0-10 Nodes per zone.

            $ {command} my-cluster --region='us-central1' --gke-cluster='projects/my-project/locations/us-central1/clusters/my-gke-cluster' --image-version='spark-1.5.75' --pools='name=dp-default,roles=default,machineType=e2-standard-4,min=0,max=10'

          Create a Dataproc on GKE Cluster in us-central1 with two distinct
          NodePools.

            $ {command} my-cluster --region='us-central1' --gke-cluster='projects/my-project/locations/us-central1/clusters/my-gke-cluster' --image-version='spark-1.5.75' --pools='name=dp-default,roles=default,machineType=e2-standard-4' --pools='name=workers,roles=spark-drivers;spark-executors,machineType=n2-standard-8
          """
  }

  @classmethod
  def Args(cls, parser):
    dataproc = dp.Dataproc(cls.ReleaseTrack())
    base.ASYNC_FLAG.AddToParser(parser)
    flags.AddClusterResourceArg(parser, 'create', dataproc.api_version)

    # 30m is backend timeout + 5m for safety buffer.
    flags.AddTimeoutFlag(parser, default='35m')

    parser.add_argument(
        '--image-version',
        metavar='VERSION',
        required=True,
        help='The image version to use for the cluster.')

    parser.add_argument(
        '--staging-bucket',
        help="""\
        The Cloud Storage bucket to use by default to stage job
        dependencies, miscellaneous config files, and job driver console output
        when using this cluster.
        """)
    parser.add_argument(
        '--temp-bucket',
        help="""\
        The Cloud Storage bucket to use by default to store
        ephemeral cluster and jobs data, such as Spark and MapReduce history files.
        """)

    parser.add_argument(
        '--properties',
        type=arg_parsers.ArgDict(),
        action=arg_parsers.UpdateAction,
        default={},
        metavar='PREFIX:PROPERTY=VALUE',
        help="""\
        Specifies configuration properties for installed packages, such as
        Spark. Properties are mapped to configuration files by specifying a
        prefix, such as "core:io.serializations".
        """)

    flags.AddGkeClusterResourceArg(parser)
    parser.add_argument(
        '--namespace',
        help="""\
            The name of the Kubernetes namespace to deploy Dataproc system
            components in. This namespace does not need to exist.
            """)

    gke_clusters.AddPoolsArg(parser)

  def Run(self, args):
    dataproc = dp.Dataproc(self.ReleaseTrack())
    cluster_ref = args.CONCEPTS.cluster.Parse()
    gke_cluster_ref = args.CONCEPTS.gke_cluster.Parse()
    virtual_cluster_config = Create._GetVirtualClusterConfig(
        dataproc, gke_cluster_ref, args)
    cluster = dataproc.messages.Cluster(
        virtualClusterConfig=virtual_cluster_config,
        clusterName=cluster_ref.clusterName,
        projectId=cluster_ref.projectId)

    return clusters.CreateCluster(
        dataproc,
        cluster_ref,
        cluster,
        args.async_,
        args.timeout,
        # This refers to the old GKE beta.
        enable_create_on_gke=False,
        action_on_failed_primary_workers=None)

  @staticmethod
  def _GetVirtualClusterConfig(dataproc, gke_cluster_ref, args):
    """Get dataproc virtual cluster configuration for GKE based clusters.

    Args:
      dataproc: Dataproc object that contains client, messages, and resources
      gke_cluster_ref: GKE cluster reference.
      args: Arguments parsed from argparse.ArgParser.

    Returns:
      virtual_cluster_config: Dataproc virtual cluster configuration
    """

    software_config = dataproc.messages.SoftwareConfig(
        imageVersion=args.image_version)

    if args.properties:
      software_config.properties = encoding.DictToAdditionalPropertyMessage(
          args.properties,
          dataproc.messages.SoftwareConfig.PropertiesValue,
          sort_items=True)

    pools = GkeNodePoolTargetsParser.Parse(dataproc,
                                           gke_cluster_ref.RelativeName(),
                                           args.pools)

    gke_cluster_config = dataproc.messages.GkeClusterConfig(
        gkeClusterTarget=gke_cluster_ref.RelativeName(), nodePoolTarget=pools)

    kubernetes_cluster_config = dataproc.messages.KubernetesClusterConfig(
        kubernetesNamespace=args.namespace, gkeClusterConfig=gke_cluster_config)

    virtual_cluster_config = dataproc.messages.VirtualClusterConfig(
        stagingBucket=args.staging_bucket,
        tempBucket=args.temp_bucket,
        softwareConfig=software_config,
        kubernetesClusterConfig=kubernetes_cluster_config)

    return virtual_cluster_config
