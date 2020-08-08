# -*- coding: utf-8 -*- #
# Copyright 2015 Google LLC. All Rights Reserved.
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

"""Tests for the `gcloud meta cache complete` command."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.command_lib.static_completion import lookup
from googlecloudsdk.core import properties
from googlecloudsdk.core.resource import resource_projector
from googlecloudsdk.core.util import files
from tests.lib import completer_test_base
from tests.lib.command_lib.util.concepts import resource_completer_test_base
from tests.lib.surface.cloudiot import base as iot_base
from tests.lib.surface.compute import test_base
from tests.lib.surface.compute.instances import test_resources


class CompleteCommandFlagCompleterTest(test_base.BaseTest,
                                       completer_test_base.FlagCompleterBase):

  def SetUp(self):
    self._clear_io = False
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))

  def Execute(self, command, track=None):
    if self._clear_io:
      self.ClearOutput()
      self.ClearErr()
    else:
      self._clear_io = True
    return self.Run(command, track=track)

  def testCompleteCommand(self):
    self.Execute('meta cache completers run '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter i')
    self.AssertOutputEquals("""\
---
- instance-1 --zone=zone-1
- instance-2 --zone=zone-1
- instance-3 --zone=zone-1
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1 --zone=zone-1
instance-2 --zone=zone-1
instance-3 --zone=zone-1
instance-1 --zone=zone-1
""")

  def testCompleteCommandWithZone(self):
    self.Execute('meta cache completers run '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1 i ')
    self.AssertOutputEquals("""\
---
- instance-1
- instance-2
- instance-3
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1
instance-2
instance-3
instance-1
""")

  def testCompleteCommandWithQualify(self):
    self.Execute('meta cache completers run --qualify=zone '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter i')
    self.AssertOutputEquals("""\
---
- instance-1 --zone=zone-1
- instance-2 --zone=zone-1
- instance-3 --zone=zone-1
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run --qualify=zone '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1 --zone=zone-1
instance-2 --zone=zone-1
instance-3 --zone=zone-1
instance-1 --zone=zone-1
""")

  def testCompleteCommandWithQualifyAndZone(self):
    self.Execute('meta cache completers run --qualify=zone '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1 i')
    self.AssertOutputEquals("""\
---
- instance-1
- instance-2
- instance-3
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run --qualify=zone '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1
instance-2
instance-3
instance-1
""")

  def testCompleteCommandWithStandardFileCompleter(self):
    with files.TemporaryDirectory(change_to=True) as test_dir:
      self.Touch(test_dir, 'abc.dat')
      self.Touch(test_dir, 'x.dat')
      self.Touch(test_dir, 'xyz.dat')
      self.Execute('meta cache completers run '
                   'argcomplete.completers:FilesCompleter x')
    self.AssertOutputNotContains('abc.dat')
    self.AssertOutputContains('x.dat')
    self.AssertOutputContains('xyz.dat')


class CompleteCommandGRICompleterTest(test_base.BaseTest,
                                      completer_test_base.GRICompleterBase):

  def SetUp(self):
    self._clear_io = False
    self.ExpectListerInvoke(
        scope_set=self.MakeAllScopes(zonal=True),
        result=resource_projector.MakeSerializable(test_resources.INSTANCES_V1))

  def Execute(self, command, track=None):
    if self._clear_io:
      self.ClearOutput()
      self.ClearErr()
    else:
      self._clear_io = True
    return self.Run(command, track=track)

  def testCompleteCommand(self):
    self.Execute('meta cache completers run '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter i')
    self.AssertOutputEquals("""\
---
- instance-1:zone-1
- instance-2:zone-1
- instance-3:zone-1
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1:zone-1
instance-2:zone-1
instance-3:zone-1
instance-1:zone-1
""")

  def testCompleteCommandWithZone(self):
    self.Execute('meta cache completers run '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1 i')
    self.AssertOutputEquals("""\
---
- instance-1
- instance-2
- instance-3
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter '
                 '--zone=zone-1')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1
instance-2
instance-3
instance-1
""")

  def testCompleteCommandWithQualify(self):
    self.Execute('meta cache completers run --qualify=zone,collection '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter i')
    self.AssertOutputEquals("""\
