# -*- coding: utf-8 -*- #
# Copyright 2016 Google LLC. All Rights Reserved.
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
"""Flags and helpers for the container related commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.api_lib.compute import constants as compute_constants
from googlecloudsdk.api_lib.container import api_adapter
from googlecloudsdk.api_lib.container import util
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import actions
from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.container import constants
from googlecloudsdk.core import log
from googlecloudsdk.core import properties

_DATAPATH_PROVIDER = {
    'legacy': 'Selects legacy datatpath for the cluster.',
    'advanced': 'Selects advanced datapath for the cluster.',
}

_DNS_PROVIDER = {
    'clouddns': 'Selects Cloud DNS as the DNS provider for the cluster.',
    'default': 'Selects the default DNS provider (kube-dns) for the cluster.',
}

_DNS_SCOPE = {
    'cluster': 'Configures the Cloud DNS zone to be private to the cluster.',
    'vpc': 'Configures the Cloud DNS zone to be private to the VPC Network.',
}


def AddBasicAuthFlags(parser):
  """Adds basic auth flags to the given parser.

  Basic auth flags are: --username, --enable-basic-auth, and --password.

  Args:
    parser: A given parser.
  """
  basic_auth_group = parser.add_group(help='Basic auth')
  username_group = basic_auth_group.add_group(
      mutex=True, help='Options to specify the username.')
  username_help_text = """\
The user name to use for basic auth for the cluster. Use `--password` to specify
a password; if not, the server will randomly generate one."""
  username_group.add_argument('--username', '-u', help=username_help_text)

  enable_basic_auth_help_text = """\
Enable basic (username/password) auth for the cluster.  `--enable-basic-auth` is
an alias for `--username=admin`; `--no-enable-basic-auth` is an alias for
`--username=""`. Use `--password` to specify a password; if not, the server will
randomly generate one. For cluster versions before 1.12, if neither
`--enable-basic-auth` nor `--username` is specified, `--enable-basic-auth` will
default to `true`. After 1.12, `--enable-basic-auth` will default to `false`."""
  username_group.add_argument(
      '--enable-basic-auth',
      help=enable_basic_auth_help_text,
      action='store_true',
      default=None)

  basic_auth_group.add_argument(
      '--password',
      help='The password to use for cluster auth. Defaults to a '
      'server-specified randomly-generated string.')


def MungeBasicAuthFlags(args):
  """Munges flags associated with basic auth.

  If --enable-basic-auth is specified, converts it --username value, and checks
  that --password is only specified if it makes sense.

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Raises:
    util.Error, if flags conflict.
  """
  if hasattr(args,
             'enable_basic_auth') and args.IsSpecified('enable_basic_auth'):
    if not args.enable_basic_auth:
      args.username = ''
    else:
      args.username = 'admin'
  if (hasattr(args, 'username') and
      hasattr(args, 'password')) and (not args.username and
                                      args.IsSpecified('password')):
    raise util.Error(constants.USERNAME_PASSWORD_ERROR_MSG)


# TODO(b/28318474): move flags common across commands here.
def AddImageTypeFlag(parser, target):
  """Adds a --image-type flag to the given parser."""
  help_text = """\
The image type to use for the {target}. Defaults to server-specified.

Image Type specifies the base OS that the nodes in the {target} will run on.
If an image type is specified, that will be assigned to the {target} and all
future upgrades will use the specified image type. If it is not specified the
server will pick the default image type.

The default image type and the list of valid image types are available
using the following command.

  $ gcloud container get-server-config
""".format(target=target)

  parser.add_argument('--image-type', help=help_text)


def AddImageFlag(parser, hidden=False):
  """Adds an --image flag to the given parser.

  Args:
    parser: A given parser.
    hidden: if true, suppress help text for this option
  """

  help_text = """\
A specific image to use on the new instances.
"""

  parser.add_argument('--image', help=help_text, hidden=hidden)


def AddImageProjectFlag(parser, hidden=False):
  """Adds an --image-project flag to the given parser.

  Args:
    parser: A given parser.
    hidden: if true, suppresses help text for this option.
  """
  help_text = """/
A specific project from which contains the os image or image family.  This is
required when using --image-type=CUSTOM.
"""

  parser.add_argument('--image-project', help=help_text, hidden=hidden)


def AddImageFamilyFlag(parser, hidden=False):
  """Adds an --image-family flag to the given parser.

  Args:
    parser: A given parser.
    hidden: if true, suppresses help text for this option.
  """

  help_text = """/
A specific image-family from which the most recent image is used on new
instances.  If both image and image family are specified, the image must be in
the image family, and the image is used.
"""
  parser.add_argument('--image-family', help=help_text, hidden=hidden)


def AddImageFlagsCreate(parser):
  AddImageTypeFlag(parser, 'cluster')
  AddImageFlag(parser, hidden=True)
  AddImageProjectFlag(parser, hidden=True)
  AddImageFamilyFlag(parser, hidden=True)


def AddNodeVersionFlag(parser, hidden=False):
  """Adds a --node-version flag to the given parser."""
  help_text = """\
The Kubernetes version to use for nodes. Defaults to server-specified.

The default Kubernetes version is available using the following command.

  $ gcloud container get-server-config
"""

  return parser.add_argument('--node-version', help=help_text, hidden=hidden)


def AddClusterVersionFlag(parser, suppressed=False, help=None):  # pylint: disable=redefined-builtin
  """Adds a --cluster-version flag to the given parser."""
  if help is None:
    help = """\
The Kubernetes version to use for the master and nodes. Defaults to
server-specified.

The default Kubernetes version is available using the following command.

  $ gcloud container get-server-config
"""

  return parser.add_argument('--cluster-version', help=help, hidden=suppressed)


def AddNotificationConfigFlag(parser, hidden=False):
  """Adds a --notification-config flag to the given parser."""

  help_text = """\
The notification configuration of the cluster. GKE supports publishing
cluster upgrade notifications to any Pub/Sub topic you created in the same
project. Create a subscription for the topic specified to receive notification
messages. See https://cloud.google.com/pubsub/docs/admin on how to manage
Pub/Sub topics and subscriptions. You can also use the filter option to
specify which event types you'd like to receive from the following options:
SecurityBulletinEvent, UpgradeEvent, UpgradeAvailableEvent.

Examples:

  $ {command} example-cluster --notification-config=pubsub=ENABLED,pubsub-topic=projects/{project}/topics/{topic-name}
  $ {command} example-cluster --notification-config=pubsub=ENABLED,pubsub-topic=projects/{project}/topics/{topic-name},filter="SecurityBulletinEvent|UpgradeEvent"

The project of the Pub/Sub topic must be the same one as the cluster. It can
be either the project ID or the project number.
"""
  return parser.add_argument(
      '--notification-config',
      type=arg_parsers.ArgDict(
          spec={
              'pubsub': str,
              'pubsub-topic': str,
              'filter': str,
          },
          required_keys=['pubsub']),
      metavar='pubsub=ENABLED|DISABLED,pubsub-topic=TOPIC',
      help=help_text,
      hidden=hidden)


def AddReleaseChannelFlag(parser, is_update=False, hidden=False):
  """Adds a --release-channel flag to the given parser."""
  short_text = """\
Release channel a cluster is subscribed to.

"""
  if is_update:
    short_text = """\
Subscribe or unsubscribe this cluster to a release channel.

"""
  help_text = short_text + """\
When a cluster is subscribed to a release channel, Google maintains
both the master version and the node version. Node auto-upgrade
defaults to true and cannot be disabled.
"""

  choices = {
      'rapid':
          """\
'rapid' channel is offered on an early access basis for customers who want
to test new releases.

WARNING: Versions available in the 'rapid' channel may be subject to
unresolved issues with no known workaround and are not subject to any
SLAs.
""",
      'regular':
          """\
Clusters subscribed to 'regular' receive versions that are considered GA
quality. 'regular' is intended for production users who want to take
advantage of new features.
""",
      'stable':
          """\
Clusters subscribed to 'stable' receive versions that are known to be
stable and reliable in production.
""",
      'None':
          """\
Use 'None' to opt-out of any release channel.
"""
  }

  return parser.add_argument(
      '--release-channel',
      metavar='CHANNEL',
      choices=choices,
      help=help_text,
      hidden=hidden)


def AddClusterAutoscalingFlags(parser, update_group=None, hidden=False):
  """Adds autoscaling related flags to parser.

  Autoscaling related flags are: --enable-autoscaling
  --min-nodes --max-nodes flags.

  Args:
    parser: A given parser.
    update_group: An optional group of mutually exclusive flag options to which
      an --enable-autoscaling flag is added.
    hidden: If true, suppress help text for added options.

  Returns:
    Argument group for autoscaling flags.
  """

  group = parser.add_argument_group('Cluster autoscaling')
  autoscaling_group = group if update_group is None else update_group
  autoscaling_group.add_argument(
      '--enable-autoscaling',
      default=None,
      help="""\
Enables autoscaling for a node pool.

Enables autoscaling in the node pool specified by --node-pool or
the default node pool if --node-pool is not provided.""",
      hidden=hidden,
      action='store_true')
  group.add_argument(
      '--max-nodes',
      help="""\
Maximum number of nodes per zone in the node pool.

Maximum number of nodes per zone to which the node pool specified by --node-pool
(or default node pool if unspecified) can scale. Ignored unless
--enable-autoscaling is also specified.""",
      hidden=hidden,
      type=int)
  group.add_argument(
      '--min-nodes',
      help="""\
Minimum number of nodes per zone in the node pool.

Minimum number of nodes per zone to which the node pool specified by --node-pool
(or default node pool if unspecified) can scale. Ignored unless
--enable-autoscaling is also specified.""",
      hidden=hidden,
      type=int)
  return group


def AddNodePoolAutoprovisioningFlag(parser, hidden=True):
  """Adds --enable-autoprovisioning flag for node pool to parser.

  Args:
    parser: A given parser.
    hidden: If true, suppress help text for added options.
  """
  parser.add_argument(
      '--enable-autoprovisioning',
      help="""\
Enables Cluster Autoscaler to treat the node pool as if it was autoprovisioned.

Cluster Autoscaler will be able to delete the node pool if it's unneeded.""",
      hidden=hidden,
      default=None,
      action='store_true')


def AddLocalSSDFlag(parser, suppressed=False, help_text=''):
  """Adds a --local-ssd-count flag to the given parser."""
  help_text += """\
The number of local SSD disks to provision on each node, formatted and mounted
in the filesystem.

Local SSDs have a fixed 375 GB capacity per device. The number of disks that
can be attached to an instance is limited by the maximum number of disks
available on a machine, which differs by compute zone. See
https://cloud.google.com/compute/docs/disks/local-ssd for more information."""
  parser.add_argument(
      '--local-ssd-count',
      help=help_text,
      hidden=suppressed,
      type=int,
      default=0)


def AddBootDiskKmsKeyFlag(parser, suppressed=False, help_text=''):
  """Adds a --boot-disk-kms-key flag to the given parser."""
  help_text += """\
The Customer Managed Encryption Key used to encrypt the boot disk attached
to each node in the node pool. This should be of the form
projects/[KEY_PROJECT_ID]/locations/[LOCATION]/keyRings/[RING_NAME]/cryptoKeys/[KEY_NAME].
For more information about protecting resources with Cloud KMS Keys please
see:
https://cloud.google.com/compute/docs/disks/customer-managed-encryption"""
  parser.add_argument(
      '--boot-disk-kms-key',
      help=help_text,
      hidden=suppressed,
      type=str,
      default='')


def AddAcceleratorArgs(parser,
                       enable_gpu_partition=False,
                       enable_gpu_time_sharing=False):
  """Adds Accelerator-related args."""

  spec = {
      'type': str,
      'count': int,
  }

  if enable_gpu_partition:
    spec['gpu-partition-size'] = str

  if enable_gpu_time_sharing:
    spec['max-time-shared-clients-per-gpu'] = int

  parser.add_argument(
      '--accelerator',
      type=arg_parsers.ArgDict(
          spec=spec, required_keys=['type'], max_length=len(spec)),
      metavar='type=TYPE,[count=COUNT]',
      help="""\
      Attaches accelerators (e.g. GPUs) to all nodes.

      *type*::: (Required) The specific type (e.g. nvidia-tesla-k80 for nVidia Tesla K80)
      of accelerator to attach to the instances. Use ```gcloud compute
      accelerator-types list``` to learn about all available accelerator types.

      *count*::: (Optional) The number of accelerators to attach to the
      instances. The default value is 1.
      """)


def AddAutoscalingProfilesFlag(parser, hidden=False):
  """Adds autoscaling profiles flag to parser.

  Autoscaling profiles flag is --autoscaling-profile.

  Args:
    parser: A given parser.
    hidden: If true, suppress help text for added options.
  """
  parser.add_argument(
      '--autoscaling-profile',
      required=False,
      default=None,
      help="""\
         Set autoscaling behaviour, choices are 'optimize-utilization' and 'balanced'.
         Default is 'balanced'.
      """,
      hidden=hidden,
      type=str)


