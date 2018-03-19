# Copyright 2017 Google Inc. All Rights Reserved.
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

"""Implements the command for copying files from and to virtual machines."""
from googlecloudsdk.api_lib.compute import base_classes
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import scp_utils


class Scp(base.Command):
  # pylint: disable=line-too-long
  """Copy files to and from Google Compute Engine virtual machines via scp.

  *{command}* securely copies files between a virtual machine instance and your
  local machine using the scp command. **This command does not work for Windows
  VMs.**

  In order to set up a successful transfer, follow these guidelines:
  *   Prefix remote file names with the virtual machine instance
      name (e.g., _example-instance_:~/_FILE_).
  *   Local file names can be used as is (e.g., ~/_FILE_).
  *   File names containing a colon (``:'') must be invoked by either their
      absolute path or a path that begins with ``./''.
  *   When the destination of your transfer is local, all source files must be
      from the same virtual machine.
  *   When the destination of your transfer is remote instead, all sources must
      be local.

  To copy a remote directory, `~/narnia`, from ``example-instance'' to the
  `~/wardrobe` directory of your local host, run:

    $ {command} example-instance:~/narnia ~/wardrobe

  Conversely, files from your local computer can be copied to a virtual machine:

    $ {command} ~/localtest.txt ~/localtest2.txt example-instance:~/narnia

  If the zone cannot be determined, you will be prompted for it.  Use the
  `--zone` flag to avoid being prompted:

    $ {command} example-instance:~/narnia ~/wardrobe --zone us-central1-a

  Under the covers, *scp(1)* is used to facilitate the transfer.
  """
  # pylint: enable=line-too-long

  @staticmethod
  def Args(parser):
    """Set up arguments for this command.

    Args:
      parser: An argparse.ArgumentParser.
    """
    scp_utils.BaseScpHelper.Args(parser)

    parser.add_argument(
        '--port',
        help='The port to connect to.')

    parser.add_argument(
        '--recurse',
        action='store_true',
        help='Upload directories recursively.')

    parser.add_argument(
        '--compress',
        action='store_true',
        help='Enable compression.')

    parser.add_argument(
        '--scp-flag',
        action='append',
        help='Extra flag to be sent to scp. This flag may be repeated.')

  def Run(self, args):
    """See scp_utils.BaseScpCommand.Run."""
    holder = base_classes.ComputeApiHolder(self.ReleaseTrack())

    scp_helper = scp_utils.BaseScpHelper()

    extra_flags = []
    # TODO(b/33467618): Add -C to SCPCommand
    if args.scp_flag:
      extra_flags.extend(args.scp_flag)
    return scp_helper.RunScp(
        holder,
        args,
        port=args.port,
        recursive=args.recurse,
        compress=args.compress,
        extra_flags=extra_flags,
        release_track=self.ReleaseTrack())