---
- instance-1:zone-1::compute.instances
- instance-2:zone-1::compute.instances
- instance-3:zone-1::compute.instances
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run --qualify=zone,collection '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1:zone-1::compute.instances
instance-2:zone-1::compute.instances
instance-3:zone-1::compute.instances
instance-1:zone-1::compute.instances
""")

  def testCompleteCommandWithQualifyAndZone(self):
    self.Execute('meta cache completers run --qualify=collection '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1 i')
    self.AssertOutputEquals("""\
---
- instance-1::compute.instances
- instance-2::compute.instances
- instance-3::compute.instances
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run --qualify=collection '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1::compute.instances
instance-2::compute.instances
instance-3::compute.instances
instance-1::compute.instances
""")

  def testCompleteCommandWithQualifyBothAndZone(self):
    self.Execute('meta cache completers run --qualify=zone,collection '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1 i')
    self.AssertOutputEquals("""\
---
- instance-1:zone-1::compute.instances
- instance-2:zone-1::compute.instances
- instance-3:zone-1::compute.instances
""")

    self.WriteInput('i\n*-1')
    self.Execute('meta cache completers run --qualify=zone,collection '
                 'googlecloudsdk.command_lib.compute.completers:'
                 'InstancesCompleter --zone=zone-1')
    self.AssertErrEquals(
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}'
        '{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\n')
    self.AssertOutputEquals("""\
instance-1:zone-1::compute.instances
instance-2:zone-1::compute.instances
instance-3:zone-1::compute.instances
instance-1:zone-1::compute.instances
""")


class CompleteCommandResourceCompleterFlagTest(
    iot_base.CloudIotRegistryBase,
    iot_base.CloudIotDeviceBase,
    completer_test_base.FlagCompleterBase,
    resource_completer_test_base.ResourceCompleterBase):

  def SetUp(self):
    self.device_spec_path = ('googlecloudsdk.command_lib.iot.resource_args:'
                             'GetDeviceResourceSpec')
    self.resource_completer_path = ('googlecloudsdk.command_lib.util.'
                                    'concepts.completers:CompleterForAttribute')
    self.region_flag = '--region us-central1'

  def testRunDeviceCompleter(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self._ExpectListProjects(['p0', 'p1'])
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', project='p0', registry='r0')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r1'),
                            field_mask='name', project='p0', registry='r1')
    self._ExpectListDevices(self._MakeDevices(n=1, registry='r0'),
                            field_mask='name', project='p1', registry='r0')
    self.WriteInput(' \n')
    self.Run(
        'meta cache completers run --resource-spec-path {} --attribute device '
        '{} {}'.format(self.device_spec_path, self.resource_completer_path,
                       self.region_flag))
    self.AssertOutputEquals("""\
d0 --project=p0 --registry=r0
d1 --project=p0 --registry=r0
d0 --project=p0 --registry=r1
d1 --project=p0 --registry=r1
d0 --project=p1 --registry=r0
""")

  def testRunRegistryCompleterInDeviceResource(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self._ExpectListProjects(['p0', 'p1'])
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self.WriteInput(' \n')
    self.Run(
        'meta cache completers run --resource-spec-path {} '
        '--attribute registry {} {}'.format(
            self.device_spec_path, self.resource_completer_path,
            self.region_flag))
    self.AssertOutputEquals("""\
r0 --project=p0
r1 --project=p0
r0 --project=p1
""")

  def testRunDeviceCompleterWithPresentationKwargs(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self._ExpectListProjects(['p0', 'p1'])
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', project='p0', registry='r0')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r1'),
                            field_mask='name', project='p0', registry='r1')
    self._ExpectListDevices(self._MakeDevices(n=1, registry='r0'),
                            field_mask='name', project='p1', registry='r0')
    self.WriteInput(' \n')
    self.Run(
        'meta cache completers run --resource-spec-path {} '
        '--resource-presentation-kwargs prefixes=True --attribute device {} '
        '--device-region us-central1'.format(
            self.device_spec_path,
            self.resource_completer_path))
    self.AssertOutputEquals("""\
