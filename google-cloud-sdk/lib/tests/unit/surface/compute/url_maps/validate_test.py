# -*- coding: utf-8 -*- #
# Copyright 2020 Google LLC. All Rights Reserved.
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
"""Tests for the url-maps validate subcommand."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk import calliope
from googlecloudsdk.command_lib.export import util as export_util
from googlecloudsdk.core import exceptions
from googlecloudsdk.core import yaml
from googlecloudsdk.core.util import files
from tests.lib import test_case
from tests.lib.surface.compute.url_maps import test_base


class UrlMapsValidateTestAlpha(test_base.UrlMapsTestBase):

  def PreSetUp(self):
    self.track = calliope.base.ReleaseTrack.ALPHA
    self._api = 'alpha'

  def RunValidateCommand(self, command):
    self.Run('compute url-maps validate ' + command)

  def _MakeUrlMapHostRules(self):
    return [self.messages.HostRule(hosts=['*'], pathMatcher='matcher-1')]

  def _MakeUrlMapPathMatchers(self):
    return [
        self.messages.PathMatcher(
            name='matcher-1',
            defaultService=self.MakeDefaultService(self._api),
            pathRules=[
                self.messages.PathRule(
                    paths=['/a/*'],
                    service=self.MakeService(self._api, 'service-a')),
                self.messages.PathRule(
                    paths=['/b/*'],
                    service=self.MakeService(self._api, 'service-b'))
            ])
    ]

  def _MakeUrlMapWrongPathMatchers(self):
    return [
        self.messages.PathMatcher(
            name='matcher-1',
            defaultService=self.MakeDefaultService(self._api),
            pathRules=[
                self.messages.PathRule(
                    paths=['/b/*'],
                    service=self.MakeService(self._api, 'service-a')),
                self.messages.PathRule(
                    paths=['/a/*'],
                    service=self.MakeService(self._api, 'service-b'))
            ])
    ]

  def _MakeUrlMapTests(self):
    return [
        self.messages.UrlMapTest(
            description='Routing to Service-A',
            host='google.com',
            path='/a/some_path',
            service=self.MakeService(self._api, 'service-a')),
        self.messages.UrlMapTest(
            description='Routing to Service-B',
            host='google.com',
            path='/b/some_other_path',
            service=self.MakeService(self._api, 'service-b'))
    ]

  def _MakeUrlMap(self):
    url_map = self.MakeTestUrlMap(self.messages, self._api)
    url_map.hostRules = self._MakeUrlMapHostRules()
    url_map.pathMatchers = self._MakeUrlMapPathMatchers()
    url_map.tests = self._MakeUrlMapTests()
    return url_map

  def _MakeWrongUrlMap(self):
    url_map = self.MakeTestUrlMap(self.messages, self._api)
    url_map.hostRules = self._MakeUrlMapHostRules()
    url_map.pathMatchers = self._MakeUrlMapWrongPathMatchers()
    url_map.tests = self._MakeUrlMapTests()
    return url_map

  def _ExportUrlMap(self, url_map):
    file_name = os.path.join(self.temp_path, 'temp-url-map.yaml')
    with files.FileWriter(file_name) as stream:
      export_util.Export(message=url_map, stream=stream)
    return file_name

  def testPassSimpleValidation(self):
    url_map = self._MakeUrlMap()
    file_name = self._ExportUrlMap(url_map)

    # Expect success
    self.ExpectGlobalValidateRequest(
        project=self.Project(),
        url_map=url_map,
        expected_response=self.messages.UrlMapsValidateResponse(
            result=self.messages.UrlMapValidationResult(
                loadSucceeded=True, testPassed=True)))
    self.RunValidateCommand('--source={0}'.format(file_name))

  def testPassSimpleValidationWithGlobalFlag(self):
    url_map = self._MakeUrlMap()
    file_name = self._ExportUrlMap(url_map)

    # Expect success with global request
    self.ExpectGlobalValidateRequest(
        project=self.Project(),
        url_map=url_map,
        expected_response=self.messages.UrlMapsValidateResponse(
            result=self.messages.UrlMapValidationResult(
                loadSucceeded=True, testPassed=True)))
    self.RunValidateCommand('--source={0} --global'.format(file_name))

  def testPassSimpleValidationWithRegionFlag(self):
    url_map = self._MakeUrlMap()
    file_name = self._ExportUrlMap(url_map)
    region = 'us-central1'

    # Expect success with regional request
    self.ExpectRegionValidateRequest(
        project=self.Project(),
        region=region,
        url_map=url_map,
        expected_response=self.messages.UrlMapsValidateResponse(
            result=self.messages.UrlMapValidationResult(
                loadSucceeded=True, testPassed=True)))
    self.RunValidateCommand('--source={0} --region={1}'.format(
        file_name, region))

  def testFailSimpleValidation(self):
    url_map = self._MakeWrongUrlMap()
    file_name = self._ExportUrlMap(url_map)

    # Expect validation failure
    self.ExpectGlobalValidateRequest(
        project=self.Project(),
        url_map=url_map,
        expected_response=self.messages.UrlMapsValidateResponse(
            result=self.messages.UrlMapValidationResult(
                loadSucceeded=True,
                testPassed=False,
                testFailures=[
                    self.messages.TestFailure(
                        host='google.com',
                        path='/a/some_path',
                        expectedService=self.MakeService(
                            self._api, 'service-a'),
                        actualService=self.MakeService(self._api, 'service-b')),
                    self.messages.TestFailure(
                        host='google.com',
                        path='/b/some_other_path',
                        expectedService=self.MakeService(
                            self._api, 'service-b'),
                        actualService=self.MakeService(self._api, 'service-a'))
                ])))
    self.RunValidateCommand('--source={0}'.format(file_name))

  def testNotExistingFile(self):
    file_name = os.path.join(self.temp_path, 'not_existing-file.yaml')
    with self.AssertRaisesExceptionMatches(
        files.MissingFileError, 'Unable to read file [{0}]'.format(file_name)):
      self.RunValidateCommand('--source={0}'.format(file_name))

  def testImportInvalidSchema(self):
    # This test ensures that the schema files do not contain invalid fields.
    url_map = self.MakeTestUrlMap(self.messages, self._api)

    # id and fingerprint fields should be removed from schema files manually.
    url_map.id = 12345

    # Write the URL Map to a temporary file.
    file_name = self._ExportUrlMap(url_map)

    with self.AssertRaisesExceptionMatches(
        exceptions.Error, 'Additional properties are not allowed '
        "('id' was unexpected)"):
      self.RunValidateCommand('--source {0}'.format(file_name))

  def testNoYamlFile(self):
    # Write some Java class to the temp file
    file_name = os.path.join(self.temp_path, 'MyClass.java')
    with files.FileWriter(file_name) as stream:
      stream.write('package myPackage;\n')
      stream.write('public class MyClass {\n')
      stream.write('  public static void foo(Collection c) {\n')
      stream.write('    for (Object obj : c) {}\n')
      stream.write('  }\n')
      stream.write('}\n')
      stream.flush()
      stream.close()

    with self.AssertRaisesExceptionMatches(yaml.YAMLParseError,
                                           'Failed to parse YAML'):
      self.RunValidateCommand('--source {0}'.format(file_name))

  def testSourceRequired(self):
    with self.AssertRaisesArgumentErrorMatches(
        'argument --source: Must be specified.'):
      self.RunValidateCommand('')

  def testRegionGlobalFlagsMutuallyExclusive(self):
    url_map = self._MakeUrlMap()
    file_name = self._ExportUrlMap(url_map)

    with self.AssertRaisesArgumentErrorMatches(
        'argument --global: At most one of --global | --region '
        'may be specified'):
      self.RunValidateCommand(
          '--region us-central1 --global --source {0}'.format(file_name))


if __name__ == '__main__':
  test_case.main()
