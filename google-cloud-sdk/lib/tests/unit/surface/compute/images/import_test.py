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
"""Tests for the images import subcommand."""

import uuid

from apitools.base.py import encoding
from apitools.base.py.testing import mock as client_mocker

from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.core import properties
from googlecloudsdk.core.console import console_io
from googlecloudsdk.core.resources import InvalidResourceException
from tests.lib import e2e_base
from tests.lib import test_case
from tests.lib.surface.compute import test_base


class ImagesCreateTest(e2e_base.WithMockHttp, test_base.BaseTest):

  def SetUp(self):
    self.track = calliope_base.ReleaseTrack.BETA

    self.mocked_cloudbuild_v1 = client_mocker.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'),
    )
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)
    self.cloudbuild_v1_messages = core_apis.GetMessagesModule(
        'cloudbuild', 'v1')

    self.mocked_storage_v1 = client_mocker.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_v1_messages = core_apis.GetMessagesModule(
        'storage', 'v1')

    self.mocked_crm_v1 = client_mocker.Client(
        core_apis.GetClientClass('cloudresourcemanager', 'v1'))
    self.mocked_crm_v1.Mock()
    self.addCleanup(self.mocked_crm_v1.Unmock)
    self.crm_v1_messages = core_apis.GetMessagesModule(
        'cloudresourcemanager', 'v1')

    self.mocked_servicemanagement_v1 = client_mocker.Client(
        core_apis.GetClientClass('servicemanagement', 'v1'))
    self.mocked_servicemanagement_v1.Mock()
    self.addCleanup(self.mocked_servicemanagement_v1.Unmock)
    self.servicemanagement_v1_messages = core_apis.GetMessagesModule(
        'servicemanagement', 'v1')

    self.uuid_mock = self.StartObjectPatch(uuid, 'uuid4')
    self.uuid_mock.return_value = uuid.UUID('12345678123456781234567812345678')

    properties.VALUES.core.project.Set('my-project')
    self._statuses = self.cloudbuild_v1_messages.Build.StatusValueValuesEnum

    self.source_disk = 'gs://31dd/source-image.vmdk'
    self.https_source_disk = ('https://storage.googleapis.com/'
                              '31dd/source-image.vmdk')
    self.local_source_disk = './source-image.vmdk'
    self.source_image = 'my-image'
    self.image_name = self.source_image
    self.destination_image = 'my-translated-image'
    self.copied_source = ('gs://my-project-daisy-bkt/tmpimage/12345678-'
                          '1234-5678-1234-567812345678-source-image.vmdk')
    self.import_workflow = '../workflows/image_import/import_image.wf.json'
    self.daisy_builder = 'gcr.io/compute-image-tools/daisy:release'
    self.daisy_import_step = self.cloudbuild_v1_messages.BuildStep(
        args=['-gcs_path=gs://my-project-daisy-bkt/',
              '-variables=image_name={0},source_disk_file={1}'
              .format(self.image_name, self.copied_source),
              self.import_workflow,],
        name=self.daisy_builder,
    )
    self.daisy_import_and_translate_step = self.cloudbuild_v1_messages.BuildStep(  # pylint: disable=line-too-long
        args=['-gcs_path=gs://my-project-daisy-bkt/',
              ('-variables=image_name={0},'
               'source_disk_file={1},'
               'translate_workflow={2}').format(
                   self.image_name, self.copied_source,
                   'ubuntu/translate_ubuntu_1604.wf.json'),
              '../workflows/image_import/import_and_translate.wf.json'],
        name=self.daisy_builder,
    )

    self.project = self.crm_v1_messages.Project(
        projectId='my-project', projectNumber=123456)
    admin_permissions_binding = self.crm_v1_messages.Binding(
        members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
        role='roles/compute.admin')
    iam_permissions_binding = self.crm_v1_messages.Binding(
        members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
        role='roles/iam.serviceAccountActor')
    self.permissions = self.crm_v1_messages.Policy(
        bindings=[admin_permissions_binding, iam_permissions_binding])
    self.services = self.servicemanagement_v1_messages.ListServicesResponse(
        services=[self.servicemanagement_v1_messages.ManagedService(
            serviceName='cloudbuild.googleapis.com')]
    )

  def testCommonCase(self):
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_and_translate_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_and_translate_step],
        tags=['gce-daisy'],
        status=self._statuses.SUCCESS,
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project-daisy-bkt',
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project-daisy-bkt',
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.Run("""
             compute images import {0}
             --source-file {1} --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

  def testCommonCaseNoTranslate(self):
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_step],
        status=self._statuses.SUCCESS,
        tags=['gce-daisy'],
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project-daisy-bkt',
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project-daisy-bkt',
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    self.Run("""
             compute images import {0}
             --source-file {1}
             --no-translate
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

  def testHttpsLinkToGcsImage(self):
    """Make sure https:// URIs are converted correctly to gs:// ones.

    This test should behave *exactly* like the test above
    (testCommonCaseNoTranslate). gcloud ought to recognize a URI like
    https://storage.googleapis.com/bucket/image.vmdk and translate it to
    gs://bucket/image.vmdk automatically.
    """

    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_step],
        status=self._statuses.SUCCESS,
        tags=['gce-daisy'],
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project-daisy-bkt',
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project-daisy-bkt',
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    self.Run("""
             compute images import {0}
             --source-file {1}
             --no-translate
             """.format(self.image_name, self.https_source_disk))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

  def testNonGcsHttpsUriFails(self):
    """Ensure that only "https://" URLs that point to GCS are accepted."""
    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    with self.assertRaises(InvalidResourceException):
      self.Run("""
               compute images import {0}
               --source-file {1}
               --no-translate
               """.format(self.image_name,
                          'https://example.com/not-a-gcs-bucket/file.vmdk'))

  def testTranslateFromImage(self):
    import_workflow = (
        '../workflows/image_import/ubuntu/translate_ubuntu_1604.wf.json')
    daisy_step = self.cloudbuild_v1_messages.BuildStep(
        args=['-gcs_path=gs://my-project-daisy-bkt/',
              '-variables=image_name={0},source_image=global/images/{1}'
              .format(self.destination_image, self.source_image),
              import_workflow,],
        name=self.daisy_builder,
    )
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[daisy_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[daisy_step],
        status=self._statuses.SUCCESS,
        tags=['gce-daisy'],
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.Run("""
             compute images import --source-image {0}
             --os ubuntu-1604 {1}
             """.format(self.source_image, self.destination_image))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

  def testTranslateWithCustomWorkflow(self):
    import_workflow = (
        '../workflows/image_import/ubuntu/translate_ubuntu_1604.wf.json')
    daisy_step = self.cloudbuild_v1_messages.BuildStep(
        args=['-gcs_path=gs://my-project-daisy-bkt/',
              '-variables=image_name={0},source_image=global/images/{1}'
              .format(self.destination_image, self.source_image),
              import_workflow,],
        name=self.daisy_builder,
    )
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[daisy_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[daisy_step],
        status=self._statuses.SUCCESS,
        tags=['gce-daisy'],
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.Run("""
             compute images import --source-image {0}
             --custom-workflow ubuntu/translate_ubuntu_1604.wf.json
             {1}
             """.format(self.source_image, self.destination_image))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

  def testAsync(self):
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_and_translate_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_and_translate_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project-daisy-bkt',
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project-daisy-bkt',
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    self.Run("""
             compute images import {0}
             --source-file {1} --async
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertErrContains('Created [https://cloudbuild.googleapis.com/'
                           'v1/projects/my-project/builds/1234]')

  def testTimeoutFlag(self):
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_step],
        tags=['gce-daisy'],
        timeout='60s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_step],
        tags=['gce-daisy'],
        status=self._statuses.SUCCESS,
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='60s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project-daisy-bkt',
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project-daisy-bkt',
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    self.Run("""
             compute images import {0}
             --source-file {1} --timeout 1m
             --no-translate
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

  def testLogLocation(self):
    log_location = 'gs://foo/bar'
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_step],
        tags=['gce-daisy'],
        logsBucket=log_location,
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_step],
        tags=['gce-daisy'],
        status=self._statuses.SUCCESS,
        logsBucket=log_location,
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/foo/bar/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project-daisy-bkt',
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project-daisy-bkt',
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    self.Run("""
             compute images import {0}
             --source-file {1} --log-location {2}
             --no-translate
             """.format(self.image_name, self.source_disk, log_location))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

  def testExitOnMissingPermissions(self):
    missing_permissions = self.crm_v1_messages.Policy(
        bindings=[],
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=missing_permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project-daisy-bkt',
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project-daisy-bkt',
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    with self.assertRaises(console_io.UnattendedPromptError):
      self.Run("""
               compute images import {0}
               --source-file {1} --os ubuntu-1604
               """.format(self.image_name, self.source_disk))

  def testAddMissingPermissions(self):
    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_and_translate_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_and_translate_step],
        tags=['gce-daisy'],
        status=self._statuses.SUCCESS,
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    admin_permissions_binding = self.crm_v1_messages.Binding(
        members=['serviceAccount:123456@cloudbuild.gserviceaccount.com'],
        role='roles/compute.admin',
    )

    missing_permissions = self.crm_v1_messages.Policy(
        bindings=[admin_permissions_binding],
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=missing_permissions,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_crm_v1.projects.SetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsSetIamPolicyRequest(
            resource='my-project',
            setIamPolicyRequest=self.crm_v1_messages.SetIamPolicyRequest(
                policy=self.permissions,
            ),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.mocked_storage_v1.objects.Rewrite.Expect(
        self.storage_v1_messages.StorageObjectsRewriteRequest(
            destinationBucket='my-project-daisy-bkt',
            destinationObject=('tmpimage/12345678-1234-5678-1234-567812345678'
                               '-source-image.vmdk'),
            sourceBucket='31dd',
            sourceObject='source-image.vmdk',
        ),
        response=self.storage_v1_messages.RewriteResponse(
            resource=self.storage_v1_messages.Object(
                bucket='my-project-daisy-bkt',
                name='source-image.vmdk',
                generation=123,
            ),
            done=True,
        ),
    )

    self.Run("""
             compute images import {0}
             --source-file {1} --quiet
             --os ubuntu-1604
             """.format(self.image_name, self.source_disk))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

  def testUploadLocalFile(self):
    mocked_run_gsutil_command = self.StartPatch(
        'googlecloudsdk.api_lib.storage.storage_util.RunGsutilCommand')

    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_step],
        status=self._statuses.SUCCESS,
        tags=['gce-daisy'],
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    self.Run("""
             compute images import {0}
             --source-file {1}
             --no-translate
             """.format(self.image_name, self.local_source_disk))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

    # Expect exactly one call to "gsutil cp <local file> <GCS URI>".
    mocked_run_gsutil_command.assert_called_once_with(
        'cp', [self.local_source_disk, self.copied_source])

  def testUploadLocalFileWithSpacesInPath(self):
    """The same as the last test, except with spaces in the file path."""
    mocked_run_gsutil_command = self.StartPatch(
        'googlecloudsdk.api_lib.storage.storage_util.RunGsutilCommand')

    buildin = self.cloudbuild_v1_messages.Build(
        steps=[self.daisy_import_step],
        tags=['gce-daisy'],
        timeout='7200s',
    )

    buildout = self.cloudbuild_v1_messages.Build(
        id='1234',
        projectId='my-project',
        steps=[self.daisy_import_step],
        status=self._statuses.SUCCESS,
        tags=['gce-daisy'],
        logsBucket='gs://my-project_cloudbuild/logs',
        timeout='7200s',
    )
    op_metadata = self.cloudbuild_v1_messages.BuildOperationMetadata(
        build=buildout,
    )

    self.AddHTTPResponse(
        'https://storage.googleapis.com/my-project_cloudbuild/'
        'logs/log-1234.txt',
        request_headers={'Range': 'bytes=0-'}, status=200,
        body='Here is some streamed\ndata for you to print\n')

    self.mocked_cloudbuild_v1.projects_builds.Create.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsCreateRequest(
            build=buildin,
            projectId='my-project',
        ),
        response=self.cloudbuild_v1_messages.Operation(
            metadata=encoding.JsonToMessage(
                self.cloudbuild_v1_messages.Operation.MetadataValue,
                encoding.MessageToJson(op_metadata)))
    )

    self.mocked_cloudbuild_v1.projects_builds.Get.Expect(
        self.cloudbuild_v1_messages.CloudbuildProjectsBuildsGetRequest(
            id='1234',
            projectId='my-project',
        ),
        response=buildout,
    )

    self.mocked_crm_v1.projects.Get.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetRequest(
            projectId='my-project',
        ),
        response=self.project,
    )

    self.mocked_servicemanagement_v1.services.List.Expect(
        self.servicemanagement_v1_messages.ServicemanagementServicesListRequest(
            consumerId='project:my-project',
            pageSize=100,
        ),
        response=self.services,
    )

    self.mocked_crm_v1.projects.GetIamPolicy.Expect(
        self.crm_v1_messages.CloudresourcemanagerProjectsGetIamPolicyRequest(
            resource='my-project',
            getIamPolicyRequest=self.crm_v1_messages.GetIamPolicyRequest(),
        ),
        response=self.permissions,
    )

    self.mocked_storage_v1.buckets.Insert.Expect(
        self.storage_v1_messages.StorageBucketsInsertRequest(
            bucket=self.storage_v1_messages.Bucket(
                name='my-project-daisy-bkt'),
            project='my-project',
        ),
        response='foo',
    )

    path_with_spaces = './my cool directory/source image.vmdk'
    self.Run("""
             compute images import {0}
             --source-file "{1}"
             --no-translate
             """.format(self.image_name, path_with_spaces))

    self.AssertOutputContains("""\
        Here is some streamed
        data for you to print
        """, normalize_space=True)

    # Expect exactly one call to "gsutil cp <local file> <GCS URI>".
    mocked_run_gsutil_command.assert_called_once_with(
        'cp', [path_with_spaces, self.copied_source])

  def testMissingSource(self):
    with self.AssertRaisesArgumentErrorMatches(
        'Exactly one of (--source-file | --source-image) must be specified.'):
      self.Run("""
               compute images import {0} --os ubuntu-1604
               """.format(self.destination_image))

  def testMissingNoTranslateOrOsFlags(self):
    with self.AssertRaisesArgumentErrorMatches(
        ('Exactly one of (--custom-workflow | --os | --no-translate) '
         'must be specified.')):
      self.Run("""
               compute images import --source-file {0} {1}
               """.format(self.source_image, self.destination_image))

if __name__ == '__main__':
  test_case.main()