d0 --project=p0 --device-registry=r0
d1 --project=p0 --device-registry=r0
d0 --project=p0 --device-registry=r1
d1 --project=p0 --device-registry=r1
d0 --project=p1 --device-registry=r0
""")

  def testRunDeviceCompleterWithFlagNameOverrides(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self._ExpectListProjects(['p0', 'p1'])
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', project='p0', registry='r0')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r1'),
                            field_mask='name', project='p0', registry='r1')
    self._ExpectListDevices(self._MakeDevices(n=1, registry='r0'),
                            field_mask='name', project='p1', registry='r0')
    self.WriteInput(' \n')
    self.Run(
        'meta cache completers run --resource-spec-path {} --attribute device '
        '--resource-presentation-kwargs flag_name_overrides='
        'project:--funky-project-flag;registry:--registry-flag {} {}'.format(
            self.device_spec_path,
            self.resource_completer_path,
            self.region_flag))
    self.AssertOutputEquals("""\
d0 --funky-project-flag=p0 --registry-flag=r0
d1 --funky-project-flag=p0 --registry-flag=r0
d0 --funky-project-flag=p0 --registry-flag=r1
d1 --funky-project-flag=p0 --registry-flag=r1
d0 --funky-project-flag=p1 --registry-flag=r0
""")


class CompleteCommandResourceCompleterGRITest(
    iot_base.CloudIotRegistryBase,
    iot_base.CloudIotDeviceBase,
    completer_test_base.GRICompleterBase,
    resource_completer_test_base.ResourceCompleterBase):

  def SetUp(self):
    self.device_spec_path = ('googlecloudsdk.command_lib.iot.resource_args:'
                             'GetDeviceResourceSpec')
    self.resource_completer_path = ('googlecloudsdk.command_lib.util.'
                                    'concepts.completers:CompleterForAttribute')
    self.region_flag = '--region us-central1'

  def testRunDeviceCompleter(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self._ExpectListProjects(['p0', 'p1'])
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', project='p0', registry='r0')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r1'),
                            field_mask='name', project='p0', registry='r1')
    self._ExpectListDevices(self._MakeDevices(n=1, registry='r0'),
                            field_mask='name', project='p1', registry='r0')
    self.WriteInput(' \n')
    self.Run(
        'meta cache completers run --resource-spec-path {} --attribute device '
        '{} {}'.format(self.device_spec_path, self.resource_completer_path,
                       self.region_flag))
    self.AssertOutputEquals("""\
d0:r0:us-central1:p0
d1:r0:us-central1:p0
d0:r1:us-central1:p0
d1:r1:us-central1:p0
d0:r0:us-central1:p1
""")

  def testRunRegistryCompleterInDeviceResource(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self._ExpectListProjects(['p0', 'p1'])
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self.WriteInput(' \n')
    self.Run(
        'meta cache completers run --resource-spec-path {} '
        '--attribute registry {} {}'.format(
            self.device_spec_path, self.resource_completer_path,
            self.region_flag))
    self.AssertOutputEquals("""\
r0:us-central1:p0
r1:us-central1:p0
r0:us-central1:p1
""")

  def testRunDeviceCompleterWithPresentationKwargs(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self._ExpectListProjects(['p0', 'p1'])
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', project='p0', registry='r0')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r1'),
                            field_mask='name', project='p0', registry='r1')
    self._ExpectListDevices(self._MakeDevices(n=1, registry='r0'),
                            field_mask='name', project='p1', registry='r0')
    self.WriteInput(' \n')
    self.Run(
        'meta cache completers run --resource-spec-path {} '
        '--resource-presentation-kwargs prefixes=True --attribute device {} '
        '--device-region us-central1'.format(
            self.device_spec_path,
            self.resource_completer_path))
    self.AssertOutputEquals("""\