def AddAutoprovisioningFlags(parser, hidden=False, for_create=False):
  """Adds node autoprovisioning related flags to parser.

  Autoprovisioning related flags are: --enable-autoprovisioning
  --min-cpu --max-cpu --min-memory --max-memory --autoprovisioning-image-type
  flags.

  Args:
    parser: A given parser.
    hidden: If true, suppress help text for added options.
    for_create: Add flags for create request.
  """

  group = parser.add_argument_group('Node autoprovisioning', hidden=hidden)
  group.add_argument(
      '--enable-autoprovisioning',
      required=True,
      default=None,
      help="""\
Enables  node autoprovisioning for a cluster.

Cluster Autoscaler will be able to create new node pools. Requires maximum CPU
and memory limits to be specified.""",
      hidden=hidden,
      action='store_true')

  limits_group = group.add_mutually_exclusive_group()
  limits_group.add_argument(
      '--autoprovisioning-config-file',
      type=arg_parsers.FileContents(),
      hidden=hidden,
      help="""\
Path of the JSON/YAML file which contains information about the
cluster's node autoprovisioning configuration. Currently it contains
a list of resource limits, identity defaults for autoprovisioning, node upgrade
settings, node management settings, minimum cpu platform, image type, node locations for
autoprovisioning, disk type and size configuration, Shielded instance settings,
and customer-managed encryption keys settings.

Resource limits are specified in the field 'resourceLimits'.
Each resource limits definition contains three fields:
resourceType, maximum and minimum.
Resource type can be "cpu", "memory" or an accelerator (e.g.
"nvidia-tesla-k80" for nVidia Tesla K80). Use gcloud compute accelerator-types
list to learn about available accelerator types.
Maximum is the maximum allowed amount with the unit of the resource.
Minimum is the minimum allowed amount with the unit of the resource.

Identity default contains at most one of the below fields:
serviceAccount: The Google Cloud Platform Service Account to be used by node VMs in
autoprovisioned node pools. If not specified, the project's default service account
is used.
scopes: A list of scopes to be used by node instances in autoprovisioned node pools.
Multiple scopes can be specified, separated by commas. For information on defaults,
look at:
https://cloud.google.com/sdk/gcloud/reference/container/clusters/create#--scopes

Node Upgrade settings are specified under the field
'upgradeSettings', which has the following fields:
maxSurgeUpgrade: Number of extra (surge) nodes to be created on
each upgrade of an autoprovisioned node pool.
maxUnavailableUpgrade: Number of nodes that can be unavailable at the
same time on each upgrade of an autoprovisioned node pool.

Node Management settings are specified under the field
'nodeManagement', which has the following fields:
enableAutoUpgrade: A boolean field that indicates if node
autoupgrade is enabled for autoprovisioned node pools.
enableAutoRepair: A boolean field that indicates if node
autorepair is enabled for autoprovisioned node pools.

minCpuPlatform: If specified, new autoprovisioned nodes will be
scheduled on host with specified CPU architecture or a newer one.
Note: Min CPU platform can only be specified in Beta and Alpha.

Autoprovisioned node image is specified under the 'imageType' field. If not specified
the default value will be applied.

Autoprovisioning locations is a set of zones where new node pools
can be created by Autoprovisioning. Autoprovisioning locations are
specified in the field 'autoprovisioningLocations'. All zones must
be in the same region as the cluster's master(s).

Disk type and size are specified under the 'diskType' and 'diskSizeGb' fields,
respectively. If specified, new autoprovisioned nodes will be created with
custom boot disks configured by these settings.

Shielded instance settings are specified under the 'shieldedInstanceConfig'
field, which has the following fields:
enableSecureBoot: A boolean field that indicates if secure boot is enabled for
autoprovisioned nodes.
enableIntegrityMonitoring: A boolean field that indicates if integrity
monitoring is enabled for autoprovisioned nodes.

Customer Managed Encryption Keys (CMEK) used by new auto-provisioned node pools
can be specified in the 'bootDiskKmsKey' field.
""")

  from_flags_group = limits_group.add_argument_group(
      'Flags to configure autoprovisioned nodes')
  from_flags_group.add_argument(
      '--max-cpu',
      required=for_create,
      help="""\
Maximum number of cores in the cluster.

Maximum number of cores to which the cluster can scale.""",
      hidden=hidden,
      type=int)
  from_flags_group.add_argument(
      '--min-cpu',
      help="""\
Minimum number of cores in the cluster.

Minimum number of cores to which the cluster can scale.""",
      hidden=hidden,
      type=int)
  from_flags_group.add_argument(
      '--max-memory',
      required=for_create,
      help="""\
Maximum memory in the cluster.

Maximum number of gigabytes of memory to which the cluster can scale.""",
      hidden=hidden,
      type=int)
  from_flags_group.add_argument(
      '--min-memory',
      help="""\
Minimum memory in the cluster.

Minimum number of gigabytes of memory to which the cluster can scale.""",
      hidden=hidden,
      type=int)
  from_flags_group.add_argument(
      '--autoprovisioning-image-type',
      help='Node Autoprovisioning will create new nodes with the specified image type',
      type=str)
  accelerator_group = from_flags_group.add_argument_group(
      'Arguments to set limits on accelerators:')
  accelerator_group.add_argument(
      '--max-accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'type': str,
              'count': int,
          },
          required_keys=['type', 'count'],
          max_length=2),
      required=True,
      metavar='type=TYPE,count=COUNT',
      hidden=hidden,
      help="""\
Sets maximum limit for a single type of accelerators (e.g. GPUs) in cluster.

*type*::: (Required) The specific type (e.g. nvidia-tesla-k80 for nVidia Tesla K80)
of accelerator for which the limit is set. Use ```gcloud compute
accelerator-types list``` to learn about all available accelerator types.

*count*::: (Required) The maximum number of accelerators
to which the cluster can be scaled.
""")
  accelerator_group.add_argument(
      '--min-accelerator',
      type=arg_parsers.ArgDict(
          spec={
              'type': str,
              'count': int,
          },
          required_keys=['type', 'count'],
          max_length=2),
      metavar='type=TYPE,count=COUNT',
      hidden=hidden,
      help="""\
Sets minimum limit for a single type of accelerators (e.g. GPUs) in cluster. Defaults
to 0 for all accelerator types if it isn't set.

*type*::: (Required) The specific type (e.g. nvidia-tesla-k80 for nVidia Tesla K80)
of accelerator for which the limit is set. Use ```gcloud compute
accelerator-types list``` to learn about all available accelerator types.

*count*::: (Required) The minimum number of accelerators
to which the cluster can be scaled.
""")
  identity_group = from_flags_group.add_argument_group(
      'Flags to specify identity for autoprovisioned nodes:')
  identity_group.add_argument(
      '--autoprovisioning-service-account',
      type=str,
      hidden=hidden,
      help="""\
The Google Cloud Platform Service Account to be used by node VMs in
autoprovisioned node pools. If not specified, the project default
service account is used.
""")
  identity_group.add_argument(
      '--autoprovisioning-scopes',
      type=arg_parsers.ArgList(),
      metavar='SCOPE',
      hidden=hidden,
      help="""\
The scopes be used by node instances in autoprovisioned node pools.
Multiple scopes can be specified, separated by commas. For information
on defaults, look at:
https://cloud.google.com/sdk/gcloud/reference/container/clusters/create#--scopes
""")
  upgrade_settings_group = from_flags_group.add_argument_group(
      'Flags to specify upgrade settings for autoprovisioned nodes:',
      hidden=hidden,
  )
  upgrade_settings_group.add_argument(
      '--autoprovisioning-max-surge-upgrade',
      type=int,
      hidden=hidden,
      required=True,
      help="""\
Number of extra (surge) nodes to be created on each upgrade of an
autoprovisioned node pool.
""")
  upgrade_settings_group.add_argument(
      '--autoprovisioning-max-unavailable-upgrade',
      type=int,
      hidden=hidden,
      required=True,
      help="""\
Number of nodes that can be unavailable at the same time on each
upgrade of an autoprovisioned node pool.
""")
  management_settings_group = from_flags_group.add_argument_group(
      'Flags to specify node management settings for autoprovisioned nodes:',
      hidden=hidden,
  )
  management_settings_group.add_argument(
      '--enable-autoprovisioning-autoupgrade',
      hidden=hidden,
      default=None,
      required=True,
      action='store_true',
      help="""\
Enable node autoupgrade for autoprovisioned node pools.
Use --no-enable-autoprovisioning-autoupgrade to disable.
""")
  management_settings_group.add_argument(
      '--enable-autoprovisioning-autorepair',
      default=None,
      action='store_true',
      hidden=hidden,
      required=True,
      help="""\
Enable node autorepair for autoprovisioned node pools.
Use --no-enable-autoprovisioning-autorepair to disable.
""")
  from_flags_group.add_argument(
      '--autoprovisioning-locations',
      hidden=hidden,
      help="""\
Set of zones where new node pools can be created by autoprovisioning.
All zones must be in the same region as the cluster's master(s).
Multiple locations can be specified, separated by commas.""",
      metavar='ZONE',
      type=arg_parsers.ArgList(min_length=1))
  from_flags_group.add_argument(
      '--autoprovisioning-min-cpu-platform',
      hidden=hidden,
      metavar='PLATFORM',
      help="""\
If specified, new autoprovisioned nodes will be scheduled on host with
specified CPU architecture or a newer one.
""")


def AddEnableBinAuthzFlag(parser, hidden=False):
  """Adds a --enable-binauthz flag to parser."""
  help_text = """Enable Binary Authorization for this cluster."""
  parser.add_argument(
      '--enable-binauthz',
      action='store_true',
      default=None,
      help=help_text,
      hidden=hidden,
  )


def AddZoneAndRegionFlags(parser):
  """Adds the --zone and --region flags to the parser."""
  # TODO(b/33343238): Remove the short form of the zone flag.
  # TODO(b/18105938): Add zone prompting
  group = parser.add_mutually_exclusive_group()
  group.add_argument(
      '--zone',
      '-z',
      help='Compute zone (e.g. us-central1-a) for the cluster',
      action=actions.StoreProperty(properties.VALUES.compute.zone))
  group.add_argument(
      '--region', help='Compute region (e.g. us-central1) for the cluster.')


def AddAsyncFlag(parser):
  """Adds the --async flags to the given parser."""
  base.ASYNC_FLAG.AddToParser(parser)


def AddEnableKubernetesAlphaFlag(parser):
  """Adds a --enable-kubernetes-alpha flag to parser."""
  help_text = """\
Enable Kubernetes alpha features on this cluster. Selecting this
option will result in the cluster having all Kubernetes alpha API groups and
features turned on. Cluster upgrades (both manual and automatic) will be
disabled and the cluster will be automatically deleted after 30 days.

Alpha clusters are not covered by the Kubernetes Engine SLA and should not be
used for production workloads."""
  parser.add_argument(
      '--enable-kubernetes-alpha', action='store_true', help=help_text)


def _AddLegacyCloudRunFlag(parser, flag, **kwargs):
  """Adds a flag with the new and old product name for KubeRun."""
  new_kwargs = kwargs.copy()
  new_kwargs['hidden'] = True
  parser.add_argument(flag.format('kuberun'), **new_kwargs)
  parser.add_argument(flag.format('cloud-run'), **kwargs)


def AddEnableCloudRunAlphaFlag(parser):
  """Adds the --enable-cloud-run-alpha flags to parser."""
  help_text = """\
Enable Cloud Run alpha features on this cluster. Selecting this
option will result in the cluster having all Cloud Run alpha API groups and
features turned on.

Cloud Run alpha clusters are not covered by the Cloud Run SLA and should not be
used for production workloads."""
  _AddLegacyCloudRunFlag(
      parser, '--enable-{0}-alpha', action='store_true', help=help_text)


def AddCloudRunConfigFlag(parser, suppressed=False):
  """Adds a --cloud-run-config flag to parser."""
  help_text = """\
Configurations for Cloud Run addon, requires `--addons=CloudRun` for create
and `--update-addons=CloudRun=ENABLED` for update.

*load-balancer-type*::: (Optional) Type of load-balancer-type EXTERNAL or
INTERNAL.

Examples:

  $ {command} example-cluster --cloud-run-config=load-balancer-type=INTERNAL
"""
  _AddLegacyCloudRunFlag(
      parser,
      '--{0}-config',
      metavar='load-balancer-type=EXTERNAL',
      type=arg_parsers.ArgDict(spec={
          'load-balancer-type': (lambda x: x.upper()),
      }),
      help=help_text,
      hidden=suppressed)


def GetLegacyCloudRunFlag(flag, args, get_default):
  """Gets the value for a flag that supports cloud_run and kuberun."""
  oldflag = flag.format('cloud_run')
  newflag = flag.format('kuberun')
  specified = args.GetSpecifiedArgNames()
  oldarg = '--' + oldflag.replace('_', '-')
  newarg = '--' + newflag.replace('_', '-')
  if oldarg in specified and newarg in specified:
    log.warning('{} and {} are both specified, ignoring the latter.'.format(
        newarg, oldarg))
  return get_default(oldflag) or get_default(newflag)


def ValidateCloudRunConfigCreateArgs(cloud_run_config_args, addons_args):
  """Validates flags specifying Cloud Run config for create.

  Args:
    cloud_run_config_args: parsed commandline arguments for --cloud-run-config.
    addons_args: parsed commandline arguments for --addons.

  Raises:
    InvalidArgumentException: when load-balancer-type is not EXTERNAL nor
    INTERNAL,
    or --addons=CloudRun is not specified
  """
  if cloud_run_config_args:
    load_balancer_type = cloud_run_config_args.get('load-balancer-type', '')
    if load_balancer_type not in ['EXTERNAL', 'INTERNAL']:
      raise exceptions.InvalidArgumentException(
          '--kuberun-config',
          'load-balancer-type is either EXTERNAL or INTERNAL'
          'e.g. --kuberun-config load-balancer-type=EXTERNAL')
    if all((v not in addons_args) for v in api_adapter.CLOUDRUN_ADDONS):
      raise exceptions.InvalidArgumentException(
          '--kuberun-config', '--addon=KubeRun must be specified when '
          '--kuberun-config is given')


def ValidateCloudRunConfigUpdateArgs(cloud_run_config_args, update_addons_args):
  """Validates flags specifying Cloud Run config for update.

  Args:
    cloud_run_config_args: parsed comandline arguments for --cloud_run_config.
    update_addons_args: parsed comandline arguments for --update-addons.

  Raises:
    InvalidArgumentException: when load-balancer-type is not MTLS_PERMISSIVE nor
    MTLS_STRICT,
    or --update-addons=CloudRun=ENABLED is not specified
  """
  if cloud_run_config_args:
    load_balancer_type = cloud_run_config_args.get('load-balancer-type', '')
    if load_balancer_type not in ['EXTERNAL', 'INTERNAL']:
      raise exceptions.InvalidArgumentException(
          '--kuberun-config', 'load-balancer-type must be one of EXTERNAL or '
          'INTERNAL e.g. --kuberun-config load-balancer-type=EXTERNAL')
    if any([(update_addons_args.get(v) or False)
            for v in api_adapter.CLOUDRUN_ADDONS]):
      raise exceptions.InvalidArgumentException(
          '--kuberun-config',
          '--update-addons=KubeRun=ENABLED must be specified '
          'when --kuberun-config is given')


def AddEnableStackdriverKubernetesFlag(parser):
  """Adds a --enable-stackdriver-kubernetes flag to parser."""
  help_text = """Enable Cloud Operations for GKE."""
  parser.add_argument(
      '--enable-stackdriver-kubernetes',
      action=actions.DeprecationAction(
          '--enable-stackdriver-kubernetes',
          warn='The `--enable-stackdriver-kubernetes` flag is deprecated and '
          'will be removed in an upcoming release. '
          'Please use `--logging` and `--monitoring` instead. '
          'For more information, please read: '
          'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.',
          action='store_true'),
      default=None,
      help=help_text)


def AddEnableLoggingMonitoringSystemOnlyFlag(parser):
  """Adds a --enable-stackdriver-kubernetes-system flag to parser."""
  help_text = """Enable Cloud Operations system-only monitoring and logging."""
  parser.add_argument(
      '--enable-logging-monitoring-system-only',
      action=actions.DeprecationAction(
          '--enable-logging-monitoring-system-only',
          warn='The `--enable-logging-monitoring-system-only` flag is '
          'deprecated and will be removed in an upcoming release. '
          'Please use `--logging` and `--monitoring` instead. '
          'For more information, please read: '
          'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.',
          action='store_true'),
      help=help_text)


def AddEnableWorkloadMonitoringEapFlag(parser):
  """Adds a --enable-workload-monitoring-eap flag to parser."""
  help_text = """Enable workload monitoring (EAP)."""
  parser.add_argument(
      '--enable-workload-monitoring-eap',
      action='store_true',
      default=None,
      help=help_text,
      hidden=True,
  )


def AddManagedPrometheusFlags(parser, for_create=False):
  """Adds --enable-managed-prometheus and --disable-managed-prometheus flags to parser."""
  enable_help_text = """Enable managed collection for Managed Service for
  Prometheus."""
  disable_help_text = """Disable managed collection for Managed Service for
  Prometheus."""

  # Create can only enable the component.
  if for_create:
    parser.add_argument(
        '--enable-managed-prometheus',
        action='store_true',
        default=None,
        help=enable_help_text,
    )
  else:
    group = parser.add_group(mutex=True)
    group.add_argument(
        '--enable-managed-prometheus',
        action='store_true',
        default=None,
        help=enable_help_text,
    )
    group.add_argument(
        '--disable-managed-prometheus',
        action='store_true',
        default=None,
        help=disable_help_text,
    )


def AddEnableMasterSignalsFlags(parser, for_create=False):
  """Adds --master-logs and --enable-master-metrics flags to parser."""

  help_text = """\
Set which master components logs should be sent to Cloud Operations.

Examples:

  $ {command} --master-logs APISERVER,SCHEDULER
"""
  if for_create:
    group = parser.add_group(hidden=True)
  else:
    group = parser.add_mutually_exclusive_group(hidden=True)

  group.add_argument(
      '--master-logs',
      type=arg_parsers.ArgList(choices=api_adapter.PRIMARY_LOGS_OPTIONS),
      help=help_text,
      metavar='COMPONENT',
      action=actions.DeprecationAction(
          '--master-logs',
          warn='The `--master-logs` flag is deprecated and will be removed in '
          'an upcoming release. Please use `--logging` instead. '
          'For more information, please read: '
          'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.'
      ),
  )

  if not for_create:
    help_text = """\
Disable sending logs from master components to Cloud Operations.
"""
    group.add_argument(
        '--no-master-logs',
        action=actions.DeprecationAction(
            '--no-master-logs',
            warn='The `--no-master-logs` flag is deprecated and will be removed'
            ' in an upcoming release. Please use `--logging` instead. '
            'For more information, please read: '
            'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.',
            action='store_true'),
        default=False,
        help=help_text,
    )

  help_text = """\
Enable sending metrics from master components to Cloud Operations.
"""
  group.add_argument(
      '--enable-master-metrics',
      action=actions.DeprecationAction(
          '--enable-master-metrics',
          warn='The `--enable-master-metrics` flag is deprecated and will be '
          'removed in an upcoming release. Please use `--monitoring` instead. '
          'For more information, please read: '
          'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.',
          action='store_true'),
      default=None,
      help=help_text,
  )


def AddLoggingFlag(parser, autopilot=False):
  """Adds a --logging flag to parser."""
  if autopilot:
    parser.add_argument(
        '--logging',
        type=arg_parsers.ArgList(),
        default=None,
        help='Set the components that have logging enabled.',
        hidden=True,
        metavar='COMPONENT',
        action=actions.DeprecationAction(
            '--logging',
            warn='The `--logging` flag is deprecated for `create-auto` and will'
            ' be removed in an upcoming release. For now, only the default '
            'value "SYSTEM,WORKLOAD" is supported.'),
    )
    return

  help_text = """\
Set the components that have logging enabled. Valid component values are:
`SYSTEM`, `WORKLOAD`, `NONE`

For more information, look at
https://cloud.google.com/stackdriver/docs/solutions/gke/installing#available-logs

Examples:

  $ {command} --logging=SYSTEM
  $ {command} --logging=SYSTEM,WORKLOAD
  $ {command} --logging=NONE
"""
  parser.add_argument(
      '--logging',
      type=arg_parsers.ArgList(),
      default=None,
      help=help_text,
      metavar='COMPONENT',
  )


def AddMonitoringFlag(parser, autopilot=False):
  """Adds a --monitoring flag to parser."""
  if autopilot:
    parser.add_argument(
        '--monitoring',
        type=arg_parsers.ArgList(),
        default=None,
        help='Set the components that have monitoring enabled.',
        hidden=True,
        metavar='COMPONENT',
        action=actions.DeprecationAction(
            '--monitoring',
            warn='The `--monitoring` flag is deprecated for `create-auto` and '
            'will be removed in an upcoming release. For now, only the default '
            'value "SYSTEM" is supported.'),
    )
    return

  help_text = """\
Set the components that have monitoring enabled. Valid component values are:
`SYSTEM`, `WORKLOAD` (Deprecated), `NONE`

For more information, look at
https://cloud.google.com/stackdriver/docs/solutions/gke/installing#available-metrics

Examples:

  $ {command} --monitoring=SYSTEM
  $ {command} --monitoring=NONE
"""
  parser.add_argument(
      '--monitoring',
      type=arg_parsers.ArgList(),
      default=None,
      help=help_text,
      metavar='COMPONENT',
  )


