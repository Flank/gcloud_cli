# -*- coding: utf-8 -*- #
# Copyright 2016 Google Inc. All Rights Reserved.
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
"""Tests for the ML Versions library."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import os

from googlecloudsdk.api_lib.ml_engine import versions_api
from googlecloudsdk.command_lib.util.args import labels_util
from googlecloudsdk.core import resources
from tests.lib import test_case
from tests.lib.surface.ml_engine import base


class VersionsClientTest(base.MlGaPlatformTestBase):

  def _MakePatchRequest(self, version_ref, version, update_mask):
    return self.msgs.MlProjectsModelsVersionsPatchRequest(
        name=version_ref.RelativeName(),
        googleCloudMlV1Version=version,
        updateMask=','.join(update_mask))

  def SetUp(self):
    self.versions = versions_api.VersionsClient()
    self.version_ref = resources.REGISTRY.Parse(
        'myVersion',
        params={'projectsId': self.Project(), 'modelsId': 'myModel'},
        collection='ml.projects.models.versions')
    self.model_ref = resources.REGISTRY.Parse(
        'myModel', params={'projectsId': self.Project()},
        collection='ml.projects.models')

  def testCreate(self):
    op = self.msgs.GoogleLongrunningOperation(name='opId')
    version = self.short_msgs.Version(
        name='myVersion',
        deploymentUri='gs://path/to/file',
        runtimeVersion='0.12', description='Foo The Bar')
    self.client.projects_models_versions.Create.Expect(
        request=self.versions._MakeCreateRequest(
            parent='projects/{}/models/myModel'.format(self.Project()),
            version=version),
        response=op)
    self.assertEqual(op, self.versions.Create(self.model_ref, version=version))

  def testDelete(self):
    op = self.msgs.GoogleLongrunningOperation(name='opId')
    name = 'projects/{}/models/myModel/versions/myVersion'.format(
        self.Project())
    self.client.projects_models_versions.Delete.Expect(
        request=self.msgs.MlProjectsModelsVersionsDeleteRequest(name=name),
        response=op)
    self.assertEqual(op, self.versions.Delete(self.version_ref))

  def testGet(self):
    version = self.short_msgs.Version(name='versionName')
    name = 'projects/{}/models/myModel/versions/myVersion'.format(
        self.Project())
    self.client.projects_models_versions.Get.Expect(
        request=self.msgs.MlProjectsModelsVersionsGetRequest(name=name),
        response=version)
    self.assertEqual(version, self.versions.Get(self.version_ref))

  def testList(self):
    response_items = [
        self.short_msgs.Version(name='versionName1'),
        self.short_msgs.Version(name='versionName2')
    ]
    self.client.projects_models_versions.List.Expect(
        request=self.msgs.MlProjectsModelsVersionsListRequest(
            parent='projects/{}/models/myModel'.format(self.Project()),
            pageSize=100),
        response=self.short_msgs.ListVersionsResponse(
            versions=response_items))
    self.assertEqual(response_items, list(self.versions.List(self.model_ref)))

  def testPatch(self):
    labels = {'foo': 'bar', 'fizz': 'buzz'}
    updated_description = 'My New Description'
    labels_field = self.short_msgs.Version.LabelsValue(
        additionalProperties=[
            self.short_msgs.Version.LabelsValue.AdditionalProperty(
                key=key, value=value)
            for key, value in sorted(labels.items())])
    version = self.short_msgs.Version(labels=labels_field,
                                      description=updated_description)
    self.client.projects_models_versions.Patch.Expect(
        self._MakePatchRequest(self.version_ref, version,
                               update_mask=['labels', 'description']),
        version)

    label_update = labels_util.UpdateResult(True, labels_field)
    self.assertEqual(version, self.versions.Patch(self.version_ref,
                                                  label_update,
                                                  updated_description))

  def testPatchNoUpdate(self):
    no_label_update = labels_util.UpdateResult(False, None)
    with self.assertRaises(versions_api.NoFieldsSpecifiedError):
      self.versions.Patch(self.version_ref, no_label_update)

  def testSetDefault(self):
    version = self.short_msgs.Version()
    name = 'projects/{}/models/myModel/versions/myVersion'.format(
        self.Project())
    self.client.projects_models_versions.SetDefault.Expect(
        request=self.versions._MakeSetDefaultRequest(name=name),
        response=version)
    self.assertEqual(version, self.versions.SetDefault(self.version_ref))

  def testBuildVersion(self):
    self.assertEqual(
        self.versions.BuildVersion('myVersion'),
        self.short_msgs.Version(name='myVersion'))

  def testBuildVersion_FullySpecified(self):
    self.assertEqual(
        self.versions.BuildVersion('myVersion',
                                   deployment_uri='gs://foo/bar',
                                   runtime_version='0.12'),
        self.short_msgs.Version(name='myVersion',
                                deploymentUri='gs://foo/bar',
                                runtimeVersion='0.12'))

  def testBuildVersion_Yaml(self):
    test_yaml = """
        deploymentUri: gs://baz/qux
        description: spam
        runtimeVersion: '1.0'
        manualScaling:
          nodes: 10
        framework: SCIKIT_LEARN
        pythonVersion: '2.7'
    """
    framework = self.short_msgs.Version.FrameworkValueValuesEnum.SCIKIT_LEARN
    self.assertEqual(
        self.versions.BuildVersion(
            'myVersion',
            path=self.Touch(self.temp_path, 'version.yaml', test_yaml)),
        self.short_msgs.Version(
            name='myVersion',
            deploymentUri='gs://baz/qux',
            description='spam',
            runtimeVersion='1.0',
            manualScaling=self.short_msgs.ManualScaling(nodes=10),
            framework=framework,
            pythonVersion='2.7'))

  def testBuildVersion_YamlOverridden(self):
    test_yaml = """
        deploymentUri: gs://baz/qux
        description: spam
        runtimeVersion: '1.0'
        manualScaling:
          nodes: 10
        framework: SCIKIT_LEARN
        pythonVersion: '2.7'
    """
    self.assertEqual(
        self.versions.BuildVersion(
            'myVersion',
            path=self.Touch(self.temp_path, 'version.yaml', test_yaml),
            deployment_uri='gs://foo/bar',
            runtime_version='0.12',
            python_version='3.6',
            framework=self.short_msgs.Version.FrameworkValueValuesEnum.XGBOOST),
        self.short_msgs.Version(
            name='myVersion',
            deploymentUri='gs://foo/bar',
            runtimeVersion='0.12',
            description='spam',
            manualScaling=self.short_msgs.ManualScaling(nodes=10),
            pythonVersion='3.6',
            framework=self.short_msgs.Version.FrameworkValueValuesEnum.XGBOOST))

  def testBuildVersion_YamlBadConfigFields(self):
    """Tests YAML with valid fields that are not valid in the config file."""
    test_yaml = """
        name: foo
        manualScaling:
          nodes: 10
    """
    with self.assertRaisesRegex(
        versions_api.InvalidVersionConfigFile,
        r'Invalid field \[name\] '
        r'in configuration file \[.*version\.yaml\]\. '
        r'Allowed fields: '
        r'\[autoScaling(, [a-zA-Z]+)+\]'):
      self.versions.BuildVersion(
          'myVersion',
          path=self.Touch(self.temp_path, 'version.yaml', test_yaml))

  def testBuildVersion_YamlInvalidFields(self):
    """Tests YAML with fields that are not ever valid."""
    test_yaml = """
        name: myVersion
        manualScaling:
          nodes: 10
        toaster: true
    """
    with self.assertRaisesRegex(
        versions_api.InvalidVersionConfigFile,
        r'Invalid fields \[name, toaster\] '
        r'in configuration file \[.*version\.yaml\]\. '
        r'Allowed fields: '
        r'\[autoScaling(, [a-zA-Z]+)+\]'):
      self.versions.BuildVersion(
          'myVersion',
          path=self.Touch(self.temp_path, 'version.yaml', test_yaml))

  def testBuildVersion_MissingFile(self):
    """Tests a missing YAML config file."""
    with self.assertRaisesRegex(
        versions_api.InvalidVersionConfigFile,
        r'Could not read Version configuration file \[.*\.yaml\]'):
      self.versions.BuildVersion(
          'myVersion',
          path=os.path.join(self.temp_path, 'missing.yaml'))

  def testBuildVersion_BadYaml(self):
    """Tests invalid YAML in the config file."""
    with self.assertRaisesRegex(
        versions_api.InvalidVersionConfigFile,
        r'Could not read Version configuration file \[.*\.yaml\]'):
      self.versions.BuildVersion(
          'myVersion',
          path=self.Touch(self.temp_path, 'version.yaml', '%'))


if __name__ == '__main__':
  test_case.main()