d0:r0:us-central1:p0
d1:r0:us-central1:p0
d0:r1:us-central1:p0
d1:r1:us-central1:p0
d0:r0:us-central1:p1
""")

  def testRunDeviceCompleterWithFlagNameOverrides(self):
    properties.VALUES.core.project.Set(None)
    properties.PersistProperty(properties.VALUES.core.project, None,
                               properties.Scope.USER)
    self._ExpectListProjects(['p0', 'p1'])
    self._ExpectListRegistries(self._MakeRegistries(n=2, project='p0'),
                               project='p0')
    self._ExpectListRegistries(self._MakeRegistries(n=1, project='p1'),
                               project='p1')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r0'),
                            field_mask='name', project='p0', registry='r0')
    self._ExpectListDevices(self._MakeDevices(n=2, registry='r1'),
                            field_mask='name', project='p0', registry='r1')
    self._ExpectListDevices(self._MakeDevices(n=1, registry='r0'),
                            field_mask='name', project='p1', registry='r0')
    self.WriteInput(' \n')
    self.Run(
        'meta cache completers run --resource-spec-path {} --attribute device '
        '--resource-presentation-kwargs flag_name_overrides='
        'project:--funky-project-flag;registry:--registry-flag {} {}'.format(
            self.device_spec_path,
            self.resource_completer_path,
            self.region_flag))
    self.AssertOutputEquals("""\
d0:r0:us-central1:p0
d1:r0:us-central1:p0
d0:r1:us-central1:p0
d1:r1:us-central1:p0
d0:r0:us-central1:p1
""")


class CompleteCommandRunExceptionTest(test_base.BaseTest,
                                      completer_test_base.FlagCompleterBase):

  def SetUp(self):
    self.StartDictPatch(os.environ)

  def testUpdateNoSuchListCommand(self):
    self.StartObjectPatch(lookup, 'LoadCompletionCliTree',
                          return_value={})
    os.environ['_ARGCOMPLETE_TEST'] = (
        'collection=sql.instances,list_command=no-such-gcloud-command')
    self.WriteInput('x\nx')
    with self.assertRaisesRegex(
        Exception,
        r'Update command \[no-such-gcloud-command --quiet]: Invalid choice: '
        r"'no-such-gcloud-command'\."):
      self.Run('meta cache completers run --stack-trace '
               'googlecloudsdk.command_lib.compute.completers:TestCompleter')
    self.AssertOutputEquals('')

  def testUpdateNoSuchListCommandNoStackTrace(self):
    self.StartObjectPatch(lookup, 'LoadCompletionCliTree',
                          return_value={})
    os.environ['_ARGCOMPLETE_TEST'] = (
        'collection=sql.instances,list_command=no-such-gcloud-command')
    self.WriteInput('x\nx')
    self.Run('meta cache completers run --no-stack-trace '
             'googlecloudsdk.command_lib.compute.completers:TestCompleter')
    self.AssertErrMatches("""\
{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\
ERROR: \\(gcloud\\) Invalid choice: 'no-such-gcloud-command'.
.*
ERROR: Update command \\[no-such-gcloud-command --quiet]: Invalid choice: 'no-such-gcloud-command'.
{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\
ERROR: \\(gcloud\\) Invalid choice: 'no-such-gcloud-command'.
.*
ERROR: Update command \\[no-such-gcloud-command --quiet]: Invalid choice: 'no-such-gcloud-command'.
{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}""")
    self.AssertOutputEquals('')

  def testUpdateListCommandCoreException(self):
    os.environ['_ARGCOMPLETE_TEST'] = (
        'collection=sql.instances,list_command=meta test --core-exception')
    self.WriteInput('x\nx')
    with self.assertRaisesRegex(
        Exception,
        r'Update command \[meta test --core-exception --quiet]: '
        r'Some core exception\.'):
      self.Run('meta cache completers run --stack-trace '
               'googlecloudsdk.command_lib.compute.completers:TestCompleter')
    self.AssertOutputEquals('')

  def testUpdateListCommandCoreExceptionNoStackTrace(self):
    os.environ['_ARGCOMPLETE_TEST'] = (
        'collection=sql.instances,list_command=meta test --core-exception')
    self.WriteInput('x\nx')
    self.Run('meta cache completers run --no-stack-trace '
             'googlecloudsdk.command_lib.compute.completers:TestCompleter')
    self.AssertErrEquals("""\
{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\
ERROR: (gcloud.meta.test) Some core exception.
ERROR: Update command [meta test --core-exception --quiet]: Some core exception.
{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}\
ERROR: (gcloud.meta.test) Some core exception.
ERROR: Update command [meta test --core-exception --quiet]: Some core exception.
{"ux": "PROMPT_RESPONSE", "message": "COMPLETE> "}
""")
    self.AssertOutputEquals('')


if __name__ == '__main__':
  test_base.main()
