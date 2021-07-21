# -*- coding: utf-8 -*- #
# Copyright 2018 Google LLC. All Rights Reserved.
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
"""Set up flags for creating or updating a workerpool."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.calliope import arg_parsers
from googlecloudsdk.calliope import base

_WP_CONFIG_LINK = 'https://cloud.google.com/build/docs/private-pools/worker-pool-config-file-schema'

_CREATE_FILE_DESC = ('A file that contains the configuration for the'
                     ' worker pool to be created. See %s for options.' %
                     _WP_CONFIG_LINK)
_UPDATE_FILE_DESC = ('A file that contains updates to the configuration for'
                     ' the worker pool. See %s for options.' % _WP_CONFIG_LINK)


def AddWorkerpoolArgs(parser, release_track, update=False):
  """Set up all the argparse flags for creating or updating a workerpool.

  Args:
    parser: An argparse.ArgumentParser-like object.
    release_track: A base.ReleaseTrack-like object.
    update: If true, use the version of the flags for updating a workerpool.
      Otherwise, use the version for creating a workerpool.

  Returns:
    The parser argument with workerpool flags added in.
  """
  verb = 'update' if update else 'create'
  parser.add_argument(
      'WORKER_POOL',
      help='The unique identifier for the worker pool to %s. This value should be 1-63 characters, and valid characters are [a-z][0-9]-'
      % verb)
  parser.add_argument(
      '--region',
      required=True,
      help='The Cloud region where the worker pool is %sd. See https://cloud.google.com/build/docs/locations for available locations.'
      % verb)
  file_or_flags = parser.add_mutually_exclusive_group(required=update)
  file_or_flags.add_argument(
      '--config-from-file',
      help=(_UPDATE_FILE_DESC if update else _CREATE_FILE_DESC),
  )
  flags = file_or_flags.add_argument_group(
      'Command-line flags to configure the worker pool:')
  if not update:
    flags.add_argument(
        '--peered-network',
        help="""\
Existing network to which workers are peered. The network is specified in
resource URL format
projects/{network_project}/global/networks/{network_name}.

If not specified, the workers are not peered to any network.
""")

  worker_flags = flags.add_argument_group(
      'Configuration to be used for creating workers in the worker pool:')
  worker_flags.add_argument(
      '--worker-machine-type',
      help="""\
Compute Engine machine type for a worker pool.

If unspecified, Cloud Build uses a standard machine type.
""")
  worker_flags.add_argument(
      '--worker-disk-size',
      type=arg_parsers.BinarySize(lower_bound='100GB'),
      help="""\
Size of the disk attached to the worker.

If not given, Cloud Build will use a standard disk size.
""")

  worker_flags.add_argument(
      '--no-external-ip',
      hidden=release_track == base.ReleaseTrack.GA,
      action='store_true',
      help="""\
If set, workers in the worker pool are created without an external IP address.

If the worker pool is within a VPC Service Control perimeter, use this flag.
""")

  if release_track == base.ReleaseTrack.GA:
    if update:
      egress_flags = flags.add_mutually_exclusive_group()
      egress_flags.add_argument(
          '--no-public-egress',
          action='store_true',
          help="""\
If set, workers in the worker pool are created without an external IP address.

If the worker pool is within a VPC Service Control perimeter, use this flag.
    """)

      egress_flags.add_argument(
          '--public-egress',
          action='store_true',
          help="""\
If set, workers in the worker pool are created with an external IP address.
  """)
    else:
      flags.add_argument(
          '--no-public-egress',
          action='store_true',
          help="""\
If set, workers in the worker pool are created without an external IP address.

If the worker pool is within a VPC Service Control perimeter, use this flag.
""")

  return parser


def AddWorkerpoolCreateArgs(parser, release_track):
  """Set up all the argparse flags for creating a workerpool.

  Args:
    parser: An argparse.ArgumentParser-like object.
    release_track: A base.ReleaseTrack-like object.

  Returns:
    The parser argument with workerpool flags added in.
  """
  return AddWorkerpoolArgs(parser, release_track, update=False)


def AddWorkerpoolUpdateArgs(parser, release_track):
  """Set up all the argparse flags for updating a workerpool.

  Args:
    parser: An argparse.ArgumentParser-like object.
    release_track: A base.ReleaseTrack-like object.

  Returns:
    The parser argument with workerpool flags added in.
  """
  return AddWorkerpoolArgs(parser, release_track, update=True)