def AddNodeLabelsFlag(parser,
                      for_node_pool=False,
                      for_update=False,
                      hidden=False):
  """Adds a --node-labels flag to the given parser."""
  if for_node_pool:
    if for_update:
      help_text = """\
Replaces all the user specified Kubernetes labels on all nodes in an existing
node pool with the given labels.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --node-labels=label1=value1,label2=value2
"""
    else:
      help_text = """\
Applies the given Kubernetes labels on all nodes in the new node pool.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --node-labels=label1=value1,label2=value2
"""
  else:
    help_text = """\
Applies the given Kubernetes labels on all nodes in the new node pool.

Examples:

  $ {command} example-cluster --node-labels=label-a=value1,label-2=value2
"""
  help_text += """
New nodes, including ones created by resize or recreate, will have these labels
on the Kubernetes API node object and can be used in nodeSelectors.
See [](http://kubernetes.io/docs/user-guide/node-selection/) for examples.

Note that Kubernetes labels, intended to associate cluster components
and resources with one another and manage resource lifecycles, are different
from Google Kubernetes Engine labels that are used for the purpose of tracking
billing and usage information."""

  parser.add_argument(
      '--node-labels',
      metavar='NODE_LABEL',
      type=arg_parsers.ArgDict(),
      help=help_text,
      hidden=hidden)


def AddLocalSSDsAlphaFlags(parser, for_node_pool=False, suppressed=False):
  """Adds the --local-ssd-count and --local-ssd-volumes flags to the parser."""
  local_ssd_relationship = """\
--local-ssd-count is the equivalent of using --local-ssd-volumes with type=scsi,format=fs\n
"""
  group = parser.add_mutually_exclusive_group()
  AddLocalSSDVolumeConfigsFlag(group, for_node_pool=for_node_pool)
  AddEphemeralStorageFlag(group, for_node_pool=for_node_pool, hidden=suppressed)
  AddLocalSSDFlag(
      group, suppressed=suppressed, help_text=local_ssd_relationship)


def AddLocalSSDsBetaFlags(parser, for_node_pool=False, suppressed=False):
  """Adds the --local-ssd-count flag to the parser."""
  group = parser.add_mutually_exclusive_group()
  AddLocalSSDFlag(group, suppressed=suppressed)
  AddEphemeralStorageFlag(group, for_node_pool=for_node_pool, hidden=suppressed)


def AddLocalSSDVolumeConfigsFlag(parser, for_node_pool=False, help_text=''):
  """Adds a --local-ssd-volumes flag to the given parser."""
  help_text += """\
Adds the requested local SSDs on all nodes in default node pool(s) in new cluster.

Examples:

  $ {{command}} {0} --local-ssd-volumes count=2,type=nvme,format=fs

'count' must be between 1-8\n
'type' must be either scsi or nvme\n
'format' must be either fs or block

New nodes, including ones created by resize or recreate, will have these local SSDs.

Local SSDs have a fixed 375 GB capacity per device. The number of disks that
can be attached to an instance is limited by the maximum number of disks
available on a machine, which differs by compute zone. See
https://cloud.google.com/compute/docs/disks/local-ssd for more information.
""".format('node-pool-1 --cluster=example-cluster'
           if for_node_pool else 'example_cluster')
  count_validator = arg_parsers.RegexpValidator(
      r'^[1-8]$', 'Count must be a number between 1 and 8')
  type_validator = arg_parsers.RegexpValidator(
      r'^(scsi|nvme)$', 'Type must be either "scsi" or "nvme"')
  format_validator = arg_parsers.RegexpValidator(
      r'^(fs|block)$', 'Format must be either "fs" or "block"')
  parser.add_argument(
      '--local-ssd-volumes',
      metavar='[count=COUNT],[type=TYPE],[format=FORMAT]',
      type=arg_parsers.ArgDict(
          spec={
              'count': count_validator,
              'type': type_validator,
              'format': format_validator,
          },
          required_keys=['count', 'type', 'format'],
          max_length=3),
      action='append',
      help=help_text)


def AddEphemeralStorageFlag(parser,
                            hidden=False,
                            for_node_pool=False,
                            help_text=''):
  """Adds --ephemeral-storage flag to the parser."""
  help_text += """\
Parameters for the ephemeral storage filesystem.
If unspecified, ephemeral storage is backed by the boot disk.

Examples:

  $ {{command}} {0} --ephemeral-storage local-ssd-count=2

'local-ssd-count' specifies the number of local SSDs to use to back ephemeral
storage. Local SDDs use NVMe interfaces and each is 375 GB in size.
If 'local-ssd-count=0', it means to disable using local SSDs as ephemeral storage.

See https://cloud.google.com/compute/docs/disks/local-ssd for more information.
""".format('node-pool-1 --cluster=example cluster'
           if for_node_pool else 'example_cluster')
  parser.add_argument(
      '--ephemeral-storage',
      help=help_text,
      hidden=hidden,
      type=arg_parsers.ArgDict(
          spec={'local-ssd-count': int}, required_keys=['local-ssd-count']),
  )


def AddNodeTaintsFlag(parser,
                      for_node_pool=False,
                      for_update=False,
                      hidden=False):
  """Adds a --node-taints flag to the given parser."""
  if for_node_pool:
    if for_update:
      help_text = """\
Replaces all the user specified Kubernetes taints on all nodes in an existing
node pool, which can be used with tolerations for pod scheduling.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --node-taints=key1=val1:NoSchedule,key2=val2:PreferNoSchedule
"""
    else:
      help_text = """\
Applies the given kubernetes taints on all nodes in the new node pool, which can
be used with tolerations for pod scheduling.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --node-taints=key1=val1:NoSchedule,key2=val2:PreferNoSchedule
"""
  else:
    help_text = """\
Applies the given kubernetes taints on all nodes in default node pool(s) in new
cluster, which can be used with tolerations for pod scheduling.

Examples:

  $ {command} example-cluster --node-taints=key1=val1:NoSchedule,key2=val2:PreferNoSchedule
"""
  help_text += """
To read more about node-taints, see https://cloud.google.com/kubernetes-engine/docs/node-taints.
"""

  parser.add_argument(
      '--node-taints',
      metavar='NODE_TAINT',
      type=arg_parsers.ArgDict(),
      help=help_text,
      hidden=hidden)


def AddPreemptibleFlag(parser, for_node_pool=False, suppressed=False):
  """Adds a --preemptible flag to parser."""
  if for_node_pool:
    help_text = """\
Create nodes using preemptible VM instances in the new node pool.

  $ {command} node-pool-1 --cluster=example-cluster --preemptible
"""
  else:
    help_text = """\
Create nodes using preemptible VM instances in the new cluster.

  $ {command} example-cluster --preemptible
"""
  help_text += """
New nodes, including ones created by resize or recreate, will use preemptible
VM instances. See https://cloud.google.com/kubernetes-engine/docs/preemptible-vm
for more information on how to use Preemptible VMs with Kubernetes Engine."""

  parser.add_argument(
      '--preemptible', action='store_true', help=help_text, hidden=suppressed)


def AddSpotFlag(parser, for_node_pool=False, hidden=False):
  """Adds a --spot flag to parser."""
  if for_node_pool:
    help_text = """\
Create nodes using spot VM instances in the new node pool.

  $ {command} node-pool-1 --cluster=example-cluster --spot
"""
  else:
    help_text = """\
Create nodes using spot VM instances in the new cluster.

  $ {command} example-cluster --spot
"""
  help_text += """
New nodes, including ones created by resize or recreate, will use spot
VM instances."""

  parser.add_argument(
      '--spot', action='store_true', help=help_text, hidden=hidden)


def AddPlacementTypeFlag(parser, for_node_pool=False, hidden=False):
  """Adds a --placement-type flag to parser."""
  if for_node_pool:
    help_text = textwrap.dedent("""\
      Placement type allows to define the type of node placement within this node
      pool.

      `UNSPECIFIED` - No requirements on the placement of nodes. This is the
      default option.

      `COMPACT` - Google will attempt to place the nodes in a close proximity to each
      other. This helps to reduce the communication latency between the nodes, but
      imposes additional limitations on the node pool size.

        $ {command} node-pool-1 --cluster=example-cluster --placement-type=COMPACT
      """)
  else:
    help_text = textwrap.dedent("""\
      Placement type allows to define the type of node placement within the default
      node pool of this cluster.

      `UNSPECIFIED` - No requirements on the placement of nodes. This is the
      default option.

      `COMPACT` - Google will attempt to place the nodes in a close proximity to each
      other. This helps to reduce the communication latency between the nodes, but
      imposes additional limitations on the node pool size.

        $ {command} example-cluster --placement-type=COMPACT
      """)

  parser.add_argument(
      '--placement-type',
      choices=api_adapter.PLACEMENT_OPTIONS,
      help=help_text,
      hidden=hidden)


def AddMaintenanceIntervalFlag(parser, for_node_pool=False, hidden=True):
  """Adds a --maintenance-interval flag to the given parser."""
  type_validator = arg_parsers.RegexpValidator(
      r'^(PERIODIC|AS_NEEDED)$', 'Type must be either"PERIODIC" or "AS_NEEDED"')
  if for_node_pool:
    help_text = """\
Specify the frequency of planned maintenance events in the new nodepool

Examples:

  $ {command} node-pool-1 example-cluster --maintenance-interval=PERIODIC

The maintenance interval type must be either 'PERIODIC' or 'AS_NEEDED'
"""
  else:
    help_text = """\
Specify the frequency of planned maintenance events in the new cluster

Examples:

  $ {command} example-cluster --maintenance-interval=PERIODIC

The maintenance interval type must be either 'PERIODIC' or 'AS_NEEDED'
"""
  parser.add_argument(
      '--maintenance-interval',
      type=type_validator,
      hidden=hidden,
      help=help_text)


def AddNodePoolNameArg(parser, help_text):
  """Adds a name flag to the given parser.

  Args:
    parser: A given parser.
    help_text: The help text describing the operation being performed.
  """
  parser.add_argument('name', metavar='NAME', help=help_text)


def AddNodePoolClusterFlag(parser, help_text):
  """Adds a --cluster flag to the parser.

  Args:
    parser: A given parser.
    help_text: The help text describing usage of the --cluster flag being set.
  """
  parser.add_argument(
      '--cluster',
      help=help_text,
      action=actions.StoreProperty(properties.VALUES.container.cluster))


def AddEnableAutoRepairFlag(parser, for_node_pool=False, for_create=False):
  """Adds a --enable-autorepair flag to parser."""
  if for_node_pool:
    help_text = """\
Enable node autorepair feature for a node pool.

  $ {command} node-pool-1 --cluster=example-cluster --enable-autorepair
"""
    if for_create:
      help_text += """
Node autorepair is enabled by default for node pools using COS, COS_CONTAINERD, UBUNTU or UBUNTU_CONTAINERD
as a base image, use --no-enable-autorepair to disable.
"""
  else:
    help_text = """\
Enable node autorepair feature for a cluster's default node pool(s).

  $ {command} example-cluster --enable-autorepair
"""
    if for_create:
      help_text += """
Node autorepair is enabled by default for clusters using COS, COS_CONTAINERD, UBUNTU or UBUNTU_CONTAINERD
as a base image, use --no-enable-autorepair to disable.
"""
  help_text += """
See https://cloud.google.com/kubernetes-engine/docs/how-to/node-auto-repair for \
more info."""

  parser.add_argument(
      '--enable-autorepair', action='store_true', default=None, help=help_text)


def AddEnableAutoUpgradeFlag(parser,
                             for_node_pool=False,
                             suppressed=False,
                             default=None):
  """Adds a --enable-autoupgrade flag to parser."""
  if for_node_pool:
    help_text = """\
Sets autoupgrade feature for a node pool.

  $ {command} node-pool-1 --cluster=example-cluster --enable-autoupgrade
"""
  else:
    help_text = """\
Sets autoupgrade feature for a cluster's default node pool(s).

  $ {command} example-cluster --enable-autoupgrade
"""
  help_text += """
See https://cloud.google.com/kubernetes-engine/docs/node-auto-upgrades for more \
info."""

  parser.add_argument(
      '--enable-autoupgrade',
      action='store_true',
      default=default,
      help=help_text,
      hidden=suppressed)


def AddAutoprovisioningNetworkTagsFlag(parser, help_text):
  """Adds a --autoprovisioning-network-tags to the given parser."""
  parser.add_argument(
      '--autoprovisioning-network-tags',
      metavar='TAGS',
      type=arg_parsers.ArgList(min_length=1),
      help=help_text)


def AddAutoprovisioningNetworkTagsCreate(parser):
  AddAutoprovisioningNetworkTagsFlag(
      parser, """\
Applies the given Compute Engine tags (comma separated) on all nodes in the auto-provisioned node pools of the new Standard cluster or the new Autopilot cluster.

Examples:

  $ {command} example-cluster --autoprovisioning-network-tags=tag1,tag2

New nodes in auto-provisioned node pools, including ones created by resize or recreate, will have these tags
on the Compute Engine API instance object and can be used in firewall rules.
See https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create
for examples.
""")


def AddAutoprovisioningNetworkTagsUpdate(parser):
  """Adds a --autoprovisioning-network-tags flag to the given parser."""
  help_text = """\
Replaces the user specified Compute Engine tags on all nodes in all the existing
auto-provisioned node pools in the Standard cluster or the Autopilot with the given tags (comma separated).

Examples:

  $ {command} example-cluster --autoprovisioning-network-tags=tag1,tag2

New nodes in auto-provisioned node pools, including ones created by resize or recreate, will have these tags
on the Compute Engine API instance object and these tags can be used in
firewall rules.
See https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create
for examples.
"""
  parser.add_argument(
      '--autoprovisioning-network-tags',
      metavar='TAGS',
      type=arg_parsers.ArgList(),
      help=help_text)


def AddTagsFlag(parser, help_text):
  """Adds a --tags to the given parser."""
  parser.add_argument(
      '--tags',
      metavar='TAG',
      type=arg_parsers.ArgList(min_length=1),
      help=help_text)


def AddTagsCreate(parser):
  AddTagsFlag(
      parser, """\
Applies the given Compute Engine tags (comma separated) on all nodes in the new
node-pool.

Examples:

  $ {command} example-cluster --tags=tag1,tag2

New nodes, including ones created by resize or recreate, will have these tags
on the Compute Engine API instance object and can be used in firewall rules.
See https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create
for examples.
""")


def AddTagsNodePoolUpdate(parser, hidden=False):
  """Adds a --tags flag to the given parser."""
  help_text = """\
Replaces all the user specified Compute Engine tags on all nodes in an existing
node pool with the given tags (comma separated).

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --tags=tag1,tag2

New nodes, including ones created by resize or recreate, will have these tags
on the Compute Engine API instance object and these tags can be used in
firewall rules.
See https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create
for examples.
"""
  parser.add_argument(
      '--tags',
      metavar='TAG',
      type=arg_parsers.ArgList(),
      help=help_text,
      hidden=hidden)


def AddMasterAuthorizedNetworksFlags(parser, enable_group_for_update=None):
  """Adds Master Authorized Networks related flags to parser.

  Master Authorized Networks related flags are:
  --enable-master-authorized-networks --master-authorized-networks.

  Args:
    parser: A given parser.
    enable_group_for_update: An optional group of mutually exclusive flag
      options to which an --enable-master-authorized-networks flag is added in
      an update command.
  """
  if enable_group_for_update is None:
    # Flags are being added to the same group.
    master_flag_group = parser.add_argument_group('Master Authorized Networks')
    enable_flag_group = master_flag_group
  else:
    # Flags are being added to different groups, so the new one should have no
    # help text (has only one arg).
    master_flag_group = parser.add_argument_group('')
    enable_flag_group = enable_group_for_update

  enable_flag_group.add_argument(
      '--enable-master-authorized-networks',
      default=None,
      help="""\
Allow only specified set of CIDR blocks (specified by the
`--master-authorized-networks` flag) to connect to Kubernetes master through
HTTPS. Besides these blocks, the following have access as well:\n
  1) The private network the cluster connects to if
  `--enable-private-nodes` is specified.
  2) Google Compute Engine Public IPs if `--enable-private-nodes` is not
  specified.\n
Use `--no-enable-master-authorized-networks` to disable. When disabled, public
internet (0.0.0.0/0) is allowed to connect to Kubernetes master through HTTPS.
""",
      action='store_true')
  master_flag_group.add_argument(
      '--master-authorized-networks',
      type=arg_parsers.ArgList(min_length=1),
      metavar='NETWORK',
      help='The list of CIDR blocks (up to {max_private} for private cluster, '
      '{max_public} for public cluster) that are allowed to connect '
      'to Kubernetes master through HTTPS. Specified in CIDR notation (e.g. '
      '1.2.3.4/30). Cannot be specified unless '
      '`--enable-master-authorized-networks` is also specified.'.format(
          max_private=api_adapter.MAX_AUTHORIZED_NETWORKS_CIDRS_PRIVATE,
          max_public=api_adapter.MAX_AUTHORIZED_NETWORKS_CIDRS_PUBLIC))


def AddNetworkPolicyFlags(parser, hidden=False):
  """Adds --enable-network-policy flags to parser."""
  parser.add_argument(
      '--enable-network-policy',
      action='store_true',
      default=None,
      hidden=hidden,
      help='Enable network policy enforcement for this cluster. If you are '
      'enabling network policy on an existing cluster the network policy '
      'addon must first be enabled on the master by using '
      '--update-addons=NetworkPolicy=ENABLED flag.')


