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
"""Command to SSH into a Cloud TPU VM Node."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import argparse
import os.path
import threading

from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.compute import completers
from googlecloudsdk.command_lib.compute import flags
from googlecloudsdk.command_lib.compute import ssh_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import ssh as tpu_ssh_utils
from googlecloudsdk.command_lib.compute.tpus.tpu_vm import util as tpu_utils
from googlecloudsdk.command_lib.util.ssh import ssh
from googlecloudsdk.core import log
from googlecloudsdk.core import properties
from googlecloudsdk.core.util.files import FileWriter
import six


def AddCommandArgGroup(parser):
  """Argument group for running commands using SSH."""
  command_group = parser.add_argument_group(
      help='These arguments are used to run commands using SSH.')
  command_group.add_argument(
      '--command',
      help="""\
      Command to run on the Cloud TPU VM.

      Runs the command on the target Cloud TPU VM and then exits.

      Note: in the case of a TPU Pod, it will only run the command in the
      workers specified with the `--worker` flag (defaults to worker 0 if not
      set).
      """)
  command_group.add_argument(
      '--output-directory',
      help="""\
      Path to the directory to output the logs of the commands.

      The path can be relative or absolute. The directory must already exist.

      If not specified, standard output will be used.

      The logs will be written in files named {WORKER_ID}.log. For example:
      "2.log".
      """)


def AddSSHArgs(parser):
  """Additional flags and positional args to be passed to *ssh(1)*."""
  parser.add_argument(
      '--ssh-flag',
      action='append',
      help="""\
      Additional flags to be passed to *ssh(1)*. It is recommended that flags
      be passed using an assignment operator and quotes. Example:

        $ {command} example-instance --zone=us-central1-a --ssh-flag="-vvv" --ssh-flag="-L 80:localhost:80"

      This flag will replace occurences of ``%USER%'' and ``%TPU%'' with
      their dereferenced values. For example, passing ``80:%TPU%:80`` into
      the flag is equivalent to passing ``80:162.222.181.197:80'' to *ssh(1)*
      if the external IP address of 'example-instance' is 162.222.181.197.

      If connecting to the instance's external IP, then %TPU% is replaced
      with that, otherwise it is replaced with the internal IP.
      """)

  parser.add_argument(
      'user_tpu',
      completer=completers.InstancesCompleter,
      metavar='[USER@]TPU',
      help="""\
      Specifies the Cloud TPU VM to SSH into.

      ``USER'' specifies the username with which to SSH. If omitted, the user
      login name is used.

      ``TPU'' specifies the name of the Cloud TPU VM to SSH into.
      """)

  parser.add_argument(
      'ssh_args',
      nargs=argparse.REMAINDER,
      help="""\
          Flags and positionals passed to the underlying ssh implementation.
          """,
      example="""\
        $ {command} example-instance --zone=us-central1-a -- -vvv -L 80:%TPU%:80
      """)


def SSHRunCmd(env, cmd, output_file_writer):
  """Returns a function to run."""
  return cmd.Run(
      env, force_connect=True, explicit_output_file=output_file_writer,
      explicit_error_file=output_file_writer)


@base.ReleaseTracks(base.ReleaseTrack.ALPHA)
class Ssh(base.Command):
  """SSH into a Cloud TPU VM."""

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    ssh_utils.BaseSSHCLIHelper.Args(parser)
    AddSSHArgs(parser)
    tpu_ssh_utils.AddTPUSSHArgs(parser)
    AddCommandArgGroup(parser)
    flags.AddZoneFlag(parser, resource_type='tpu', operation_type='ssh')

  def Run(self, args):
    user, tpu_name = ssh_utils.GetUserAndInstance(args.user_tpu)

    # If zone is not set, retrieve the one from the config.
    if args.zone is None:
      args.zone = properties.VALUES.compute.zone.Get(required=True)
    # Validate the output path.
    if args.output_directory:
      if not args.command:
        raise exceptions.InvalidArgumentException(
            '--output_directory', 'cannot be specified without the `--command` '
            'flag. Please specify the `--command` flag or remove the '
            '--output-directory flag.')
      output_directory_path = os.path.abspath(
          os.path.expandvars(os.path.expanduser(args.output_directory)))
      if not os.path.isdir(output_directory_path):
        raise exceptions.InvalidArgumentException(
            '--output_directory', 'Failed to find directory {}. Please create '
            'it or specify another directory'.format(output_directory_path))

    # Retrieve the node.
    tpu = tpu_utils.TPUNode()
    node = tpu.Get(tpu_name, args.zone)
    if not tpu_utils.IsTPUVMNode(node):
      raise exceptions.BadArgumentException(
          'TPU',
          'this command is only available for Cloud TPU VM nodes. To access '
          'this node, please see '
          'https://cloud.google.com/tpu/docs/creating-deleting-tpus.')

    worker_ips = tpu_ssh_utils.ParseWorkerFlag(
        args.worker, node.networkEndpoints, args.internal_ip)

    if len(worker_ips) > 1 and not args.command:
      raise exceptions.InvalidArgumentException(
          '--worker', 'cannot target multiple workers without the `--command` '
          'flag.')

    host_key_suffixes = tpu_ssh_utils.GetHostKeySuffixes(
        tpu, tpu_name, worker_ips, len(node.networkEndpoints), args.zone)

    # Generate the public key.
    ssh_helper = ssh_utils.BaseSSHCLIHelper()
    ssh_helper.Run(args)
    public_key = ssh_helper.keys.GetPublicKey().ToEntry()

    project = tpu_utils.GetProject(self.ReleaseTrack(), ssh_helper)

    if not args.plain:
      # If there is an '@' symbol in the user_host arg, the user is requesting
      # to connect as a specific user. This may get overridden by OS Login.
      username_requested = '@' in args.user_tpu
      _, expiration_micros = ssh_utils.GetSSHKeyExpirationFromArgs(args)
      user, _ = ssh.CheckForOsloginAndGetUser(
          None, project, user, public_key, expiration_micros,
          self.ReleaseTrack(), username_requested=username_requested,
          instance_enable_oslogin=tpu_ssh_utils.TpuHasOsLoginEnabled(node))

    # Format the key correctly.
    public_key = '{1}:{0} {1}'.format(public_key, user)

    if not args.plain and not args.dry_run:
      tpu_ssh_utils.AddSSHKeyIfNeeded(
          project, tpu, node, tpu_name, args.zone, public_key)

    command_list = args.command.split(' ') if args.command else None

    remainder = []
    if args.ssh_args:
      remainder.extend(args.ssh_args)

    if args.output_directory:
      log.status.Print('Preparing SSH command execution; output will be logged '
                       'to {}'.format(output_directory_path))

    ssh_threads = []
    for worker, ips in worker_ips.items():
      identity_file = None
      options = None
      if not args.plain:
        identity_file = ssh_helper.keys.key_file
        options = ssh_helper.GetConfig(
            tpu_ssh_utils.GetInstanceID(node.id, worker, host_key_suffixes),
            args.strict_host_key_checking, None)

      remote = ssh.Remote(ips.ip_address, user)
      extra_flags = ssh.ParseAndSubstituteSSHFlags(
          args, remote, ips.ip_address, ips.internal_address)
      cmd = ssh.SSHCommand(remote=remote, identity_file=identity_file,
                           remote_command=command_list, extra_flags=extra_flags,
                           options=options, remainder=remainder)

      if args.dry_run:
        log.out.Print(' '.join(cmd.Build(ssh_helper.env)))
        continue

      output_file_writer = None
      if args.output_directory:
        output_file_writer = FileWriter('{}/{}.log'.format(
            output_directory_path, six.text_type(worker)))

      if len(worker_ips) > 1:
        # Run the command on multiple workers concurrently.
        ssh_threads.append(
            threading.Thread(target=tpu_ssh_utils.AttemptRunWithRetries,
                             args=('SSH', worker, cmd, ssh_helper.env,
                                   output_file_writer, True, SSHRunCmd)))
        ssh_threads[-1].start()
      else:
        # Run on a single worker.
        tpu_ssh_utils.AttemptRunWithRetries(
            'SSH', worker, cmd, ssh_helper.env, output_file_writer, False,
            SSHRunCmd)


