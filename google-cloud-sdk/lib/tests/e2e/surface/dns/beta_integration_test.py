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

"""Integration tests for the 'gcloud dns' commands."""

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from tests.lib import e2e_utils
from tests.lib import test_case
from tests.lib.surface.dns import base


class ProjectInfoTest(base.DnsTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

  def testDescribe(self):
    self.Run(
        'dns project-info describe {0}'.format(self.Project()))
    self.AssertOutputContains("""\
id: {0}
kind: dns#project
""".format(self.Project()))


class ManagedZonesTest(base.DnsTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA
    messages = core_apis.GetMessagesModule('dns', self.beta_version)
    self.test_zone = messages.ManagedZone(
        description=u'Zone!',
        dnsName=unicode(
            # Random name generation that ends in .com.
            # Example: kvtqfsqro8mo5.com.
            e2e_utils.GetResourceNameGenerator(suffix='.com.',
                                               hash_len=13,
                                               delimiter='',
                                               timestamp_format=None).next()),
        kind=u'dns#managedZone',
        name=unicode(e2e_utils.GetResourceNameGenerator(prefix='zone').next()),
        nameServers=[])

    self.Run((
        'dns managed-zones create {0}'
        ' --dns-name {1} --labels foo=bar --description {2}').format(
            self.test_zone.name,
            self.test_zone.dnsName,
            self.test_zone.description))
    self.AssertErrContains("""\
Created [https://www.googleapis.com/dns/{2}/projects/{0}/managedZones/{1}].
""".format(self.Project(), self.test_zone.name, self.beta_version))

  def TearDown(self):
    self.Run('dns managed-zones delete {0}'.format(self.test_zone.name))
    self.AssertErrContains("""\
Deleted [https://www.googleapis.com/dns/{2}/projects/{0}/managedZones/{1}].
""".format(self.Project(), self.test_zone.name, self.beta_version))

  def testList(self):
    self.Run('dns managed-zones list')
    self.AssertOutputContains("""\
{0} {1} Zone!
""".format(self.test_zone.name, self.test_zone.dnsName), normalize_space=True)

  def testDescribe(self):
    self.Run('dns managed-zones describe {0}'.format(self.test_zone.name))
    self.AssertOutputContains("""\
description: Zone!
dnsName: {0}
""".format(self.test_zone.dnsName))
    self.AssertOutputContains("""\
labels:
  foo: bar
""")
    self.AssertOutputContains("""\
kind: dns#managedZone
""")
    self.AssertOutputContains("""\
name: {0}
nameServers:
""".format(self.test_zone.name))


if __name__ == '__main__':
  test_case.main()