def AddNetworkPerformanceConfigFlags(parser, hidden=True):
  """Adds config flags for advanced networking bandwidth tiers."""

  network_perf_config_help = """\
      Configures network performance settings for the node pool.
      If this flag is not specified, the pool will be created
      with its default network performance configuration.

      *total-egress-bandwidth-tier*::: Total egress bandwidth is the available
      outbound bandwidth from a VM, regardless of whether the traffic
      is going to internal IP or external IP destinations.
      The following tier values are allowed: [{tier_values}]

      """.format(tier_values=','.join(['DEFAULT', 'TIER_1']))

  spec = {'total-egress-bandwidth-tier': str}

  parser.add_argument(
      '--network-performance-configs',
      type=arg_parsers.ArgDict(spec=spec),
      action='append',
      metavar='PROPERTY=VALUE',
      hidden=hidden,
      help=network_perf_config_help)


def AddILBSubsettingFlags(parser, hidden=False):
  """Adds --enable-l4-ilb-subsetting flags to parser."""
  parser.add_argument(
      '--enable-l4-ilb-subsetting',
      action='store_true',
      default=None,
      hidden=hidden,
      help='Enable Subsetting for L4 ILB services created on this cluster.')


def AddClusterDNSFlags(parser, hidden=False):
  """Adds flags related to clusterDNS to parser.

  This includes:
  --cluster-dns={clouddns|default},
  --cluster-dns-scope={cluster|vpc},
  --cluster-dns-domain=string

  Args:
    parser: A given parser.
    hidden: Indicates that the flags are hidden.
  """
  group = parser.add_argument_group('ClusterDNS', hidden=hidden)
  group.add_argument(
      '--cluster-dns',
      choices=_DNS_PROVIDER,
      help='DNS provider to use for this cluster.',
      hidden=hidden,
  )
  group.add_argument(
      '--cluster-dns-scope',
      choices=_DNS_SCOPE,
      help="""\
            DNS scope for the Cloud DNS zone created - valid only with
             `--cluster-dns=clouddns`""",
      hidden=hidden,
  )
  group.add_argument(
      '--cluster-dns-domain',
      help="""\
            DNS domain for this cluster.
            The default value is `cluster.local`.
            This is configurable when `--cluster-dns=clouddns` and
             `--cluster-dns-scope=vpc` are set.
            The value must be a valid DNS subdomain as defined in RFC 1123.
            """,
      hidden=hidden,
  )


def AddPrivateClusterFlags(parser, default=None, with_deprecated=False):
  """Adds flags related to private clusters to parser."""

  default = {} if default is None else default
  group = parser.add_argument_group('Private Clusters')
  if with_deprecated:
    if 'private_cluster' not in default:
      group.add_argument(
          '--private-cluster',
          help=('Cluster is created with no public IP addresses on the cluster '
                'nodes.'),
          default=None,
          action=actions.DeprecationAction(
              'private-cluster',
              warn='The --private-cluster flag is deprecated and will be removed '
              'in a future release. Use --enable-private-nodes instead.',
              action='store_true'))

  if 'enable_private_nodes' not in default:
    group.add_argument(
        '--enable-private-nodes',
        help=('Cluster is created with no public IP addresses on the cluster '
              'nodes.'),
        default=None,
        action='store_true')

  if 'enable_private_endpoint' not in default:
    group.add_argument(
        '--enable-private-endpoint',
        help=('Cluster is managed using the private IP address of the master '
              'API endpoint.'),
        default=None,
        action='store_true')

  if 'master_ipv4_cidr' not in default:
    group.add_argument(
        '--master-ipv4-cidr',
        help=('IPv4 CIDR range to use for the master network.  This should have'
              ' a netmask of size /28 and should be used in conjunction with '
              'the --enable-private-nodes flag.'),
        default=None)


def AddEnableLegacyAuthorizationFlag(parser, hidden=False):
  """Adds a --enable-legacy-authorization flag to parser."""
  help_text = """\
Enables the legacy ABAC authentication for the cluster.
User rights are granted through the use of policies which combine attributes
together. For a detailed look at these properties and related formats, see
https://kubernetes.io/docs/admin/authorization/abac/. To use RBAC permissions
instead, create or update your cluster with the option
`--no-enable-legacy-authorization`.
"""
  parser.add_argument(
      '--enable-legacy-authorization',
      action='store_true',
      default=None,
      hidden=hidden,
      help=help_text)


def AddAuthenticatorSecurityGroupFlags(parser, hidden=False):
  """Adds --security-group to parser."""
  help_text = """\
The name of the RBAC security group for use with Google security groups
in Kubernetes RBAC
(https://kubernetes.io/docs/reference/access-authn-authz/rbac/).

To include group membership as part of the claims issued by Google
during authentication, a group must be designated as a security group by
including it as a direct member of this group.

If unspecified, no groups will be returned for use with RBAC."""
  parser.add_argument(
      '--security-group', help=help_text, default=None, hidden=hidden)


def AddStartIpRotationFlag(parser, hidden=False):
  """Adds a --start-ip-rotation flag to parser."""
  help_text = """\
Start the rotation of this cluster to a new IP. For example:

  $ {command} example-cluster --start-ip-rotation

This causes the cluster to serve on two IPs, and will initiate a node upgrade \
to point to the new IP. See documentation for more details: \
https://cloud.google.com/kubernetes-engine/docs/how-to/ip-rotation."""
  parser.add_argument(
      '--start-ip-rotation',
      action='store_true',
      default=False,
      hidden=hidden,
      help=help_text)


def AddStartCredentialRotationFlag(parser, hidden=False):
  """Adds a --start-credential-rotation flag to parser."""
  help_text = """\
Start the rotation of IP and credentials for this cluster. For example:

  $ {command} example-cluster --start-credential-rotation

This causes the cluster to serve on two IPs, and will initiate a node upgrade \
to point to the new IP. See documentation for more details: \
https://cloud.google.com/kubernetes-engine/docs/how-to/credential-rotation."""
  parser.add_argument(
      '--start-credential-rotation',
      action='store_true',
      default=False,
      hidden=hidden,
      help=help_text)


def AddCompleteIpRotationFlag(parser, hidden=False):
  """Adds a --complete-ip-rotation flag to parser."""
  help_text = """\
Complete the IP rotation for this cluster. For example:

  $ {command} example-cluster --complete-ip-rotation

This causes the cluster to stop serving its old IP, and return to a single IP \
state. See documentation for more details: \
https://cloud.google.com/kubernetes-engine/docs/how-to/ip-rotation."""
  parser.add_argument(
      '--complete-ip-rotation',
      action='store_true',
      default=False,
      hidden=hidden,
      help=help_text)


def AddCompleteCredentialRotationFlag(parser, hidden=False):
  """Adds a --complete-credential-rotation flag to parser."""
  help_text = """\
Complete the IP and credential rotation for this cluster. For example:

  $ {command} example-cluster --complete-credential-rotation

This causes the cluster to stop serving its old IP, return to a single IP, and \
invalidate old credentials. See documentation for more details: \
https://cloud.google.com/kubernetes-engine/docs/how-to/credential-rotation."""
  parser.add_argument(
      '--complete-credential-rotation',
      action='store_true',
      default=False,
      hidden=hidden,
      help=help_text)


def AddMaintenanceWindowGroup(parser,
                              hidden=False,
                              recurring_windows_hidden=False):
  """Adds a mutex for --maintenance-window and --maintenance-window-*."""
  maintenance_group = parser.add_group(hidden=hidden, mutex=True)
  maintenance_group.help = """\
One of either maintenance-window or the group of maintenance-window flags can
be set.
"""
  AddDailyMaintenanceWindowFlag(maintenance_group)
  AddRecurringMaintenanceWindowFlags(
      maintenance_group, hidden=recurring_windows_hidden)


def AddDailyMaintenanceWindowFlag(parser, hidden=False, add_unset_text=False):
  """Adds a --maintenance-window flag to parser."""
  help_text = """\
Set a time of day when you prefer maintenance to start on this cluster. \
For example:

  $ {command} example-cluster --maintenance-window=12:43

The time corresponds to the UTC time zone, and must be in HH:MM format.

Non-emergency maintenance will occur in the 4 hour block starting at the
specified time.

This is mutually exclusive with the recurring maintenance windows
and will overwrite any existing window. Compatible with maintenance
exclusions.
"""
  unset_text = """
To remove an existing maintenance window from the cluster, use
'--clear-maintenance-window'.
"""
  description = 'Maintenance windows must be passed in using HH:MM format.'
  unset_description = ' They can also be removed by using the word \"None\".'

  if add_unset_text:
    help_text += unset_text
    description += unset_description

  type_ = arg_parsers.RegexpValidator(
      r'^([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$|^None$', description)
  parser.add_argument(
      '--maintenance-window',
      default=None,
      hidden=hidden,
      type=type_,
      metavar='START_TIME',
      help=help_text)


def AddRecurringMaintenanceWindowFlags(parser, hidden=False, is_update=False):
  """Adds flags related to recurring maintenance windows to the parser."""
  hidden_for_create = hidden and not is_update  # for surface spec validation
  if is_update:
    group = parser.add_group(hidden=hidden, mutex=True)
  else:
    group = parser

  # See core/document_renderers/render_document.py for the formatting
  # weirdness. Newlines in group help text breaks help generation horribly.
  # These + symbols get us our paragraphs. Also, note that gcloud can wrap
  # long commands funny, so these examples have to be tailored to not go too
  # long without whitespace.
  set_window_group = group.add_group(
      hidden=hidden_for_create,
      help="""\
Set a flexible maintenance window by specifying a window that recurs per an
RFC 5545 RRULE. Non-emergency maintenance will occur in the recurring windows.
+
Examples:
+
For a 9-5 Mon-Wed UTC-4 maintenance window:
+
  $ {command} example-cluster --maintenance-window-start=2000-01-01T09:00:00-04:00 --maintenance-window-end=2000-01-01T17:00:00-04:00 --maintenance-window-recurrence='FREQ=WEEKLY;BYDAY=MO,TU,WE'
+
For a daily window from 22:00 - 04:00 UTC:
+
  $ {command} example-cluster --maintenance-window-start=2000-01-01T22:00:00Z --maintenance-window-end=2000-01-02T04:00:00Z --maintenance-window-recurrence=FREQ=DAILY
""")

  set_window_group.add_argument(
      '--maintenance-window-start',
      type=arg_parsers.Datetime.Parse,
      required=True,
      hidden=hidden_for_create,
      metavar='TIME_STAMP',
      help="""\
Start time of the first window (can occur in the past). The start time
influences when the window will start for recurrences. See $ gcloud topic
datetimes for information on time formats.
""")

  set_window_group.add_argument(
      '--maintenance-window-end',
      type=arg_parsers.Datetime.Parse,
      required=True,
      hidden=hidden_for_create,
      metavar='TIME_STAMP',
      help="""\
End time of the first window (can occur in the past). Must take place after the
start time. The difference in start and end time specifies the length of each
recurrence. See $ gcloud topic datetimes for information on time formats.
""")

  set_window_group.add_argument(
      '--maintenance-window-recurrence',
      type=str,
      required=True,
      hidden=hidden_for_create,
      metavar='RRULE',
      help="""\
An RFC 5545 RRULE, specifying how the window will recur. Note that minimum
requirements for maintenance periods will be enforced. Note that FREQ=SECONDLY,
MINUTELY, and HOURLY are not supported.
""")

  if is_update:
    group.add_argument(
        '--clear-maintenance-window',
        action='store_true',
        default=False,
        help="""\
If set, remove the maintenance window that was set with --maintenance-window
family of flags.
""")
    AddMaintenanceExclusionFlags(group)


def AddMaintenanceExclusionFlags(parser, hidden=False, enable_scope=True):
  """Adds flags related to adding a maintenance exclusion to the parser."""
  help_text = """\
Sets a period of time in which maintenance should not occur. This is compatible
with both daily and recurring maintenance windows.
+
Examples:
+
  $ {command} example-cluster \
  --add-maintenance-exclusion-name=holidays-2000 \
  --add-maintenance-exclusion-start=2000-11-20T00:00:00 \
  --add-maintenance-exclusion-end=2000-12-31T23:59:59
"""

  if enable_scope:
    help_text = """\
Sets a period of time in which maintenance should not occur. This is compatible
with both daily and recurring maintenance windows.
If `--add-maintenance-exclusion-scope` is not specified, the exclusion will
exclude all upgrades.
+
Examples:
+
  $ {command} example-cluster \
  --add-maintenance-exclusion-name=holidays-2000 \
  --add-maintenance-exclusion-start=2000-11-20T00:00:00 \
  --add-maintenance-exclusion-end=2000-12-31T23:59:59 \
  --add-maintenance-exclusion-scope=no_upgrades
"""

  group = parser.add_group(hidden=hidden, help=help_text)

  group.add_argument(
      '--add-maintenance-exclusion-name',
      type=str,
      metavar='NAME',
      help="""\
A descriptor for the exclusion that can be used to remove it. If not specified,
it will be autogenerated.
""")

  group.add_argument(
      '--add-maintenance-exclusion-start',
      type=arg_parsers.Datetime.Parse,
      metavar='TIME_STAMP',
      help="""\
Start time of the exclusion window (can occur in the past). If not specified,
the current time will be used. See $ gcloud topic datetimes for information on
time formats.
""")

  group.add_argument(
      '--add-maintenance-exclusion-end',
      type=arg_parsers.Datetime.Parse,
      required=True,
      metavar='TIME_STAMP',
      help="""\
End time of the exclusion window. Must take place after the start time. See
$ gcloud topic datetimes for information on time formats.
""")

  group.add_argument(
      '--add-maintenance-exclusion-scope',
      type=arg_parsers.RegexpValidator(
          r'^(no_upgrades|no_minor_upgrades|no_minor_or_node_upgrades)$',
          'Must be in one of "no_upgrades", "no_minor_upgrades" or "no_minor_or_node_upgrades"'
      ),
      required=False,
      metavar='SCOPE',
      help="""\
Scope of the exclusion window to specify the type of upgrades that the exclusion
will apply to. Must be in one of no_upgrades, no_minor_upgrades or no_minor_or_node_upgrades.
If not specified in an exclusion, defaults to no_upgrades.
""",
      hidden=not enable_scope)

  parser.add_argument(
      '--remove-maintenance-exclusion',
      type=str,
      hidden=hidden,
      metavar='NAME',
      help="""\
Name of a maintenance exclusion to remove. If you hadn't specified a name, one
was auto-generated. Get it with $ gcloud container clusters describe.
""")


def AddLabelsFlag(parser, suppressed=False):
  """Adds Labels related flags to parser.

  Args:
    parser: A given parser.
    suppressed: Whether or not to suppress help text.
  """

  help_text = """\
Labels to apply to the Google Cloud resources in use by the Kubernetes Engine
cluster. These are unrelated to Kubernetes labels.

Examples:

  $ {command} example-cluster --labels=label_a=value1,label_b=,label_c=value3
"""
  parser.add_argument(
      '--labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=help_text,
      hidden=suppressed)


def AddUpdateLabelsFlag(parser):
  """Adds Update Labels related flags to parser.

  Args:
    parser: A given parser.
  """

  help_text = """\
Labels to apply to the Google Cloud resources in use by the Kubernetes Engine
cluster. These are unrelated to Kubernetes labels.

Examples:

  $ {command} example-cluster --update-labels=label_a=value1,label_b=value2
"""
  parser.add_argument(
      '--update-labels',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help=help_text)


def AddRemoveLabelsFlag(parser):
  """Adds Remove Labels related flags to parser.

  Args:
    parser: A given parser.
  """

  help_text = """\
Labels to remove from the Google Cloud resources in use by the Kubernetes Engine
cluster. These are unrelated to Kubernetes labels.

Examples:

  $ {command} example-cluster --remove-labels=label_a,label_b
"""
  parser.add_argument(
      '--remove-labels',
      metavar='KEY',
      type=arg_parsers.ArgList(),
      help=help_text)


def AddDiskSizeFlag(parser):
  parser.add_argument(
      '--disk-size',
      type=arg_parsers.BinarySize(lower_bound='10GB'),
      help='Size for node VM boot disks in GB. Defaults to 100GB.')


def AddDiskTypeFlag(parser):
  """Adds a --disk-type flag to the given parser.

  Args:
    parser: A given parser.
  """
  help_text = """\
Type of the node VM boot disk. Defaults to pd-standard.
"""
  parser.add_argument(
      '--disk-type',
      help=help_text,
      choices=['pd-standard', 'pd-ssd', 'pd-balanced'])


def AddIpAliasCoreFlag(parser):
  parser.add_argument(
      '--enable-ip-alias',
      action='store_true',
      default=None,
      help="""\
Enable use of alias IPs (https://cloud.google.com/compute/docs/alias-ip/)
for Pod IPs. This will require at least two secondary ranges in the
subnetwork, one for the pod IPs and another to reserve space for the
services range.
""")


