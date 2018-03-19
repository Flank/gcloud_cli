# Copyright 2015 Google Inc. All Rights Reserved.
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

"""This is a command for testing nested argument groups."""

from googlecloudsdk.calliope import base


class NestedGroups(base.Command):
  """A command with nested argument group combinations."""

  @staticmethod
  def Args(parser):

    router_interface_group = parser.add_group(
        help='Router interface flags.', mutex=True)
    vpn_tunnel_group = router_interface_group.add_group(
        help='VPN tunnel flags.')
    vpn_tunnel_group.add_argument(
        '--vpn-tunnel',
        required=True,
        help='VPN tunnel help.')
    vpn_tunnel_group.add_argument(
        '--vpn-tunnel-region',
        help='VPN tunnel region help.')
    interconnect_attachment = router_interface_group.add_group(
        help='Interconnect attachment flags.')
    interconnect_attachment.add_argument(
        '--interconnect-attachment',
        required=True,
        help='Interconnect attachment help.')
    interconnect_attachment.add_argument(
        '--interconnect-attachment-region',
        help='Interconnect attachment region help.')

    group_00 = parser.add_group(help='Group 00 flags.', mutex=True)
    group_00.add_argument(
        '--abc-00',
        default=False,
        action='store_true',
        help='ABC 00 help text.')
    group_00.add_argument(
        '--xyz-00',
        default=False,
        action='store_true',
        help='XYZ 00 help text.')

    group_01 = parser.add_group(help='Group 01 flags.', mutex=True)
    group_01.add_argument(
        '--abc-01',
        default=False,
        action='store_true',
        help='ABC 01 help text.')
    group_01.add_argument(
        '--xyz-01',
        default=True,
        action='store_true',
        help='XYZ 01 help text.')

    group_10 = parser.add_group(help='Group 10 flags.', mutex=True)
    group_10.add_argument(
        '--abc-10',
        default=True,
        action='store_true',
        help='ABC 10 help text.')
    group_10.add_argument(
        '--xyz-10',
        default=False,
        action='store_true',
        help='XYZ 10 help text.')

    group_11 = parser.add_group(help='Group 11 flags.', mutex=True)
    group_11.add_argument(
        '--abc-11',
        default=True,
        action='store_true',
        help='ABC 11 help text.')
    group_11.add_argument(
        '--xyz-11',
        default=True,
        action='store_true',
        help='XYZ 11 help text.')

    mutex_required_nargs_001 = parser.add_group(
        'Test 001.', mutex=False, required=False)
    mutex_required_nargs_001.add_argument('--abc', help='ABC help text.')

    mutex_required_nargs_011 = parser.add_group(
        'Test 011.', mutex=False, required=True)
    mutex_required_nargs_011.add_argument('--def', help='DEF help text.')

    mutex_required_nargs_101 = parser.add_group(
        'Test 101.', mutex=True, required=False)
    mutex_required_nargs_101.add_argument('--ghi', help='GHI help text.')

    mutex_required_nargs_111 = parser.add_group(
        'Test 111.', mutex=False, required=True)
    mutex_required_nargs_111.add_argument('--jkl', help='JKL help text.')

    mutex_required_nargs_002 = parser.add_group(
        'Test 002.', mutex=False, required=False)
    mutex_required_nargs_002.add_argument('--mno', help='MNO help text.')
    mutex_required_nargs_002.add_argument('--mno-sib',
                                          help='MNO sib help text.')

    mutex_required_nargs_012 = parser.add_group(
        'Test 012.', mutex=False, required=True)
    mutex_required_nargs_012.add_argument('--pqr', help='PQR help text.')
    mutex_required_nargs_012.add_argument('--pqr-sib',
                                          help='PQR sib help text.')

    mutex_required_nargs_102 = parser.add_group(
        'Test 102.', mutex=True, required=False)
    mutex_required_nargs_102.add_argument('--stu', help='STU help text.')
    mutex_required_nargs_102.add_argument('--stu-sib',
                                          help='STU sib help text.')

    mutex_required_nargs_112 = parser.add_group(
        'Test 112.', mutex=False, required=True)
    mutex_required_nargs_112.add_argument('--vwx', help='VWX help text.')
    mutex_required_nargs_112.add_argument('--vwx-sib',
                                          help='VWX sib help text.')

    modal_group = parser.add_group('Modal group test.')
    modal_group.add_argument(
        '--mode', action='store_true', required=True, help='Set the mode.')
    modal_group.add_argument(
        '--optional-value', help='Optional mode value.')
    modal_group.add_argument(
        '--meh', help='Meh if you want.')

  def Run(self, args):
    return {
        'abc-00': args.abc_00,
        'xyz-00': args.xyz_00,
        'abc-01': args.abc_01,
        'xyz-01': args.xyz_01,
        'abc-10': args.abc_10,
        'xyz-10': args.xyz_10,
        'abc-11': args.abc_11,
        'xyz-11': args.xyz_11,
        'vpn-tunnel': args.vpn_tunnel,
        'vpn-tunnel-region': args.vpn_tunnel_region,
        'interconnect-attachment': args.interconnect_attachment,
        'interconnect-attachment-region': args.interconnect_attachment_region,
    }
