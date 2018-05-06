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

"""Tests for the `gcloud meta cache list` command."""
from googlecloudsdk.api_lib.compute import lister
from googlecloudsdk.command_lib.meta import cache_util
from googlecloudsdk.core.resource import resource_projector
from tests.lib import completer_test_base
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute import test_resources


class ListCommandTest(test_base.BaseTest, completer_test_base.CompleterBase):

  def SetUp(self):
    self.resources = [
        instance.selfLink for instance in test_resources.INSTANCES_V1]

  def testListCommandListCompleter(self):
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))
    self.Run('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:InstancesCompleter '
             '--format=none --project=my-project --zone=zone-1 '
             '--verbosity=info i')
    self.AssertErrContains("""\
resource.cache
INFO: cache collection=compute.instances api_version=v1 params=[u'project', u'zone', u'instance']
INFO: cache template=['*', '*', 'i*']
INFO: cache parameter=project column=0 value=my-project aggregate=True
INFO: cache parameter=zone column=1 value=zone-1 aggregate=False
INFO: cache table=compute.instances.my-project aggregations=[project=my-project zone=zone-1]
INFO: cache update command: compute instances list --uri --quiet --format=disable --project=my-project
INFO: cache collection=compute.instances api_version=v1 params=[u'project', u'zone', u'instance']
INFO: cache rows=[(u'my-project', u'zone-1', u'instance-1'), (u'my-project', u'zone-1', u'instance-2'), (u'my-project', u'zone-1', u'instance-3')]
INFO: Display format: "default none"
""")

    self.ClearErr()
    self.StartObjectPatch(
        lister, 'GetGlobalResourcesDicts', return_value=[])
    self.Run('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:ZonesCompleter '
             '--format=none --verbosity=info i')
    self.AssertErrContains("""\
resource.cache
INFO: cache collection=compute.zones api_version=v1 params=[u'project', u'zone']
INFO: cache template=['*', 'i*']
INFO: cache parameter=project column=0 value=my-project aggregate=True
INFO: cache table=compute.zones.my-project aggregations=[project=my-project]
INFO: cache update command: compute zones list --uri --quiet --format=disable
INFO: cache collection=compute.zones api_version=v1 params=[u'project', u'zone']
INFO: cache rows=[]
INFO: Display format: "default none"
""")

    self.ClearOutput()
    self.Run('meta cache list')
    self.AssertOutputEquals("""\
+------------------------------+-----+-----+---------+---------+
|             NAME             | COL | KEY | TIMEOUT | EXPIRED |
+------------------------------+-----+-----+---------+---------+
| compute.instances.my-project | 3   | 3   | 3600    | False   |
| compute.zones.my-project     | 2   | 2   | 28800   | False   |
+------------------------------+-----+-----+---------+---------+
""")

    self.ClearOutput()
    self.Run('meta cache list --format=value(name)')
    self.AssertOutputEquals('compute.instances.my-project\n'
                            'compute.zones.my-project\n')

    self.ClearOutput()
    self.Run('meta cache list --format=value(name) --cache=resource://')
    self.AssertOutputEquals('compute.instances.my-project\n'
                            'compute.zones.my-project\n')

    self.ClearOutput()
    self.Run('meta cache list --format=value(name) --cache=')
    self.AssertOutputEquals('compute.instances.my-project\n'
                            'compute.zones.my-project\n')

    with self.AssertRaisesExceptionMatches(
        cache_util.NoTablesMatched,
        'No tables matched [instances.compute].'):
      self.Run('meta cache list instances.compute')

    self.ClearOutput()
    self.Run('meta cache list --format=json compute.instances.*')
    self.AssertOutputEquals("""\
[
  {
    "data": [
      [
        "my-project",
        "zone-1",
        "instance-1"
      ],
      [
        "my-project",
        "zone-1",
        "instance-2"
      ],
      [
        "my-project",
        "zone-1",
        "instance-3"
      ]
    ],
    "name": "compute.instances.my-project"
  }
]
""")

  def testListCommandSearchCompleter(self):
    self.Resources(search_resources={'compute.instances': self.resources})
    self.Run('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:'
             'SearchInstancesCompleter '
             '--format=none --zone=zone-1 --verbosity=info i')
    self.AssertErrContains("""\
resource.cache
INFO: cache collection=compute.instances api_version=v1 params=[u'project', u'zone', u'instance']
INFO: cache template=['*', '*', 'i*']
INFO: cache parameter=zone column=1 value=zone-1 aggregate=None
INFO: cache table=compute.instances aggregations=[zone=zone-1]
INFO: cloud resource search query: @type:compute.instances
INFO: cache rows=[(u'my-project', u'zone-1', u'instance-1'), (u'my-project', u'zone-1', u'instance-2'), (u'my-project', u'zone-1', u'instance-3')]
INFO: Display format: "default none"
""")

    self.ClearErr()
    self.StartObjectPatch(
        lister, 'GetGlobalResourcesDicts', return_value=[])
    self.Run('meta cache completers run '
             'googlecloudsdk.command_lib.compute.completers:ZonesCompleter '
             '--format=none --verbosity=info i')
    self.AssertErrContains("""\
resource.cache
INFO: cache collection=compute.zones api_version=v1 params=[u'project', u'zone']
INFO: cache template=['*', 'i*']
INFO: cache parameter=project column=0 value=my-project aggregate=True
INFO: cache table=compute.zones.my-project aggregations=[project=my-project]
INFO: cache update command: compute zones list --uri --quiet --format=disable
INFO: cache collection=compute.zones api_version=v1 params=[u'project', u'zone']
INFO: cache rows=[]
INFO: Display format: "default none"
""")

    self.ClearOutput()
    self.Run('meta cache list')
    self.AssertOutputEquals("""\
+--------------------------+-----+-----+---------+---------+
|           NAME           | COL | KEY | TIMEOUT | EXPIRED |
+--------------------------+-----+-----+---------+---------+
| compute.instances        | 3   | 3   | 3600    | False   |
| compute.zones.my-project | 2   | 2   | 28800   | False   |
+--------------------------+-----+-----+---------+---------+
""")

    with self.AssertRaisesExceptionMatches(
        cache_util.NoTablesMatched,
        'No tables matched [instances.compute].'):
      self.Run('meta cache list instances.compute')

    self.ClearOutput()
    self.Run('meta cache list --format=json compute.instances')
    self.AssertOutputEquals("""\
[
  {
    "data": [
      [
        "my-project",
        "zone-1",
        "instance-1"
      ],
      [
        "my-project",
        "zone-1",
        "instance-2"
      ],
      [
        "my-project",
        "zone-1",
        "instance-3"
      ]
    ],
    "name": "compute.instances"
  }
]
""")


if __name__ == '__main__':
  test_base.main()