def AddIPAliasRelatedFlags(parser):
  """Adds flags related to IP aliases to the parser.

  Args:
    parser: A given parser.
  """
  parser.add_argument(
      '--services-ipv4-cidr',
      metavar='CIDR',
      help="""\
Set the IP range for the services IPs.

Can be specified as a netmask size (e.g. '/20') or as in CIDR notion
(e.g. '10.100.0.0/20'). If given as a netmask size, the IP range will
be chosen automatically from the available space in the network.

If unspecified, the services CIDR range will be chosen with a default
mask size.

Can not be specified unless '--enable-ip-alias' is also specified.
""")
  parser.add_argument(
      '--create-subnetwork',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""\
Create a new subnetwork for the cluster. The name and range of the
subnetwork can be customized via optional 'name' and 'range' key-value
pairs.

'name' specifies the name of the subnetwork to be created.

'range' specifies the IP range for the new subnetwork. This can either
be a netmask size (e.g. '/20') or a CIDR range (e.g. '10.0.0.0/20').
If a netmask size is specified, the IP is automatically taken from the
free space in the cluster's network.

Examples:

Create a new subnetwork with a default name and size.

  $ {command} --create-subnetwork ""

Create a new subnetwork named "my-subnet" with netmask of size 21.

  $ {command} --create-subnetwork name=my-subnet,range=/21

Create a new subnetwork with a default name with the primary range of
10.100.0.0/16.

  $ {command} --create-subnetwork range=10.100.0.0/16

Create a new subnetwork with the name "my-subnet" with a default range.

  $ {command} --create-subnetwork name=my-subnet

Can not be specified unless '--enable-ip-alias' is also specified. Can
not be used in conjunction with the '--subnetwork' option.
""")
  parser.add_argument(
      '--cluster-secondary-range-name',
      metavar='NAME',
      help="""\
Set the secondary range to be used as the source for pod IPs. Alias
ranges will be allocated from this secondary range.  NAME must be the
name of an existing secondary range in the cluster subnetwork.

Must be used in conjunction with '--enable-ip-alias'. Cannot be used
with --create-subnetwork.
""")
  parser.add_argument(
      '--services-secondary-range-name',
      metavar='NAME',
      help="""\
Set the secondary range to be used for services (e.g. ClusterIPs).
NAME must be the name of an existing secondary range in the cluster
subnetwork.

Must be used in conjunction with '--enable-ip-alias'. Cannot be used
with --create-subnetwork.
""")


def AddMaxPodsPerNodeFlag(parser, for_node_pool=False, hidden=False):
  """Adds max pod number constraints flags to the parser.

  Args:
    parser: A given parser.
    for_node_pool: True if it's applied to a node pool. False if it's applied to
      a cluster.
    hidden: Whether or not to hide the help text.
  """
  parser.add_argument(
      '--max-pods-per-node',
      default=None,
      help="""\
The max number of pods per node for this node pool.

This flag sets the maximum number of pods that can be run at the same time on a
node. This will override the value given with --default-max-pods-per-node flag
set at the cluster level.

Must be used in conjunction with '--enable-ip-alias'.
""",
      hidden=hidden,
      type=int)
  if not for_node_pool:
    parser.add_argument(
        '--default-max-pods-per-node',
        default=None,
        help="""\
The default max number of pods per node for node pools in the cluster.

This flag sets the default max-pods-per-node for node pools in the cluster. If
--max-pods-per-node is not specified explicitly for a node pool, this flag
value will be used.

Must be used in conjunction with '--enable-ip-alias'.
""",
        hidden=hidden,
        type=int)


def AddMinCpuPlatformFlag(parser, for_node_pool=False, hidden=False):
  """Adds the --min-cpu-platform flag to the parser.

  Args:
    parser: A given parser.
    for_node_pool: True if it's applied a non-default node pool.
    hidden: Whether or not to hide the help text.
  """
  if for_node_pool:
    help_text = """\
When specified, the nodes for the new node pool will be scheduled on host with
specified CPU architecture or a newer one.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --min-cpu-platform=PLATFORM

"""
  else:
    help_text = """\
When specified, the nodes for the new cluster's default node pool will be
scheduled on host with specified CPU architecture or a newer one.

Examples:

  $ {command} example-cluster --min-cpu-platform=PLATFORM

"""

  help_text += """\
To list available CPU platforms in given zone, run:

  $ gcloud beta compute zones describe ZONE --format="value(availableCpuPlatforms)"

CPU platform selection is available only in selected zones.
"""

  parser.add_argument(
      '--min-cpu-platform', metavar='PLATFORM', hidden=hidden, help=help_text)


def AddWorkloadMetadataFlag(parser, use_mode=True):
  """Adds the --workload-metadata flag to the parser.

  Args:
    parser: A given parser.
    use_mode: Whether use Mode or NodeMetadata in WorkloadMetadataConfig.
  """
  choices = {
      'GCE_METADATA':
          "Pods running in this node pool have access to the node's "
          'underlying Compute Engine Metadata Server.',
      'GKE_METADATA':
          'Run the Kubernetes Engine Metadata Server on this node. The '
          'Kubernetes Engine Metadata Server exposes a metadata API to '
          'workloads that is compatible with the V1 Compute Metadata APIs '
          'exposed by the Compute Engine and App Engine Metadata Servers. '
          'This feature can only be enabled if Workload Identity is enabled '
          'at the cluster level.',
  }
  if not use_mode:
    choices.update({
        'SECURE': '[DEPRECATED] Prevents pods not in hostNetwork from '
                  'accessing certain VM metadata, specifically kube-env, which '
                  'contains Kubelet credentials, and the instance identity '
                  'token. This is a temporary security solution available '
                  'while the bootstrapping process for cluster nodes is '
                  'being redesigned with significant security improvements. '
                  'This feature is scheduled to be deprecated in the future '
                  'and later removed.',
        'EXPOSED':
            "[DEPRECATED] Pods running in this node pool have access to the node's "
            'underlying Compute Engine Metadata Server.',
        'GKE_METADATA_SERVER':
            '[DEPRECATED] Run the Kubernetes Engine Metadata Server on this node. The '
            'Kubernetes Engine Metadata Server exposes a metadata API to '
            'workloads that is compatible with the V1 Compute Metadata APIs '
            'exposed by the Compute Engine and App Engine Metadata Servers. '
            'This feature can only be enabled if Workload Identity is enabled '
            'at the cluster level.',
    })

  parser.add_argument(
      '--workload-metadata',
      default=None,
      choices=choices,
      type=lambda x: x.upper(),
      help='Type of metadata server available to pods running in the node pool.'
  )
  parser.add_argument(
      '--workload-metadata-from-node',
      default=None,
      hidden=True,
      choices=choices,
      type=lambda x: x.upper(),
      help='Type of metadata server available to pods running in the node pool.'
  )


def AddTagOrDigestPositional(parser,
                             verb,
                             repeated=True,
                             tags_only=False,
                             arg_name=None,
                             metavar=None):
  """Adds a tag or digest positional arg."""
  digest_str = '*.gcr.io/PROJECT_ID/IMAGE_PATH@sha256:DIGEST or'
  if tags_only:
    digest_str = ''

  if not arg_name:
    arg_name = 'image_names' if repeated else 'image_name'
    metavar = metavar or 'IMAGE_NAME'

  parser.add_argument(
      arg_name,
      metavar=metavar or arg_name.upper(),
      nargs='+' if repeated else None,
      help=('The fully qualified name(s) of image(s) to {verb}. '
            'The name(s) should be formatted as {digest_str} '
            '*.gcr.io/PROJECT_ID/IMAGE_PATH:TAG.'.format(
                verb=verb, digest_str=digest_str)))


def AddImagePositional(parser, verb):
  image_path_format = '*.gcr.io/PROJECT_ID/IMAGE_PATH[:TAG|@sha256:DIGEST]'
  if verb == 'list tags for':
    image_path_format = '*.gcr.io/PROJECT_ID/IMAGE_PATH'
  parser.add_argument(
      'image_name',
      help=('The name of the image to {verb}. The name format should be '
            '{image_format}. '.format(
                verb=verb, image_format=image_path_format)))


def AddNodeLocationsFlag(parser):
  parser.add_argument(
      '--node-locations',
      type=arg_parsers.ArgList(min_length=1),
      metavar='ZONE',
      help="""\
The set of zones in which the specified node footprint should be replicated.
All zones must be in the same region as the cluster's master(s), specified by
the `--zone` or `--region` flag. Additionally, for zonal clusters,
`--node-locations` must contain the cluster's primary zone. If not specified,
all nodes will be in the cluster's primary zone (for zonal clusters) or spread
across three randomly chosen zones within the cluster's region (for regional
clusters).

Note that `NUM_NODES` nodes will be created in each zone, such that if you
specify `--num-nodes=4` and choose two locations, 8 nodes will be created.

Multiple locations can be specified, separated by commas. For example:

  $ {command} example-cluster --zone us-central1-a --node-locations us-central1-a,us-central1-b
""")


def AddLoggingServiceFlag(parser):
  """Adds a --logging-service flag to the parser.

  Args:
    parser: A given parser.
  """
  help_str = """\
Logging service to use for the cluster. Options are:
"logging.googleapis.com/kubernetes" (the Google Cloud Logging
service with Kubernetes-native resource model enabled),
"logging.googleapis.com" (the Google Cloud Logging service),
"none" (logs will not be exported from the cluster)
"""

  parser.add_argument(
      '--logging-service',
      action=actions.DeprecationAction(
          '--logging-service',
          warn='The `--logging-service` flag is deprecated and will be removed '
          'in an upcoming release. Please use `--logging` instead. '
          'For more information, please read: '
          'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.'
      ),
      help=help_str)


def AddMonitoringServiceFlag(parser):
  """Adds a --monitoring-service flag to the parser.

  Args:
    parser: A given parser.
  """

  help_str = """\
Monitoring service to use for the cluster. Options are:
"monitoring.googleapis.com/kubernetes" (the Google Cloud
Monitoring service with Kubernetes-native resource model enabled),
"monitoring.googleapis.com" (the Google Cloud Monitoring service),
"none" (no metrics will be exported from the cluster)
"""

  parser.add_argument(
      '--monitoring-service',
      action=actions.DeprecationAction(
          '--monitoring-service',
          warn='The `--monitoring-service` flag is deprecated and will be '
          'removed in an upcoming release. Please use `--monitoring` instead. '
          'For more information, please read: '
          'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.'
      ),
      help=help_str)


def AddNodeIdentityFlags(parser, example_target):
  """Adds node identity flags to the given parser.

  Node identity flags are --scopes and --service-account.

  Args:
    parser: A given parser.
    example_target: the target for the command, e.g. mycluster.
  """
  node_identity_group = parser.add_group(
      help='Options to specify the node identity.')
  scopes_group = node_identity_group.add_group(help='Scopes options.')
  scopes_group.add_argument(
      '--scopes',
      type=arg_parsers.ArgList(),
      metavar='SCOPE',
      default='gke-default',
      help="""\
Specifies scopes for the node instances.

Examples:

  $ {{command}} {example_target} --scopes=https://www.googleapis.com/auth/devstorage.read_only

  $ {{command}} {example_target} --scopes=bigquery,storage-rw,compute-ro

Multiple scopes can be specified, separated by commas. Various scopes are
automatically added based on feature usage. Such scopes are not added if an
equivalent scope already exists.

- `monitoring-write`: always added to ensure metrics can be written
- `logging-write`: added if Cloud Logging is enabled
  (`--enable-cloud-logging`/`--logging`)
- `monitoring`: added if Cloud Monitoring is enabled
  (`--enable-cloud-monitoring`/`--monitoring`)
- `gke-default`: added for Autopilot clusters that use the default service
  account
- `cloud-platform`: added for Autopilot clusters that use any other service
  account

{scopes_help}
""".format(
    example_target=example_target, scopes_help=compute_constants.ScopesHelp()))

  sa_help_text = (
      'The Google Cloud Platform Service Account to be used by the node VMs. '
      'If a service account is specified, the cloud-platform and '
      'userinfo.email scopes are used. If no Service Account is specified, the '
      'project default service account is used.')
  node_identity_group.add_argument('--service-account', help=sa_help_text)


def AddClusterNodeIdentityFlags(parser):
  """Adds node identity flags to the given parser.

  This is a wrapper around AddNodeIdentityFlags for [alpha|beta] cluster, as it
  provides example-cluster as the example and uses non-deprecated scopes
  behavior.

  Args:
    parser: A given parser.
  """
  AddNodeIdentityFlags(parser, example_target='example-cluster')


def AddNodePoolNodeIdentityFlags(parser):
  """Adds node identity flags to the given parser.

  This is a wrapper around AddNodeIdentityFlags for (GA) node pools, as it
  provides node-pool-1 as the example and uses non-deprecated scopes behavior.

  Args:
    parser: A given parser.
  """
  AddNodeIdentityFlags(
      parser, example_target='node-pool-1 --cluster=example-cluster')


def AddAddonsFlagsWithOptions(parser, addon_options):
  """Adds the --addons flag to the parser with the given addon options."""
  parser.add_argument(
      '--addons',
      type=arg_parsers.ArgList(
          choices=(addon_options + api_adapter.CLOUDRUN_ADDONS),
          visible_choices=(addon_options +
                           api_adapter.VISIBLE_CLOUDRUN_ADDONS)),
      metavar='ADDON',
      help="""\
