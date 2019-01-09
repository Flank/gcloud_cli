# -*- coding: utf-8 -*- #
# Copyright 2018 Google Inc. All Rights Reserved.
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
"""Unit tests for the `gcloud compute instances get-shielded-vm-identity`."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import textwrap

from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.compute import flags as compute_flags
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class GetShieldedVmIdentityTest(test_base.BaseTest):

  def ApiVersion(self):
    return 'alpha'

  def ReleaseTrack(self):
    return base.ReleaseTrack.ALPHA

  def SetUp(self):
    self.track = self.ReleaseTrack()
    self.SelectApi(self.ApiVersion())

  def testShieldedVmIdentitySuccessfullyReturned(self):
    m = self.messages
    self.make_requests.side_effect = iter([
        [
            m.ShieldedVmIdentity(
                encryptionKey=m.ShieldedVmIdentityEntry(
                    ekCert='ENC-CERT',
                    ekPub='ENC-PUB'),
                kind='compute#shieldedVmIdentity',
                signingKey=m.ShieldedVmIdentityEntry(
                    ekCert='SIGN-CERT',
                    ekPub='SIGN-PUB'),
            ),
        ],
        []
    ])

    self.Run("""
        compute instances get-shielded-vm-identity --zone=central2-a instance-1
        """)

    self.CheckRequests([
        (self.compute.instances,
         'GetShieldedVmIdentity',
         m.ComputeInstancesGetShieldedVmIdentityRequest(
             instance='instance-1',
             project=self.Project(),
             zone='central2-a')),
    ])

    self.AssertOutputEquals(
        textwrap.dedent("""\
            encryptionKey:
            ekCert: ENC-CERT
            ekPub: ENC-PUB
            kind: compute#shieldedVmIdentity
            signingKey:
            ekCert: SIGN-CERT
            ekPub: SIGN-PUB
            """), normalize_space=True)

  def testNonExistingInstanceIdentityFails(self):
    m = self.messages
    def MakeRequests(*_, **kwargs):
      if kwargs['requests'][0][0] == self.compute.zones:
        yield m.Zone(name='central2-a')
      else:
        kwargs['errors'].append((404, 'Not Found'))

    self.make_requests.side_effect = MakeRequests

    with self.AssertRaisesToolExceptionRegexp(
        textwrap.dedent("""\
        Could not get ShieldedVm identity:
         - Not Found
        """)):
      self.Run("""
          compute instances get-shielded-vm-identity --zone=central2-a instance-1
          """)

    self.CheckRequests([
        (self.compute.instances,
         'GetShieldedVmIdentity',
         self.messages.ComputeInstancesGetShieldedVmIdentityRequest(
             instance='instance-1',
             project=self.Project(),
             zone='central2-a')),
    ])

  def testUnspecifiedInstanceFails(self):
    with self.assertRaisesRegex(
        compute_flags.UnderSpecifiedResourceError,
        r'Underspecified resource \[unknown-instance\]. '
        r'Specify the \[--zone\] flag.'):
      self.Run("""
          compute instances get-shielded-vm-identity unknown-instance
          """)
    self.CheckRequests()


if __name__ == '__main__':
  test_case.main()
