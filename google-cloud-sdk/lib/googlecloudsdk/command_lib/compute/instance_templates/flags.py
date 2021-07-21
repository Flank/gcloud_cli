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
"""Flags and helpers for the compute instance groups commands."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import re

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute.instance_templates import service_proxy_aux_data

DEFAULT_LIST_FORMAT = """\
    table(
      name,
      properties.machineType.machine_type(),
      properties.scheduling.preemptible.yesno(yes=true, no=''),
      creationTimestamp
    )"""


def MakeInstanceTemplateArg(plural=False):
  return flags.ResourceArgument(
      resource_name='instance template',
      completer=completers.InstanceTemplatesCompleter,
      plural=plural,
      global_collection='compute.instanceTemplates')


def MakeSourceInstanceArg():
  return flags.ResourceArgument(
      name='--source-instance',
      resource_name='instance',
      completer=completers.InstancesCompleter,
      required=False,
      zonal_collection='compute.instances',
      short_help=('The name of the source instance that the instance template '
                  'will be created from.\n\nYou can override machine type and '
                  'labels. Values of other flags will be ignored and values '
                  'from the source instance will be used instead.')
  )


def AddServiceProxyConfigArgs(parser, hide_arguments=False):
  """Adds service proxy configuration arguments for instance templates."""
  service_proxy_group = parser.add_group(hidden=hide_arguments)
  service_proxy_group.add_argument(
      '--service-proxy',
      type=arg_parsers.ArgDict(
          spec={
              'enabled': None,
              'serving-ports': str,
              'proxy-port': int,
              'tracing': service_proxy_aux_data.TracingState,
              'access-log': str,
              'network': str
          },
          allow_key_only=True,
          required_keys=['enabled']),
      hidden=hide_arguments,
      help="""\
      Controls whether the Traffic Director service proxy (Envoy) and agent are installed and configured on the VM.
      "cloud-platform" scope is enabled automatically to allow connections to the Traffic Director API.
      Do not use the --no-scopes flag.

      *enabled*::: If specified, the service-proxy software will be installed when the instance is created.
      The instance is configured to work with Traffic Director.

      *serving-ports*::: Semi-colon-separated (;) list of the ports, specified inside quotation marks ("), on which the customer's application/workload
      is serving.

      For example:

            --serving-ports="80;8080"

      The service proxy will intercept inbound traffic, then forward it to the specified serving port(s) on localhost.
      If not provided, no incoming traffic is intercepted.

      *proxy-port*::: The port on which the service proxy listens.
      The VM intercepts traffic and redirects it to this port to be handled by the service proxy.
      If omitted, the default value is '15001'.

      *tracing*::: Enables the service proxy to generate distributed tracing information.
      If set to ON, the service proxy's control plane generates a configuration that enables request ID-based tracing.
      For more information, refer to the `generate_request_id` documentation
      for the Envoy proxy. Allowed values are `ON` and `OFF`.

      *access-log*::: The filepath for access logs sent to the service proxy by the control plane.
      All incoming and outgoing requests are recorded in this file.
      For more information, refer to the file access log documentation for the Envoy proxy.

      *network*::: The name of a valid VPC network. The Google Cloud Platform VPC network used by the service proxy's control plane
      to generate dynamic configuration for the service proxy.
      """)
  service_proxy_group.add_argument(
      '--service-proxy-labels',
      metavar='KEY=VALUE, ...',
      type=arg_parsers.ArgDict(),
      hidden=hide_arguments,
      help="""\
      Labels that you can apply to your service proxy. These will be reflected in your Envoy proxy's bootstrap metadata.
      These can be any `key=value` pairs that you want to set as proxy metadata (for example, for use with config filtering).
      You might use these flags for application and version labels: `app=review` and/or `version=canary`.
      """)
  service_proxy_group.add_argument(
      '--service-proxy-agent-location',
      metavar='LOCATION',
      hidden=True,
      help="""\
      GCS bucket location of service-proxy-agent. Mainly used for testing and development.
      """)
  service_proxy_group.add_argument(
      '--service-proxy-xds-version',
      type=int,
      hidden=True,
      help="""\
      xDS version of the service proxy to be installed.
      """)


def ValidateServiceProxyFlags(args):
  """Validates the values of all --service-proxy related flags."""

  if getattr(args, 'service_proxy', False):
    if args.no_scopes:
      # --no-scopes flag needs to be removed for adding cloud-platform scope.
      # This is required for TrafficDirector to work properly.
      raise exceptions.ConflictingArgumentsException('--service-proxy',
                                                     '--no-scopes')

    if 'serving-ports' in args.service_proxy:
      try:
        serving_ports = list(
            map(int, args.service_proxy['serving-ports'].split(';')))
        for port in serving_ports:
          if port < 1 or port > 65535:
            # valid port range is 1 - 65535
            raise ValueError
      except ValueError:
        # an invalid port is present in the list of workload ports.
        raise exceptions.InvalidArgumentException(
            'serving-ports',
            'List of ports can only contain numbers between 1 and 65535.')

    if 'proxy-port' in args.service_proxy:
      try:
        proxy_port = args.service_proxy['proxy-port']
        if proxy_port < 1025 or proxy_port > 65535:
          # valid range for proxy-port is 1025 - 65535
          raise ValueError
      except ValueError:
        raise exceptions.InvalidArgumentException(
            'proxy-port',
            'Port value can only be between 1025 and 65535.')


def AddMeshArgs(parser, hide_arguments=False):
  """Adds Anthos Service Mesh configuration arguments for instance templates."""

  mesh_group = parser.add_group(hidden=hide_arguments)
  mesh_group.add_argument(
      '--mesh',
      type=arg_parsers.ArgDict(
          spec={
              'gke-cluster': str,
              'workload': str
          },
          allow_key_only=False,
          required_keys=['gke-cluster', 'workload']),
      hidden=hide_arguments,
      help="""\
      Controls whether the Anthos Service Mesh service proxy (Envoy) and agent are installed and configured on the VM.
      "cloud-platform" scope is enabled automatically to allow the service proxy to be started.
      Do not use the `--no-scopes` flag.

      *gke-cluster*::: The location/name of the GKE cluster. The location can be a zone or a
          region, e.g. ``us-central1-a/my-cluster''.

      *workload*::: The workload identifier of the VM. In a GKE cluster, it is
          the identifier namespace/name of the `WorkloadGroup` custom resource representing the VM
          workload, e.g. ``foo/my-workload''.
      """)


def ValidateMeshFlag(args):
  """Validates the values of the --mesh flag."""

  if getattr(args, 'mesh', False):
    if args.no_scopes:
      # --no-scopes flag needs to be removed for adding cloud-platform scope.
      # This is required for ASM's service proxy to work properly.
      raise exceptions.ConflictingArgumentsException('--mesh',
                                                     '--no-scopes')

    rgx = r'(.*)\/(.*)'
    try:
      if not re.match(rgx, args.mesh['gke-cluster']):
        raise ValueError
    except ValueError:
      raise exceptions.InvalidArgumentException(
          'gke-cluster',
          'GKE cluster value should have the format location/name.')
    try:
      if not re.match(rgx, args.mesh['workload']):
        raise ValueError
    except ValueError:
      raise exceptions.InvalidArgumentException(
          'workload', 'Workload value should have the format namespace/name.')


def AddPostKeyRevocationActionTypeArgs(parser):
  """Helper to add --post-key-revocation-action-type flag."""
  help_text = ('Specifies the behavior of the instance when the KMS key of one '
               'of its attached disks is revoked. The default is noop.')
  choices_text = {
      'noop':
          'No operation is performed.',
      'shutdown': ('The instance is shut down when the KMS key of one of '
                   'its attached disks is revoked.')
  }
  parser.add_argument(
      '--post-key-revocation-action-type',
      choices=choices_text,
      metavar='POLICY',
      required=False,
      help=help_text)