Addons
(https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/projects.locations.clusters#Cluster.AddonsConfig)
are additional Kubernetes cluster components. Addons specified by this flag will
be enabled. The others will be disabled. Default addons: {0}.
The Istio addon is deprecated and will be removed in an upcoming release.
For more information and migration, see https://cloud.google.com/istio/docs/istio-on-gke/migrate-to-anthos-service-mesh.
""".format(', '.join(api_adapter.DEFAULT_ADDONS)))


def AddAddonsFlags(parser):
  """Adds the --addons flag to the parser for the beta and GA tracks."""
  AddAddonsFlagsWithOptions(parser, api_adapter.ADDONS_OPTIONS)


def AddAlphaAddonsFlags(parser):
  """Adds the --addons flag to the parser for the alpha track."""
  AddAddonsFlagsWithOptions(parser, api_adapter.ALPHA_ADDONS_OPTIONS)


def AddBetaAddonsFlags(parser):
  """Adds the --addons flag to the parser for the beta track."""
  AddAddonsFlagsWithOptions(parser, api_adapter.BETA_ADDONS_OPTIONS)


def AddPodSecurityPolicyFlag(parser, hidden=False):
  """Adds a --enable-pod-security-policy flag to parser."""
  help_text = """\
Enables the pod security policy admission controller for the cluster.  The pod
security policy admission controller adds fine-grained pod create and update
authorization controls through the PodSecurityPolicy API objects. For more
information, see
https://cloud.google.com/kubernetes-engine/docs/how-to/pod-security-policies.
"""
  parser.add_argument(
      '--enable-pod-security-policy',
      action='store_true',
      default=None,
      hidden=hidden,
      help=help_text)


def AddAllowRouteOverlapFlag(parser):
  """Adds a --allow-route-overlap flag to parser."""
  help_text = """\
Allows the provided cluster CIDRs to overlap with existing routes
that are less specific and do not terminate at a VM.

When enabled, `--cluster-ipv4-cidr` must be fully specified (e.g. `10.96.0.0/14`
, but not `/14`). If `--enable-ip-alias` is also specified, both
`--cluster-ipv4-cidr` and `--services-ipv4-cidr` must be fully specified.

Must be used in conjunction with '--enable-ip-alias' or '--no-enable-ip-alias'.
"""
  parser.add_argument(
      '--allow-route-overlap',
      action='store_true',
      default=None,
      help=help_text)


def AddTpuFlags(parser, hidden=False, enable_tpu_service_networking=False):
  """Adds flags related to TPUs to the parser.

  Args:
    parser: A given parser.
    hidden: Whether or not to hide the help text.
    enable_tpu_service_networking: Whether to add the
      enable_tpu_service_networking flag.
  """

  tpu_group = parser.add_group(help='Flags relating to Cloud TPUs:')

  tpu_group.add_argument(
      '--enable-tpu',
      action='store_true',
      default=None,
      hidden=hidden,
      help="""\
Enable Cloud TPUs for this cluster.

Can not be specified unless `--enable-ip-alias` is also specified.
""")

  group = tpu_group

  if enable_tpu_service_networking:
    group = tpu_group.add_mutually_exclusive_group()
    group.add_argument(
        '--enable-tpu-service-networking',
        action='store_true',
        default=None,
        hidden=hidden,
        help="""\
Enable Cloud TPU's Service Networking mode. In this mode, the CIDR blocks used
by the Cloud TPUs will be allocated and managed by Service Networking, instead
of Kubernetes Engine.

This cannot be specified if `tpu-ipv4-cidr` is specified.
""")

  group.add_argument(
      '--tpu-ipv4-cidr',
      metavar='CIDR',
      hidden=hidden,
      help="""\
Set the IP range for the Cloud TPUs.

Can be specified as a netmask size (e.g. '/20') or as in CIDR notion
(e.g. '10.100.0.0/20'). If given as a netmask size, the IP range will be chosen
automatically from the available space in the network.

If unspecified, the TPU CIDR range will use automatic default '/20'.

Can not be specified unless '--enable-tpu' and '--enable-ip-alias' are also
specified.
""")


def AddIssueClientCertificateFlag(parser):
  """Adds --issue-client-certificate flag to the parser."""
  help_text = """\
Issue a TLS client certificate with admin permissions.

When enabled, the certificate and private key pair will be present in
MasterAuth field of the Cluster object. For cluster versions before 1.12, a
client certificate will be issued by default. As of 1.12, client certificates
are disabled by default.
"""
  parser.add_argument(
      '--issue-client-certificate',
      action='store_true',
      default=None,
      help=help_text)


def AddIstioConfigFlag(parser, suppressed=False):
  """Adds --istio-config flag to the parser.

  Args:
    parser: A given parser.
    suppressed: Whether or not to suppress help text.
  """

  help_text = """\
Configurations for Istio addon, requires --addons contains Istio for create,
or --update-addons Istio=ENABLED for update.

*auth*::: (Optional) Type of auth MTLS_PERMISSIVE or MTLS_STRICT.

Examples:

  $ {command} example-cluster --istio-config=auth=MTLS_PERMISSIVE
"""
  parser.add_argument(
      '--istio-config',
      metavar='auth=MTLS_PERMISSIVE',
      type=arg_parsers.ArgDict(spec={
          'auth': (lambda x: x.upper()),
      }),
      action=actions.DeprecationAction(
          '--istio-config',
          warn="""\
The `--istio-config` flag is deprecated and will be removed in an upcoming
release. For more information and migration, see
https://cloud.google.com/istio/docs/istio-on-gke/migrate-to-anthos-service-mesh.
"""),
      help=help_text,
      hidden=suppressed)


def ValidateIstioConfigCreateArgs(istio_config_args, addons_args):
  """Validates flags specifying Istio config for create.

  Args:
    istio_config_args: parsed comandline arguments for --istio_config.
    addons_args: parsed comandline arguments for --addons.

  Raises:
    InvalidArgumentException: when auth is not MTLS_PERMISSIVE nor MTLS_STRICT,
    or --addon=Istio is not specified
  """
  if istio_config_args:
    auth = istio_config_args.get('auth', '')
    if auth not in ['MTLS_PERMISSIVE', 'MTLS_STRICT']:
      raise exceptions.InvalidArgumentException(
          '--istio-config', 'auth is either MTLS_PERMISSIVE or MTLS_STRICT'
          'e.g. --istio-config auth=MTLS_PERMISSIVE')
    if 'Istio' not in addons_args:
      raise exceptions.InvalidArgumentException(
          '--istio-config', '--addon=Istio must be specified when '
          '--istio-config is given')


def ValidateIstioConfigUpdateArgs(istio_config_args, disable_addons_args):
  """Validates flags specifying Istio config for update.

  Args:
    istio_config_args: parsed comandline arguments for --istio_config.
    disable_addons_args: parsed comandline arguments for --update-addons.

  Raises:
    InvalidArgumentException: when auth is not MTLS_PERMISSIVE nor MTLS_STRICT,
    or --update-addons=Istio=ENABLED is not specified
  """
  if istio_config_args:
    auth = istio_config_args.get('auth', '')
    if auth not in ['MTLS_PERMISSIVE', 'MTLS_STRICT']:
      raise exceptions.InvalidArgumentException(
          '--istio-config', 'auth must be one of MTLS_PERMISSIVE or '
          'MTLS_STRICT e.g. --istio-config auth=MTLS_PERMISSIVE')
    disable_istio = disable_addons_args.get('Istio')
    if disable_istio is None or disable_istio:
      raise exceptions.InvalidArgumentException(
          '--istio-config', '--update-addons=Istio=ENABLED must be specified '
          'when --istio-config is given')


# TODO(b/110368338): Drop this warning when changing the default value of the
# flag.
def WarnForUnspecifiedIpAllocationPolicy(args):
  if not args.IsSpecified('enable_ip_alias'):
    log.status.Print(
        'Default change: VPC-native is the default mode during cluster '
        'creation for versions greater than 1.21.0-gke.1500. To create '
        'advanced routes based clusters, please pass the '
        '`--no-enable-ip-alias` flag')


def WarnForNodeModification(args, enable_autorepair):
  if not (args.image_type or '').lower().startswith('ubuntu'):
    return
  if enable_autorepair or args.enable_autoupgrade:
    log.status.Print(
        'Note: Modifications on the boot disks of node VMs do not persist '
        'across node recreations. Nodes are recreated during manual-upgrade, '
        'auto-upgrade, auto-repair, and auto-scaling. To preserve '
        'modifications across node recreation, use a DaemonSet.')


def WarnForNodeVersionAutoUpgrade(args):
  if not hasattr(args, 'node_version'):
    return
  if not hasattr(args, 'enable_autoupgrade'):
    return
  if args.IsSpecified('node_version') and args.enable_autoupgrade:
    log.status.Print('Note: ' + util.WARN_NODE_VERSION_WITH_AUTOUPGRADE_ENABLED)


def AddMachineTypeFlag(parser):
  """Adds --machine-type flag to the parser.

  Args:
    parser: A given parser.
  """

  help_text = """\
The type of machine to use for nodes. Defaults to e2-medium.
The list of predefined machine types is available using the following command:

  $ gcloud compute machine-types list

You can also specify custom machine types with the string "custom-CPUS-RAM"
where "CPUS" is the number of virtual CPUs and "RAM" is the amount of RAM in
MiB.

For example, to create a node pool using custom machines with 2 vCPUs and 12 GB
of RAM:

  $ {command} high-mem-pool --machine-type=custom-2-12288
"""

  parser.add_argument('--machine-type', '-m', help=help_text)


def AddWorkloadIdentityFlags(parser, use_identity_provider=False):
  """Adds Workload Identity flags to the parser."""
  parser.add_argument(
      '--workload-pool',
      default=None,
      help="""\
Enable Workload Identity on the cluster.

When enabled, Kubernetes service accounts will be able to act as Cloud IAM
Service Accounts, through the provided workload pool.

Currently, the only accepted workload pool is the workload pool of
the Cloud project containing the cluster, `PROJECT_ID.svc.id.goog`.

For more information on Workload Identity, see

            https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity
  """,
      required=False,
      type=arg_parsers.RegexpValidator(
          # Don't document hub.id.goog in the error, but still pass it through
          # for now.
          r'^[a-z][-a-z0-9]{4,}[a-z0-9]\.(svc|hub)\.id\.goog$',
          "Must be in format of '[PROJECT_ID].svc.id.goog'"),
  )
  if use_identity_provider:
    parser.add_argument(
        '--identity-provider',
        default=None,
        help="""\
  Enable 3P identity provider on the cluster.
    """)


def AddWorkloadIdentityUpdateFlags(parser):
  """Adds Workload Identity update flags to the parser."""
  parser.add_argument(
      '--disable-workload-identity',
      default=False,
      action='store_true',
      help="""\
Disable Workload Identity on the cluster.

For more information on Workload Identity, see

            https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity
""")


def AddWorkloadCertificatesFlags(parser):
  """Adds Workload Certificates flags to the parser."""
  parser.add_argument(
      '--enable-workload-certificates',
      default=None,
      hidden=True,
      action='store_true',
      help="""\
Enable Workload Certificates.

After the cluster is created, configure an issuing certificate authority using
the Kubernetes API.

To disable Workload Certificates in an existing cluster, explicitly set flag
`--no-enable-workload-certificates`.
""")


def AddMeshCertificatesFlags(parser):
  """Adds Mesh Certificates flags to the parser."""
  parser.add_argument(
      '--enable-mesh-certificates',
      default=None,
      hidden=True,
      action='store_true',
      help=textwrap.dedent("""\
    Enable Mesh Certificates.

    After the cluster is created, configure an issuing certificate authority using
    the Kubernetes API.

    To disable Mesh Certificates in an existing cluster, explicitly set flag
    `--no-enable-mesh-certificates`.
    """))


def AddWorkloadAltsFlags(parser):
  """Adds Workload ALTS flags to the parser."""
  parser.add_argument(
      '--enable-alts',
      hidden=True,
      action=arg_parsers.StoreTrueFalseAction,
      help="""\
Enable Workload ALTS.
""")


def AddGkeOidcFlag(parser):
  parser.add_argument(
      '--enable-gke-oidc',
      default=None,
      action=actions.DeprecationAction(
          '--enable-gke-oidc',
          warn='GKE OIDC is being replaced by Identity Service across Anthos '
          'and GKE. Thus, flag `--enable-gke-oidc` is also deprecated. Please '
          'use `--enable-identity-service` to enable the Identity Service '
          'component',
          action='store_true'),
      help="""\
Enable GKE OIDC authentication on the cluster.

When enabled, users would be able to authenticate to Kubernetes cluster after
properly setting OIDC config.

GKE OIDC is by default disabled when creating a new cluster. To disable GKE OIDC
in an existing cluster, explicitly set flag `--no-enable-gke-oidc`.
""")


def AddIdentityServiceFlag(parser):
  parser.add_argument(
      '--enable-identity-service',
      default=None,
      action='store_true',
      help="""\
Enable Identity Service component on the cluster.

When enabled, users can authenticate to Kubernetes cluster with external
identity providers.

Identity Service is by default disabled when creating a new cluster.
To disable Identity Service in an existing cluster, explicitly set flag
`--no-enable-identity-service`.
""")


def AddResourceUsageExportFlags(parser, is_update=False, hidden=False):
  """Adds flags about exporting cluster resource usage to BigQuery."""

  group = parser.add_group(
      "Exports cluster's usage of cloud resources", hidden=hidden)
  if is_update:
    group.is_mutex = True
    group.add_argument(
        '--clear-resource-usage-bigquery-dataset',
        action='store_true',
        hidden=hidden,
        default=None,
        help='Disables exporting cluster resource usage to BigQuery.')
    group = group.add_group()

  dataset_help_text = """\
The name of the BigQuery dataset to which the cluster's usage of cloud
resources is exported. A table will be created in the specified dataset to
store cluster resource usage. The resulting table can be joined with BigQuery
Billing Export to produce a fine-grained cost breakdown.

Examples:

  $ {command} example-cluster --resource-usage-bigquery-dataset=example_bigquery_dataset_name
"""

  group.add_argument(
      '--resource-usage-bigquery-dataset',
      default=None,
      hidden=hidden,
      help=dataset_help_text)

  network_egress_help_text = """\
Enable network egress metering on this cluster.

When enabled, a DaemonSet is deployed into the cluster. Each DaemonSet pod
meters network egress traffic by collecting data from the conntrack table, and
exports the metered metrics to the specified destination.

Network egress metering is disabled if this flag is omitted, or when
`--no-enable-network-egress-metering` is set.
"""
  group.add_argument(
      '--enable-network-egress-metering',
      action='store_true',
      default=None,
      hidden=hidden,
      help=network_egress_help_text)

  resource_consumption_help_text = """\
Enable resource consumption metering on this cluster.

When enabled, a table will be created in the specified BigQuery dataset to store
resource consumption data. The resulting table can be joined with the resource
usage table or with BigQuery billing export.

Resource consumption metering is enabled unless `--no-enable-resource-
consumption-metering` is set.
"""

  if is_update:
    resource_consumption_help_text = """\
Enable resource consumption metering on this cluster.

When enabled, a table will be created in the specified BigQuery dataset to store
resource consumption data. The resulting table can be joined with the resource
usage table or with BigQuery billing export.

To disable resource consumption metering, set `--no-enable-resource-consumption-
metering`. If this flag is omitted, then resource consumption metering will
remain enabled or disabled depending on what is already configured for this
cluster.
"""
  group.add_argument(
      '--enable-resource-consumption-metering',
      action='store_true',
      default=None,
      hidden=hidden,
      help=resource_consumption_help_text)


def AddEnablePrivateIpv6AccessFlag(parser, hidden=False):
  """Adds --enable-private-ipv6-access flag to the parser.

  When enabled, this allows gRPC clients on this cluster's pods a fast
  path to access Google hosted services (eg. Cloud Spanner,
  Cloud Dataflow, Cloud Bigtable)
  This is currently only available on Alpha clusters, and needs
  '--enable-kubernetes-alpha' to be specified also.

  Args:
    parser: A given parser.
    hidden: If true, suppress help text for added options.
  """
  parser.add_argument(
      '--enable-private-ipv6-access',
      default=None,
      help="""\
Enables private access to Google services over IPv6.

When enabled, this allows gRPC clients on this cluster's pods a fast path to
access Google hosted services (eg. Cloud Spanner, Cloud Dataflow, Cloud
Bigtable).

This is currently only available on Alpha clusters, specified by using
--enable-kubernetes-alpha.
      """,
      hidden=hidden,
      action='store_true')


def AddPrivateIpv6GoogleAccessTypeFlag(api_version, parser, hidden=False):
  """Adds --private-ipv6-google-access-type={disabled|outbound-only|bidirectional} flag."""
  messages = apis.GetMessagesModule('container', api_version)
  util.GetPrivateIpv6GoogleAccessTypeMapper(
      messages, hidden).choice_arg.AddToParser(parser)


def AddStackTypeFlag(parser):
  """Adds --stack-type flag to the given parser.

  Args:
    parser: A given parser.
  """
  help_text = "IP stack type of the node VMs. Defaults to 'ipv4'"
  parser.add_argument(
      '--stack-type',
      help=help_text,
      hidden=True,
      choices=['ipv4', 'ipv4-ipv6'])


def AddIpv6AccessTypeFlag(parser):
  """Adds --ipv6-access-type flag to the given parser.

  Args:
    parser: A given parser.
  """
  help_text = "IPv6 access type of the subnetwork. Defaults to 'external'"
  parser.add_argument(
      '--ipv6-access-type',
      help=help_text,
      hidden=True,
      choices=['external', 'internal'])


def AddEnableIntraNodeVisibilityFlag(parser, hidden=False):
  """Adds --enable-intra-node-visibility flag to the parser.

  When enabled, the intra-node traffic is visible to VPC network.

  Args:
    parser: A given parser.
    hidden: If true, suppress help text for added options.
  """
  parser.add_argument(
      '--enable-intra-node-visibility',
      default=None,
      hidden=hidden,
      action='store_true',
      help="""\
Enable Intra-node visibility for this cluster.

Enabling intra-node visibility makes your intra-node pod-to-pod traffic
visible to the networking fabric. With this feature, you can use VPC flow
logging or other VPC features for intra-node traffic.

Enabling it on an existing cluster causes the cluster
master and the cluster nodes to restart, which might cause a disruption.
""")


def AddVerticalPodAutoscalingFlags(parser, hidden=False, experimental=False):
  """Adds vertical pod autoscaling related flags to the parser.

  VerticalPodAutoscaling related flags are:
  --enable-vertical-pod-autoscaling
  --enable-experimental-vertical-pod-autoscaling

  Args:
    parser: A given parser.
    hidden: If true, suppress help text for added options.
    experimental: It true, add experimental vertical pod autoscaling flag
  """

  group = parser.add_group(
      mutex=True, help='Flags for vertical pod autoscaling:')
  group.add_argument(
      '--enable-vertical-pod-autoscaling',
      default=None,
      help='Enable vertical pod autoscaling for a cluster.',
      hidden=hidden,
      action='store_true')
  if experimental:
    group.add_argument(
        '--enable-experimental-vertical-pod-autoscaling',
        default=None,
        help=('Enable experimental vertical pod autoscaling features'
              'for a cluster.'),
        hidden=True,
        action='store_true')


def AddVerticalPodAutoscalingFlagsExperimental(parser, hidden=False):
  return AddVerticalPodAutoscalingFlags(parser, hidden, experimental=True)


def AddSandboxFlag(parser, hidden=False):
  """Adds a --sandbox flag to the given parser.

  Args:
    parser: A given parser.
    hidden: Whether or not to hide the help text.
  """
  type_validator = arg_parsers.RegexpValidator(r'^gvisor$',
                                               'Type must be "gvisor"')
  parser.add_argument(
      '--sandbox',
      type=arg_parsers.ArgDict(
          spec={'type': type_validator}, required_keys=['type'], max_length=1),
      metavar='type=TYPE',
      hidden=hidden,
      help="""\
Enables the requested sandbox on all nodes in the node pool.

Examples:

  $ {command} node-pool-1 --cluster=example-cluster --sandbox="type=gvisor"

The only supported type is 'gvisor'.
      """)


def AddSecurityProfileForCreateFlags(parser, hidden=False):
  """Adds flags related to Security Profile to the parser for cluster creation.

  Args:
    parser: A given parser.
    hidden: Whether or not to hide the help text.
  """

  group = parser.add_group(help='Flags for Security Profile:')

  group.add_argument(
      '--security-profile',
      hidden=hidden,
      help="""\
Name and version of the security profile to be applied to the cluster.

Examples:

  $ {command} example-cluster --security-profile=default-1.0-gke.0
""")

  group.add_argument(
      '--security-profile-runtime-rules',
      default=True,
      action='store_true',
      hidden=hidden,
      help="""\
Apply runtime rules in the specified security profile to the cluster.
When enabled (by default), a security profile controller and webhook
are deployed on the cluster to enforce the runtime rules. If
--no-security-profile-runtime-rules is specified to disable this
feature, only bootstrapping rules are applied, and no security profile
controller or webhook are installed.
""")


def AddSecurityProfileForUpdateFlag(parser, hidden=False):
  """Adds --security-profile to specify security profile for cluster update.

  Args:
    parser: A given parser.
    hidden: Whether or not to hide the help text.
  """

  parser.add_argument(
      '--security-profile',
      hidden=hidden,
      help="""\
Name and version of the security profile to be applied to the cluster.
If not specified, the current setting of security profile will be
preserved.

Examples:

  $ {command} example-cluster --security-profile=default-1.0-gke.1
""")


def AddSecurityProfileForUpgradeFlags(parser, hidden=False):
  """Adds flags related to Security Profile to the parser for cluster upgrade.

  Args:
    parser: A given parser.
    hidden: Whether or not to hide the help text.
  """

  group = parser.add_group(help='Flags for Security Profile:')

  group.add_argument(
      '--security-profile',
      hidden=hidden,
      help="""\
Name and version of the security profile to be applied to the cluster.
If not specified, the current security profile settings are preserved.
If the current security profile is not supported in the new cluster
version, this option must be explicitly specified with a supported
security profile, otherwise the operation will fail.

Examples:

  $ {command} example-cluster --security-profile=default-1.0-gke.1
""")

  group.add_argument(
      '--security-profile-runtime-rules',
      default=None,
      action='store_true',
      hidden=hidden,
      help="""\
Apply runtime rules in the specified security profile to the cluster.
When enabled, a security profile controller and webhook
are deployed on the cluster to enforce the runtime rules. If
--no-security-profile-runtime-rules is specified to disable this
feature, only bootstrapping rules are applied, and no security profile
controller or webhook are installed.
""")


def AddNodeGroupFlag(parser):
  """Adds --node-group flag to the parser."""
  help_text = """\
Assign instances of this pool to run on the specified Google Compute Engine
node group. This is useful for running workloads on sole tenant nodes.

To see available sole tenant node-groups, run:

  $ gcloud compute sole-tenancy node-groups list

To create a sole tenant node group, run:

  $ gcloud compute sole-tenancy node-groups create [GROUP_NAME] \
    --zone [ZONE] --node-template [TEMPLATE_NAME] --target-size [TARGET_SIZE]

See https://cloud.google.com/compute/docs/nodes for more
information on sole tenancy and node groups.
"""

  parser.add_argument('--node-group', help=help_text)


def AddInitialNodePoolNameArg(parser, hidden=True):
  """Adds --node-pool-name argument to the parser."""
  help_text = """\
Name of the initial node pool that will be created for the cluster.

Specifies the name to use for the initial node pool that will be created
with the cluster.  If the settings specified require multiple node pools
to be created, the name for each pool will be prefixed by this name.  For
example running the following will result in three node pools being
created, example-node-pool-0, example-node-pool-1 and
example-node-pool-2:

  $ {command} example-cluster --num-nodes 9 --max-nodes-per-pool 3 \
    --node-pool-name example-node-pool
"""

  parser.add_argument('--node-pool-name', hidden=hidden, help=help_text)


def AddMetadataFlags(parser):
  """Adds --metadata and --metadata-from-file flags to the given parser."""
  metadata_help = """\
      Compute Engine metadata to be made available to the guest operating system
      running on nodes within the node pool.

      Each metadata entry is a key/value pair separated by an equals sign.
      Metadata keys must be unique and less than 128 bytes in length. Values
      must be less than or equal to 32,768 bytes in length. The total size of
      all keys and values must be less than 512 KB. Multiple arguments can be
      passed to this flag. For example:

      ``--metadata key-1=value-1,key-2=value-2,key-3=value-3''

      Additionally, the following keys are reserved for use by Kubernetes
      Engine:

      * ``cluster-location''
      * ``cluster-name''
      * ``cluster-uid''
      * ``configure-sh''
      * ``enable-os-login''
      * ``gci-update-strategy''
      * ``gci-ensure-gke-docker''
      * ``instance-template''
      * ``kube-env''
      * ``startup-script''
      * ``user-data''

      Google Kubernetes Engine sets the following keys by default:

      * ``serial-port-logging-enable''

      See also Compute Engine's
      link:https://cloud.google.com/compute/docs/storing-retrieving-metadata[documentation]
      on storing and retrieving instance metadata.
      """

  parser.add_argument(
      '--metadata',
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      help=metadata_help,
      metavar='KEY=VALUE',
      action=arg_parsers.StoreOnceAction)

  metadata_from_file_help = """\
      Same as ``--metadata'' except that the value for the entry will
      be read from a local file.
      """

  parser.add_argument(
      '--metadata-from-file',
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      help=metadata_from_file_help,
      metavar='KEY=LOCAL_FILE_PATH')


def AddEnableShieldedNodesFlags(parser):
  """Adds a --enable-shielded-nodes flag to the given parser."""
  help_text = """\
Enable Shielded Nodes for this cluster. Enabling Shielded Nodes will enable a
more secure Node credential bootstrapping implementation. Starting with version
1.18, clusters will have Shielded GKE nodes by default.
"""
  parser.add_argument(
      '--enable-shielded-nodes',
      action='store_true',
      default=None,
      help=help_text,
      hidden=False)


# pylint: disable=protected-access
def ValidateSurgeUpgradeSettings(args):
  """Raise exception if upgrade settings are not all-or-nothing."""
  if ('max_surge_upgrade' in args._specified_args and
      'max_unavailable_upgrade' not in args._specified_args):
    raise exceptions.InvalidArgumentException(
        '--max-surge-upgrade', util.INVALIID_SURGE_UPGRADE_SETTINGS)
  if ('max_surge_upgrade' not in args._specified_args and
      'max_unavailable_upgrade' in args._specified_args):
    raise exceptions.InvalidArgumentException(
        '--max-unavailable-upgrade', util.INVALIID_SURGE_UPGRADE_SETTINGS)


def ValidateNotificationConfigFlag(args):
  """Raise exception if validation of notification config fails."""
  if 'notification_config' in args._specified_args:
    if 'pubsub' in args.notification_config:
      pubsub = args.notification_config['pubsub']
      if pubsub != 'ENABLED' and pubsub != 'DISABLED':
        raise exceptions.InvalidArgumentException(
            '--notification-config', 'invalid [pubsub] value \"{0}\"; '
            'must be ENABLED or DISABLED.'.format(pubsub))
      if pubsub == 'ENABLED' and 'pubsub-topic' not in args.notification_config:
        raise exceptions.InvalidArgumentException(
            '--notification-config',
            'when [pubsub] is ENABLED, [pubsub-topic] must not be empty')
    if 'filter' in args.notification_config:
      known_event_types = [
          'UpgradeEvent', 'UpgradeAvailableEvent', 'SecurityBulletinEvent'
      ]
      lower_known_event_types = []
      for event_type in known_event_types:
        lower_known_event_types.append(event_type.lower())
      filter_opt = args.notification_config['filter']
      inputted_types = filter_opt.split('|')

      for inputted_type in inputted_types:
        if inputted_type.lower() not in lower_known_event_types:
          raise exceptions.InvalidArgumentException(
              '--notification_config',
              'valid keys for filter are {0}; received \'{1}\''.format(
                  known_event_types, inputted_type))


# pylint: enable=protected-access


def AddSurgeUpgradeFlag(parser, for_node_pool=False, default=None):
  """Adds --max-surge-upgrade flag to the parser."""

  if for_node_pool:
    max_surge_help = """\
Number of extra (surge) nodes to be created on each upgrade of the node pool.

Specifies the number of extra (surge) nodes to be created during this node
pool's upgrades. For example, running the following command will result in
creating an extra node each time the node pool is upgraded:

  $ {command} node-pool-1 --cluster=example-cluster --max-surge-upgrade=1 \
  --max-unavailable-upgrade=0

Must be used in conjunction with '--max-unavailable-upgrade'.
"""
  else:
    max_surge_help = """\
Number of extra (surge) nodes to be created on each upgrade of a node pool.

Specifies the number of extra (surge) nodes to be created during this node
pool's upgrades. For example, running the following command will result in
creating an extra node each time the node pool is upgraded:

  $ {command} example-cluster --max-surge-upgrade=1 --max-unavailable-upgrade=0

Must be used in conjunction with '--max-unavailable-upgrade'.
"""
  parser.add_argument(
      '--max-surge-upgrade',
      type=int,
      default=default,
      help=max_surge_help,
      hidden=False)


def AddMaxUnavailableUpgradeFlag(parser, for_node_pool=False, is_create=False):
  """Adds --max-unavailable-upgrade flag to the parser."""

  if for_node_pool:
    if is_create:
      max_unavailable_upgrade_help = """\
Number of nodes that can be unavailable at the same time on each upgrade of the
node pool.

Specifies the number of nodes that can be unavailable at the same time during
this node pool's upgrades. For example, running the following command will
result in having 3 nodes being upgraded in parallel (1 + 2), but keeping always
at least 3 (5 - 2) available each time the node pool is upgraded:

  $ {command} node-pool-1 --cluster=example-cluster --num-nodes=5 \
  --max-surge-upgrade=1 --max-unavailable-upgrade=2

Must be used in conjunction with '--max-surge-upgrade'.
"""
    else:
      max_unavailable_upgrade_help = """\
Number of nodes that can be unavailable at the same time on each upgrade of the
node pool.

Specifies the number of nodes that can be unavailable at the same time during
this node pool's upgrades. For example, assume the node pool has 5 nodes,
running the following command will result in having 3 nodes being upgraded in
parallel (1 + 2), but keeping always at least 3 (5 - 2) available each time the
node pool is upgraded:

  $ {command} node-pool-1 --cluster=example-cluster --max-surge-upgrade=1 \
  --max-unavailable-upgrade=2

Must be used in conjunction with '--max-surge-upgrade'.
"""

  else:
    max_unavailable_upgrade_help = """\
Number of nodes that can be unavailable at the same time on each upgrade of a
node pool.

Specifies the number of nodes that can be unavailable at the same time while
this node pool is being upgraded. For example, running the following command
will result in having 3 nodes being upgraded in parallel (1 + 2), but keeping
always at least 3 (5 - 2) available each time the node pool is upgraded:

   $ {command} example-cluster --num-nodes=5 --max-surge-upgrade=1 \
     --max-unavailable-upgrade=2

Must be used in conjunction with '--max-surge-upgrade'.
"""
  parser.add_argument(
      '--max-unavailable-upgrade',
      type=int,
      default=None,
      help=max_unavailable_upgrade_help,
      hidden=False)


def AddRespectPodDisruptionBudgetFlag(parser, hidden=True):
  """Adds --respect-pdb flag to the parser."""

  respect_pdb_help = """\
Indicates whether node pool rollbacks should respect pod disruption budgets.
"""

  parser.add_argument(
      '--respect-pdb', type=bool, help=respect_pdb_help, hidden=hidden)


def AddEnableRollingUpdateFlag(parser, hidden=True):
  """Adds --enable-rolling-update flag to the parser."""

  enable_rolling_update_help = """\
Changes node pool update strategy to Rolling Update.
"""

  parser.add_argument(
      '--enable-rolling-update',
      action='store_true',
      help=enable_rolling_update_help,
      hidden=hidden)


def AddEnableBlueGreenUpdateFlag(parser, hidden=True):
  """Adds --enable-blue-green-update flag to the parser."""

  blue_green_update_help = """\
Changes node pool update strategy to Blue Green Update.
"""

  parser.add_argument(
      '--enable-blue-green-update',
      action='store_true',
      help=blue_green_update_help,
      hidden=hidden)


def AddNodePoolSoakDurationFlag(parser, for_node_pool=False, hidden=True):
  """Adds --node-pool-soak-duration flag to the parser."""

  node_pool_soak_duration_help = """\
Time in seconds to be spent waiting during Blue Green Update before
deleting the Blue pool and completing the update.

"""

  if for_node_pool:
    node_pool_soak_duration_help += """\
  $ {command} node-pool-1 --cluster=example-cluster\
  --node-pool-soak-duration=600s
"""
  else:
    node_pool_soak_duration_help += """\
  $ {command} example-cluster\
  --node-pool-soak-duration=600s
"""

  parser.add_argument(
      '--node-pool-soak-duration',
      type=str,
      help=node_pool_soak_duration_help,
      hidden=hidden)


def AddStandardRolloutPolicyFlag(parser, for_node_pool=False, hidden=True):
  """Adds --standard-rollout-policy flag to the parser."""

  standard_rollout_policy_help = """\
Standard rollout policy options for Blue Green Update.

Batch sizes are specfied by one of, batch-node-count or batch-percent.
The duration between batches is specified by batch-soak-duration.

"""

  if for_node_pool:
    standard_rollout_policy_help += """\
  $ {command} node-pool-1 --cluster=example-cluster\
  --standard-rollout-policy=batch-node-count=3,batch-soak-duration=60s

  $ {command} node-pool-1 --cluster=example-cluster\
  --standard-rollout-policy=batch-percent=3,batch-soak-duration=60s
"""
  else:
    standard_rollout_policy_help += """\
  $ {command} example-cluster\
  --standard-rollout-policy=batch-node-count=3,batch-soak-duration=60s

  $ {command} example-cluster\
  --standard-rollout-policy=batch-percent=3,batch-soak-duration=60s
"""

  spec = {
      'batch-node-count': int,
      'batch-percent': float,
      'batch-soak-duration': str,
  }

  parser.add_argument(
      '--standard-rollout-policy',
      help=standard_rollout_policy_help,
      hidden=hidden,
      metavar='batch-node-count=BATCH_NODE_COUNT,batch-percent=BATCH_NODE_PERCENTAGE,batch-soak-duration=BATCH_SOAK_DURATION',
      type=arg_parsers.ArgDict(spec=spec))


def AddLinuxSysctlFlags(parser, for_node_pool=False):
  """Adds Linux sysctl flag to the given parser."""
  if for_node_pool:
    help_text = """\
Linux kernel parameters to be applied to all nodes in the new node pool as well
as the pods running on the nodes.

Examples:

  $ {command} node-pool-1 --linux-sysctls="net.core.somaxconn=1024,net.ipv4.tcp_rmem=4096 87380 6291456"
"""
  else:
    help_text = """\
Linux kernel parameters to be applied to all nodes in the new cluster's default
node pool as well as the pods running on the nodes.

Examples:

  $ {command} example-cluster --linux-sysctls="net.core.somaxconn=1024,net.ipv4.tcp_rmem=4096 87380 6291456"
"""
  parser.add_argument(
      '--linux-sysctls',
      type=arg_parsers.ArgDict(min_length=1),
      default={},
      help=help_text,
      metavar='KEY=VALUE',
      action=arg_parsers.StoreOnceAction)


def AddDisableDefaultSnatFlag(parser, for_cluster_create=False):
  """Adds disable-default-snat flag to the parser.

  Args:
    parser: A given parser.
    for_cluster_create: Whether the flag is for cluster creation.
  """

  if for_cluster_create:
    help_text = """\
Disable default source NAT rules applied in cluster nodes.

By default, cluster nodes perform source network address translation (SNAT)
for packets sent from Pod IP address sources to destination IP addresses
that are not in the non-masquerade CIDRs list.
For more details about SNAT and IP masquerading, see:
https://cloud.google.com/kubernetes-engine/docs/how-to/ip-masquerade-agent#how_ipmasq_works
SNAT changes the packet's source IP address to the node's internal IP address.

When this flag is set, GKE does not perform SNAT for packets sent to any destination.
You must set this flag if the cluster uses privately reused public IPs.

The --disable-default-snat flag is only applicable to private GKE clusters, which are
inherently VPC-native. Thus, --disable-default-snat requires that you also set
--enable-ip-alias and --enable-private-nodes.
"""
  else:
    help_text = """\
Disable default source NAT rules applied in cluster nodes.

By default, cluster nodes perform source network address translation (SNAT)
for packets sent from Pod IP address sources to destination IP addresses
that are not in the non-masquerade CIDRs list.
For more details about SNAT and IP masquerading, see:
https://cloud.google.com/kubernetes-engine/docs/how-to/ip-masquerade-agent#how_ipmasq_works
SNAT changes the packet's source IP address to the node's internal IP address.

When this flag is set, GKE does not perform SNAT for packets sent to any destination.
You must set this flag if the cluster uses privately reused public IPs.

The --disable-default-snat flag is only applicable to private GKE clusters, which are
inherently VPC-native. Thus, --disable-default-snat requires that the cluster was created
with both --enable-ip-alias and --enable-private-nodes.
"""
  parser.add_argument(
      '--disable-default-snat',
      default=(False if for_cluster_create else None),
      action='store_true',
      help=help_text)


def AddNodePoolLocationsFlag(parser, for_create=False):
  """Adds a --node-locations flag for node pool to parser."""
  if for_create:
    help_text = """
The set of zones in which the node pool's nodes should be located.

Multiple locations can be specified, separated by commas. For example:

  $ {command} node-pool-1 --cluster=sample-cluster --node-locations=us-central1-a,us-central1-b"""
  else:
    help_text = """\
Set of zones in which the node pool's nodes should be located.
Changing the locations for a node pool will result in nodes being either created or removed
from the node pool, depending on whether locations are being added or removed.

Multiple locations can be specified, separated by commas. For example:

  $ {command} node-pool-1 --cluster=sample-cluster --node-locations=us-central1-a,us-central1-b"""
  parser.add_argument(
      '--node-locations',
      type=arg_parsers.ArgList(min_length=1),
      metavar='ZONE',
      help=help_text)


def AddShieldedInstanceFlags(parser):
  """Adds Shielded Instance flags to the given parser."""
  secure_boot_help = """\
      The instance will boot with secure boot enabled.
      """
  parser.add_argument(
      '--shielded-secure-boot',
      default=None,
      action='store_true',
      help=secure_boot_help)

  integrity_monitoring_help = """\
      Enables monitoring and attestation of the boot integrity of the
      instance. The attestation is performed against the integrity policy
      baseline. This baseline is initially derived from the implicitly
      trusted boot image when the instance is created.
      """
  parser.add_argument(
      '--shielded-integrity-monitoring',
      default=None,
      action='store_true',
      help=integrity_monitoring_help)


def AddDatabaseEncryptionFlag(parser):
  """Adds Database Encryption flags to the given parser."""
  parser.add_argument(
      '--database-encryption-key',
      default=None,
      help="""\
Enable Database Encryption.

Enable database encryption that will be used to encrypt Kubernetes Secrets at
the application layer. The key provided should be the resource ID in the format of
`projects/[KEY_PROJECT_ID]/locations/[LOCATION]/keyRings/[RING_NAME]/cryptoKeys/[KEY_NAME]`.
For more information, see
https://cloud.google.com/kubernetes-engine/docs/how-to/encrypting-secrets.
""",
      required=False,
      type=arg_parsers.RegexpValidator(
          r'^projects/[^/]+/locations/[^/]+/keyRings/[^/]+/cryptoKeys/[^/]+$',
          'Must be in format of \'projects/[KEY_PROJECT_ID]/locations/[LOCATION]/keyRings/[RING_NAME]/cryptoKeys/[KEY_NAME]\''
      ))


def AddDisableDatabaseEncryptionFlag(parser):
  parser.add_argument(
      '--disable-database-encryption',
      default=False,
      action='store_true',
      help="""\
Disable database encryption.

Disable Database Encryption which encrypt Kubernetes Secrets at
the application layer. For more information, see
https://cloud.google.com/kubernetes-engine/docs/how-to/encrypting-secrets.
      """)


def AddSystemConfigFlag(parser, hidden=True):
  """Adds --system-config-from-file flag to the given parser."""
  parser.add_argument(
      '--system-config-from-file',
      type=arg_parsers.FileContents(),
      hidden=hidden,
      help="""
Path of the YAML/JSON file that contains the node configuration, including
Linux kernel parameters (sysctls) and kubelet configs.

Examples:

    kubeletConfig:
      cpuManagerPolicy: static
    linuxConfig:
      sysctl:
        net.core.somaxconn: '2048'
        net.ipv4.tcp_rmem: '4096 87380 6291456'

List of supported kubelet configs in 'kubeletConfig'.

KEY               | VALUE
----------------- | ----------------------------------
cpuManagerPolicy  | either 'static' or 'none'
cpuCFSQuota       | true or false (enabled by default)
cpuCFSQuotaPeriod | interval (e.g., '100ms')

List of supported sysctls in 'linuxConfig'.

KEY                                        | VALUE
------------------------------------------ | ------------------------------------------
net.core.netdev_max_backlog                | Any positive integer, less than 2147483647
net.core.rmem_max                          | Any positive integer, less than 2147483647
net.core.wmem_default                      | Any positive integer, less than 2147483647
net.core.wmem_max                          | Any positive integer, less than 2147483647
net.core.optmem_max                        | Any positive integer, less than 2147483647
net.core.somaxconn                         | Must be [128, 2147483647]
net.ipv4.tcp_rmem                          | Any positive integer tuple
net.ipv4.tcp_wmem                          | Any positive integer tuple
net.ipv4.tcp_tw_reuse                      | Must be {0, 1}

Note, updating the system configuration of an existing node pool requires recreation of the nodes which which might cause a disruption.
""")


def AddCostManagementConfigFlag(parser, is_update=False):
  """Adds flags related to GKE cost management to the given parser."""
  help_text = """
Enable the cost management feature.

When enabled, you can get informational GKE cost breakdowns by cluster,
namespace and label in your billing data exported to BigQuery
(https://cloud.google.com/billing/docs/how-to/export-data-bigquery).
"""

  if is_update:
    help_text += """\

Use --no-enable-cost-management to disable this feature.
"""
  parser.add_argument(
      '--enable-cost-management',
      action='store_true',
      default=None,
      help=help_text)


def AddReservationAffinityFlags(parser, for_node_pool=False):
  """Adds the argument to handle reservation affinity configurations."""
  target = 'node pool' if for_node_pool else 'default initial node pool'

  group_text = """\
Specifies the reservation for the {}.""".format(target)
  group = parser.add_group(help=group_text)

  affinity_text = """\
The type of the reservation for the {}.""".format(target)
  group.add_argument(
      '--reservation-affinity',
      choices=['any', 'none', 'specific'],
      default=None,
      help=affinity_text)
  group.add_argument(
      '--reservation',
      default=None,
      help="""
The name of the reservation, required when `--reservation-affinity=specific`.
""")


def AddDatapathProviderFlag(parser, hidden=False):
  """Adds --datapath-provider={legacy|advanced} flag."""
  help_text = """
Select datapath provider for the cluster. Defaults to `legacy`.

$ {command} --datapath-provider=legacy
$ {command} --datapath-provider=advanced
"""
  parser.add_argument(
      '--datapath-provider',
      choices=_DATAPATH_PROVIDER,
      help=help_text,
      hidden=hidden)


def AddDataplaneV2Flag(parser, hidden=False):
  """Adds --enable-dataplane-v2 boolean flag."""
  help_text = """
Enables the new eBPF dataplane for GKE clusters that is required for
network security, scalability and visibility features.
"""
  parser.add_argument(
      '--enable-dataplane-v2',
      action='store_true',
      help=help_text,
      hidden=hidden)


def AddMasterGlobalAccessFlag(parser, is_update=False):
  """Adds --enable-master-global-access boolean flag."""
  help_text_suffix = """\

Must be used in conjunction with '--enable-ip-alias' and '--enable-private-nodes'.
"""

  if is_update:
    help_text_suffix = """"""

  help_text = """
Use with private clusters to allow access to the master's private endpoint from any Google Cloud region or on-premises environment regardless of the
private cluster's region.
""" + help_text_suffix

  parser.add_argument(
      '--enable-master-global-access',
      help=help_text,
      default=None,
      action='store_true')


def AddEnableGvnicFlag(parser):
  help_text = """
Enable the use of GVNIC for this cluster. Requires re-creation of nodes using
either a node-pool upgrade or node-pool creation.
"""

  parser.add_argument(
      '--enable-gvnic', help=help_text, default=None, action='store_true')


def AddEnableConfidentialNodesFlag(parser, for_node_pool=False, hidden=False,
                                   is_update=False):
  """Adds a --enable-confidential-nodes flag to the given parser."""
  target = 'node pool' if for_node_pool else 'cluster'

  help_text = """\
Enable confidential nodes for the {}. Enabling Confidential Nodes
will create nodes using Confidential VM
https://cloud.google.com/compute/confidential-vm/docs/about-cvm.""".format(
    target)

  if is_update:
    help_text = """\
    Recreate all the nodes in the node pool to be confidential VM
    https://cloud.google.com/compute/confidential-vm/docs/about-cvm."""

  parser.add_argument(
      '--enable-confidential-nodes',
      help=help_text,
      default=None,
      hidden=hidden,
      action='store_true')


def AddKubernetesObjectsExportConfig(parser, for_create=False):
  """Adds kubernetes-objects-changes-target and kubernetes-objects-snapshots-target flags to parser."""
  help_text = """\
Set kubernetes objects changes target [Currently only CLOUD_LOGGING value is supported].
  """
  validation_description = 'Only value CLOUD_LOGGING is accepted'
  regexp = r'^CLOUD_LOGGING$|^NONE$'
  if for_create:
    regexp = r'^CLOUD_LOGGING$'
  type_ = arg_parsers.RegexpValidator(regexp, validation_description)
  group = parser.add_group(hidden=True)
  group.add_argument(
      '--kubernetes-objects-changes-target',
      default=None,
      type=type_,
      help=help_text)
  help_text = """\
Set kubernetes objects snapshots target [Currently only CLOUD_LOGGING value is supported].
  """
  group.add_argument(
      '--kubernetes-objects-snapshots-target',
      default=None,
      type=type_,
      help=help_text)


def AddEnableCloudLogging(parser):
  parser.add_argument(
      '--enable-cloud-logging',
      action=actions.DeprecationAction(
          '--enable-cloud-logging',
          show_message=lambda val: val,
          warn='Legacy Logging and Monitoring is deprecated. Thus, '
          'flag `--enable-cloud-logging` is also deprecated and will be removed'
          ' in an upcoming release. '
          'Please use `--logging` (optionally with `--monitoring`). '
          'For more details, please read: '
          'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.',
          action='store_true'),
      help='Automatically send logs from the cluster to the Google Cloud '
      'Logging API.')


def AddEnableCloudMonitoring(parser):
  parser.add_argument(
      '--enable-cloud-monitoring',
      action=actions.DeprecationAction(
          '--enable-cloud-monitoring',
          show_message=lambda val: val,
          warn='Legacy Logging and Monitoring is deprecated. Thus, '
          'flag `--enable-cloud-monitoring` is also deprecated. Please use '
          '`--monitoring` (optionally with `--logging`). '
          'For more details, please read: '
          'https://cloud.google.com/stackdriver/docs/solutions/gke/installing.',
          action='store_true'),
      help='Automatically send metrics from pods in the cluster to the Google '
      'Cloud Monitoring API. VM metrics will be collected by Google Compute '
      'Engine regardless of this setting.')


def AddMaxNodesPerPool(parser):
  parser.add_argument(
      '--max-nodes-per-pool',
      type=arg_parsers.BoundedInt(100, api_adapter.MAX_NODES_PER_POOL),
      help='The maximum number of nodes to allocate per default initial node '
      'pool. Kubernetes Engine will automatically create enough nodes pools '
      'such that each node pool contains less than '
      '`--max-nodes-per-pool` nodes. Defaults to {nodes} nodes, but can be set '
      'as low as 100 nodes per pool on initial create.'.format(
          nodes=api_adapter.MAX_NODES_PER_POOL))


def AddNumNodes(parser, default=3):
  parser.add_argument(
      '--num-nodes',
      type=arg_parsers.BoundedInt(1),
      help='The number of nodes to be created in each of the cluster\'s zones.',
      default=default)


def AddThreadsPerCore(parser):
  help_text = """
      The number of visible threads per physical core for each node. To disable
      simultaneous multithreading (SMT) set this to 1.
    """
  parser.add_argument(
      '--threads-per-core',
      type=arg_parsers.BoundedInt(1),
      help=help_text,
      default=None)


def AddNumaNodeCount(parser):
  help_text = """
      The number of virtual NUMA nodes for the instance.
      Valid values are: 0, 1, 2, 4 or 8. Setting NUMA node count to 0 means
      using the default setting.
      """
  parser.add_argument(
      '--numa-node-count',
      type=arg_parsers.BoundedInt(1),
      help=help_text,
      default=None)


def AddEnableGcfsFlag(parser, for_node_pool=False, hidden=True):
  """Adds the argument to handle GCFS configurations."""
  target = 'node pool' if for_node_pool else 'default initial node pool'
  help_text = """\
Specifies whether to enable GCFS on {}.""".format(target)
  parser.add_argument(
      '--enable-gcfs',
      help=help_text,
      default=None,
      hidden=hidden,
      action='store_true')


def AddEnableImageStreamingFlag(parser, for_node_pool=False):
  """Adds the argument to handle image streaming configurations."""
  target = 'node pool' if for_node_pool else 'cluster'
  help_text = """\
Specifies whether to enable image streaming on {}.""".format(target)
  parser.add_argument(
      '--enable-image-streaming',
      help=help_text,
      default=None,
      action='store_true')


def AddDisableAutopilotFlag(parser):
  """Adds the argument to convert cluster from Autopilot mode to Standard mode."""
  help_text = """\
Converts a cluster from Autopilot mode to Standard mode."""
  parser.add_argument(
      '--disable-autopilot',
      help=help_text,
      default=None,
      hidden=True,
      action='store_true')


def AddPrivateEndpointSubnetworkFlag(parser, hidden=True):
  """Adds the argument to handle private endpoint subnetwork."""
  help_text = ' '
  parser.add_argument(
      '--private-endpoint-subnetwork',
      help=help_text,
      hidden=hidden,
      metavar='NAME')


def AddCrossConnectSubnetworksFlag(parser, hidden=True):
  """Adds the cross connect items to the operations."""
  help_text = ' '

  parser.add_argument(
      '--cross-connect-subnetworks',
      help=help_text,
      hidden=hidden,
      type=arg_parsers.ArgList(min_length=1),
      metavar='SUBNETS')


def AddCrossConnectSubnetworkFlag(parser, hidden=True):
  """Adds the argument for identifying the cross connect subnet."""
  parser.add_argument(
      '--cross-connect-subnetwork',
      hidden=hidden,
      help='full path of cross connect subnet whose endpoint to persist')


def AddGetCredentialsArgs(parser):
  """Add common arguments for `get-credentials` command."""
  parser.add_argument(
      'name',
      help='Name of the cluster to get credentials for.',
      action=actions.StoreProperty(properties.VALUES.container.cluster))
  parser.add_argument(
      '--internal-ip',
      help='Whether to use the internal IP address of the cluster endpoint.',
      action='store_true')


def AddCrossConnectSubnetworksMutationFlags(parser, hidden=True):
  """Adds flags for mutating cross connect subnetworks in cluster update."""
  add_help_text = ' '

  remove_help_text = ' '

  clear_help_text = ' '

  parser.add_argument(
      '--add-cross-connect-subnetworks',
      help=add_help_text,
      hidden=hidden,
      type=arg_parsers.ArgList(min_length=1),
      metavar='SUBNETS')

  parser.add_argument(
      '--remove-cross-connect-subnetworks',
      help=remove_help_text,
      hidden=hidden,
      type=arg_parsers.ArgList(min_length=1),
      metavar='SUBNETS')

  parser.add_argument(
      '--clear-cross-connect-subnetworks',
      help=clear_help_text,
      hidden=hidden,
      default=None,
      action='store_true')


def AddNetworkConfigFlags(parser):
  """Adds flags related to the network config for the node pool.

  Args:
    parser: A given parser.
  """
  group = parser.add_mutually_exclusive_group()

  group.add_argument(
      '--pod-ipv4-range',
      metavar='NAME',
      help="""
Set the pod range to be used as the source for pod IPs for the pods in this node
pool. NAME must be the name of an existing subnetwork secondary range in the
subnetwork for this cluster.

Must be used in VPC native clusters. Cannot be used with
`--create-ipv4-pod-range`.

Examples:

Specify a pod range called ``other-range''

  $ {command} --pod-ipv4-range other-range
""")
  group.add_argument(
      '--create-pod-ipv4-range',
      metavar='KEY=VALUE',
      type=arg_parsers.ArgDict(),
      help="""
Create a new pod range for the node pool. The name and range of the
pod range can be customized via optional ``name'' and ``range'' keys.

``name'' specifies the name of the secondary range to be created.

``range'' specifies the IP range for the new secondary range. This can either
be a netmask size (e.g. "/20") or a CIDR range (e.g. "10.0.0.0/20").
If a netmask size is specified, the IP is automatically taken from the
free space in the cluster's network.

Must be used in VPC native clusters. Can not be used in conjunction with the
`--pod-ipv4-range` option.

Examples:

Create a new pod range with a default name and size.

  $ {command} --create-pod-ipv4-range ""

Create a new pod range named ``my-range'' with netmask of size ``21''.

  $ {command} --create-pod-ipv4-range name=my-range,range=/21

Create a new pod range with a default name with the primary range of
``10.100.0.0/16''.

  $ {command} --create-pod-ipv4-range range=10.100.0.0/16

Create a new pod range with the name ``my-range'' with a default range.

  $ {command} --create-pod-ipv4-range name=my-range

Must be used in VPC native clusters. Can not be used in conjunction with the
`--pod-ipv4-range` option.
""")


def AddEnableServiceExternalIPs(parser):
  """Adds a --enable-service-externalips flag to the given parser."""
  help_text = """\
Enables use of services with externalIPs field.
"""
  parser.add_argument(
      '--enable-service-externalips',
      action='store_true',
      default=None,
      help=help_text,
      hidden=False)


def AddDisablePodCIDROverprovisionFlag(parser, hidden=True):
  """Adds a --disable-pod-cidr-overprovision flag to the given parser."""
  help_text = """\
Disables pod cidr overprovision on nodes.
Pod cidr overprovisioning is enabled by default.
"""
  parser.add_argument(
      '--disable-pod-cidr-overprovision',
      action='store_true',
      default=None,
      help=help_text,
      hidden=hidden)


def AddNodePoolEnablePrivateNodes(parser, for_update=False, hidden=True):  # pylint: disable=unused-argument
  """Adds a --enable-private-nodes to the given node-pool parser."""
  help_text = ' '
  # TODO(b/179052417) - make different help text for update & create operations.
  parser.add_argument(
      '--enable-private-nodes',
      hidden=hidden,
      default=None,
      action='store_true',
      help=help_text)


def AddPrivateEndpointFQDNFlag(parser, hidden=True):
  """Adds a --private-endpoint-fqdn flag to the given parser."""
  help_text = ' '
  parser.add_argument(
      '--private-endpoint-fqdn',
      help=help_text,
      hidden=hidden,
      default=None,
      action='store_true')


def VerifyGetCredentialsFlags(args):
  """Verifies that the passed flags are valid for get-credentials.

  Only one of the following flags may be specified at a time:
  --cross-connect, --private-endpoint-fqdn, or --internal-ip

  Args:
    args: an argparse namespace. All the arguments that were provided to this
      command invocation.

  Raises:
    util.Error, if flags conflict.
  """
  if (args.IsSpecified('internal_ip') +
      args.IsSpecified('cross_connect_subnetwork') +
      args.IsSpecified('private_endpoint_fqdn')) > 1:
    raise util.Error(constants.CONFLICTING_GET_CREDS_FLAGS_ERROR_MSG)
