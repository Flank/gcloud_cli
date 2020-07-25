# -*- coding: utf-8 -*- #
# Copyright 2019 Google LLC. All Rights Reserved.
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
"""Tests for google3.third_party.py.tests.unit.surface.builds.deploy.configure.gke."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import copy
import os.path
import uuid

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.cloudbuild import cloudbuild_util
from googlecloudsdk.api_lib.util import apis as core_apis
from googlecloudsdk.calliope import base as calliope_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.builds.deploy import build_util
from googlecloudsdk.core import exceptions as core_exceptions
from googlecloudsdk.core import properties
from googlecloudsdk.core.util import times
from surface.builds.deploy.configure import gke
from tests.lib import e2e_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.apitools import http_error


class ConfigureGKEDeployTestAlpha(e2e_base.WithMockHttp,
                                  sdk_test_base.WithFakeAuth,
                                  sdk_test_base.WithTempCWD):

  def PreSetUp(self):
    self.track = calliope_base.ReleaseTrack.ALPHA

  def SetUp(self):
    properties.VALUES.core.project.Set('my-project')
    self.StartPatch('time.sleep')  # To speed up tests with polling

    self.mocked_cloudbuild_v1 = mock.Client(
        core_apis.GetClientClass('cloudbuild', 'v1'))
    self.mocked_cloudbuild_v1.Mock()
    self.addCleanup(self.mocked_cloudbuild_v1.Unmock)
    self.build_msg = core_apis.GetMessagesModule('cloudbuild', 'v1')
    self._step_statuses = self.build_msg.BuildStep.StatusValueValuesEnum
    self._statuses = self.build_msg.Build.StatusValueValuesEnum
    self._sub_options = self.build_msg.BuildOptions.SubstitutionOptionValueValuesEnum

    self.mocked_container_v1 = mock.Client(
        core_apis.GetClientClass('container', 'v1')
    )
    self.mocked_container_v1.Mock()
    self.addCleanup(self.mocked_container_v1.Unmock)
    self.container_msg = core_apis.GetMessagesModule('container', 'v1')

    self.mocked_sourcerepo_v1 = mock.Client(
        core_apis.GetClientClass('sourcerepo', 'v1')
    )
    self.mocked_sourcerepo_v1.Mock()
    self.addCleanup(self.mocked_sourcerepo_v1.Unmock)
    self.sourcerepo_msg = core_apis.GetMessagesModule('sourcerepo', 'v1')

    self.mocked_storage_v1 = mock.Client(
        core_apis.GetClientClass('storage', 'v1'))
    self.mocked_storage_v1.Mock()
    self.addCleanup(self.mocked_storage_v1.Unmock)
    self.storage_msg = core_apis.GetMessagesModule('storage', 'v1')

    self.mocked_scheduler_v1 = mock.Client(
        core_apis.GetClientClass('cloudscheduler', 'v1'))
    self.mocked_scheduler_v1.Mock()
    self.addCleanup(self.mocked_scheduler_v1.Unmock)
    self.scheduler_msg = core_apis.GetMessagesModule('cloudscheduler', 'v1')

    self.frozen_time = '2019-07-29T00:05:00.000000Z'
    frozen_time = times.ParseDateTime(self.frozen_time)
    frozen_uuid = uuid.uuid4()
    self.frozen_tgz_filename = '{frozen_time}-{frozen_uuid}.tgz'.format(
        frozen_time=times.GetTimeStampFromDateTime(frozen_time),
        frozen_uuid=frozen_uuid.hex)
    self.frozen_tgz_filepath = 'deploy/source/{}'.format(
        self.frozen_tgz_filename)
    self.StartObjectPatch(times, 'Now', return_value=frozen_time)
    self.StartObjectPatch(uuid, 'uuid4', return_value=frozen_uuid)
    self.StartObjectPatch(os.path, 'getsize', return_value=100)

  def ExpectInitialMessagesForConfigure(
      self, repo_type='github', repo_owner='test-owner', repo_name='test-repo',
      cluster='test-cluster', location='us-central1',
      bucket_name_override=None):
    if repo_type != 'github':
      repo = self.sourcerepo_msg.Repo()
      csr_repo_name = repo_name
      if repo_type == 'bitbucket_mirrored':
        csr_repo_name = 'bitbucket_{}_{}'.format(repo_owner, repo_name)
        repo.mirrorConfig = self.sourcerepo_msg.MirrorConfig(
            url='https://bitbucket.org/{}/{}.git'.format(repo_owner, repo_name))
      elif repo_type == 'github_mirrored':
        csr_repo_name = 'github_{}_{}'.format(repo_owner, repo_name)
        repo.mirrorConfig = self.sourcerepo_msg.MirrorConfig(
            url='https://github.com/{}/{}'.format(repo_owner, repo_name))
      sourcerepo_name = 'projects/my-project/repos/{csr_repo_name}'.format(
          csr_repo_name=csr_repo_name)
      self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
          self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
              name=sourcerepo_name),
          response=repo)

    cluster_name = 'projects/my-project/locations/{location}/clusters/{cluster}'.format(
        location=location, cluster=cluster)
    self.mocked_container_v1.projects_locations_clusters.Get.Expect(
        self.container_msg.ContainerProjectsLocationsClustersGetRequest(
            name=cluster_name),
        response=self.container_msg.Cluster(
            name=cluster_name,
            status=self.container_msg.Cluster.StatusValueValuesEnum.RUNNING))

    if bucket_name_override:
      bucket_name = bucket_name_override
    else:
      bucket_name = 'my-project_cloudbuild'
    b = self.storage_msg.Bucket(id=bucket_name)
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    if bucket_name_override is None:
      self.mocked_storage_v1.buckets.List.Expect(
          self.storage_msg.StorageBucketsListRequest(
              project='my-project',
              prefix=b.id),
          response=self.storage_msg.Buckets(items=[b]))

  def ExpectMessagesForTriggerDoesNotExist(self, bt_name, bt_create,
                                           bt_create_resp, bt_patch=None,
                                           bt_patch_resp=None):
    self.mocked_cloudbuild_v1.projects_triggers.Get.Expect(
        self.build_msg.CloudbuildProjectsTriggersGetRequest(
            projectId='my-project',
            triggerId=bt_name),
        exception=http_error.MakeHttpError(404, 'not found'))
    self.mocked_cloudbuild_v1.projects_triggers.Create.Expect(
        self.build_msg.CloudbuildProjectsTriggersCreateRequest(
            buildTrigger=bt_create,
            projectId='my-project'),
        response=bt_create_resp)
    if bt_patch and bt_patch_resp:
      self.mocked_cloudbuild_v1.projects_triggers.Patch.Expect(
          self.build_msg.CloudbuildProjectsTriggersPatchRequest(
              buildTrigger=bt_patch,
              projectId='my-project',
              triggerId=bt_create_resp.id),
          response=bt_patch_resp)

  def ExpectMessagesForTriggerExists(self, bt_name, bt_get_resp, bt_patch,
                                     bt_patch_resp):
    self.mocked_cloudbuild_v1.projects_triggers.Get.Expect(
        self.build_msg.CloudbuildProjectsTriggersGetRequest(
            projectId='my-project',
            triggerId=bt_name),
        response=bt_get_resp)
    self.mocked_cloudbuild_v1.projects_triggers.Patch.Expect(
        self.build_msg.CloudbuildProjectsTriggersPatchRequest(
            buildTrigger=bt_patch,
            projectId='my-project',
            triggerId=bt_get_resp.id),
        response=bt_patch_resp)

  def ExpectMessagesForJobDoesNotExist(self, cp_job_id, cp_job_create):
    self.mocked_scheduler_v1.projects_locations_jobs.Get.Expect(
        self.scheduler_msg.CloudschedulerProjectsLocationsJobsGetRequest(
            name='projects/my-project/locations/us-east1/jobs/' + cp_job_id),
        exception=http_error.MakeHttpError(404, 'not found'))
    self.mocked_scheduler_v1.projects_locations_jobs.Create.Expect(
        self.scheduler_msg.CloudschedulerProjectsLocationsJobsCreateRequest(
            parent='projects/my-project/locations/us-east1',
            job=cp_job_create),
        response=cp_job_create)

  def ExpectMessagesForJobExists(self, cp_job_id, cp_job_patch):
    cp_job_name = 'projects/my-project/locations/us-east1/jobs/' + cp_job_id
    self.mocked_scheduler_v1.projects_locations_jobs.Get.Expect(
        self.scheduler_msg.CloudschedulerProjectsLocationsJobsGetRequest(
            name=cp_job_name),
        response=cp_job_patch)
    self.mocked_scheduler_v1.projects_locations_jobs.Patch.Expect(
        self.scheduler_msg.CloudschedulerProjectsLocationsJobsPatchRequest(
            name=cp_job_name,
            job=cp_job_patch),
        response=cp_job_patch)

  def ExpectMessagesForTriggerPatch(self, bt_patch):
    self.mocked_cloudbuild_v1.projects_triggers.Patch.Expect(
        self.build_msg.CloudbuildProjectsTriggersPatchRequest(
            buildTrigger=bt_patch,
            projectId='my-project',
            triggerId=bt_patch.id),
        response=bt_patch)

  def ExpectMessagesPRPreviewDoesNotExist(
      self, pp_bt_name='ppgab-test-owner-test-repo',
      pp_bt_description='Build and deploy on PR create/update against '
                        '"test-pr-pattern"',
      cp_bt_name='cpgab-test-owner-test-repo',
      cp_bt_description='Clean expired preview deployments for PRs '
                        'against "test-pr-pattern"',
      cp_job_id='cpgab-test-owner-test-repo',
      cp_job_description='Every day, run trigger to clean expired preview '
                         'deployments for PRs against "test-pr-pattern" in '
                         'test-owner/test-repo',
      repo_name='test-repo',
      comment_control=False, preview_expiry='3',
      image='gcr.io/my-project/github.com/test-owner/test-repo:$COMMIT_SHA',
      build_timeout=None,
      pr_pattern='test-pr-pattern'
  ):
    locations_res = self.scheduler_msg.ListLocationsResponse(locations=[
        self.scheduler_msg.Location(
            labels=self.scheduler_msg.Location.LabelsValue(
                additionalProperties=[
                    self.scheduler_msg.Location.LabelsValue.AdditionalProperty(
                        key='cloud.googleapis.com/region',
                        value='us-east1')]))])
    self.mocked_scheduler_v1.projects_locations.List.Expect(
        self.scheduler_msg.CloudschedulerProjectsLocationsListRequest(
            name='projects/my-project'),
        response=locations_res)

    pp_bt_create = self.DefaultPRPreviewBuildTriggerCreate(
        pp_bt_name,
        pp_bt_description,
        repo_name=repo_name,
        app_name=repo_name,
        build_timeout=build_timeout,
        preview_expiry=preview_expiry,
        comment_control=comment_control,
        image=image,
        pr_pattern=pr_pattern)
    pp_bt_create_resp = self.DefaultBuildTriggerCreateResponse(pp_bt_create)
    pp_bt_patch = self.DefaultBuildTriggerPatch(pp_bt_create_resp)
    pp_bt_patch_resp = self.DefaultBuildTriggerPatchResp(pp_bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(pp_bt_name, pp_bt_create,
                                              pp_bt_create_resp, pp_bt_patch,
                                              pp_bt_patch_resp)

    cp_bt_create = self.DefaultCleanPreviewBuildTriggerCreate(
        cp_bt_name,
        cp_bt_description,
        repo_name=repo_name,
        app_name=repo_name)
    cp_bt_create_resp = self.DefaultBuildTriggerCreateResponse(
        cp_bt_create, trigger_id='555-555-555')

    self.ExpectMessagesForTriggerDoesNotExist(cp_bt_name, cp_bt_create,
                                              cp_bt_create_resp)

    cp_job_create = self.DefaultCleanPreviewSchedulerJobCreate(
        cp_job_id,
        cp_job_description,
        repo_name=repo_name)

    self.ExpectMessagesForJobDoesNotExist(cp_job_id, cp_job_create)

    tags = build_util._DEFAULT_CLEAN_PREVIEW_TAGS[:]
    tags.append(repo_name)
    tags.append('cloudscheduler-job-location_us-east1')
    tags.append('cloudscheduler-job-id_' + cp_job_id)
    cp_bt_patch = self.TriggerSetTags(cp_bt_create_resp, tags)
    self.ExpectMessagesForTriggerPatch(cp_bt_patch)

  def DefaultGitPushBuildTriggerCreate(
      self, name, description, repo_source=None, github_events_config=None,
      image='gcr.io/my-project/github.com/test-owner/test-repo:$COMMIT_SHA',
      dockerfile='Dockerfile', app_name='test-repo', config='',
      namespace='default', expose='0', cluster='test-cluster',
      location='us-central1',
      config_staging_dir='my-project_cloudbuild/deploy/config',
      build_timeout=None
  ):
    substitutions_dict = {
        build_util._DOCKERFILE_PATH_SUB_VAR: dockerfile,
        build_util._APP_NAME_SUB_VAR: app_name,
        build_util._K8S_YAML_PATH_SUB_VAR: config,
        build_util._EXPOSE_PORT_SUB_VAR: expose,
        build_util._GKE_CLUSTER_SUB_VAR: cluster,
        build_util._GKE_LOCATION_SUB_VAR: location,
        build_util._OUTPUT_BUCKET_PATH_SUB_VAR: config_staging_dir,
        build_util._K8S_ANNOTATIONS_SUB_VAR: '',
        build_util._K8S_NAMESPACE_SUB_VAR: namespace,
    }
    trigger_tags = build_util._DEFAULT_TAGS[:]
    trigger_tags.append(app_name)
    build_tags = build_util._DEFAULT_TAGS[:]
    build_tags.append(app_name)
    return self.build_msg.BuildTrigger(
        name=name,
        description=description,
        triggerTemplate=repo_source,
        github=github_events_config,
        tags=trigger_tags,
        substitutions=cloudbuild_util.EncodeTriggerSubstitutions(
            substitutions_dict, self.build_msg
        ),
        build=self.build_msg.Build(
            timeout=build_timeout,
            tags=build_tags,
            options=self.build_msg.BuildOptions(
                substitutionOption=self._sub_options.ALLOW_LOOSE
            ),
            steps=[
                self.build_msg.BuildStep(
                    id=build_util._BUILD_BUILD_STEP_ID,
                    name='gcr.io/cloud-builders/docker',
                    args=[
                        'build', '--network', 'cloudbuild', '--no-cache', '-t',
                        image, '-f',
                        '${}'.format(build_util._DOCKERFILE_PATH_SUB_VAR), '.'
                    ],
                ),
                self.build_msg.BuildStep(
                    id=build_util._PUSH_BUILD_STEP_ID,
                    name='gcr.io/cloud-builders/docker',
                    args=['push', image]
                ),
                self.build_msg.BuildStep(
                    id=build_util._PREPARE_DEPLOY_BUILD_STEP_ID,
                    name=build_util._GKE_DEPLOY_PROD,
                    args=[
                        'prepare',
                        '--filename=${}'.format(
                            build_util._K8S_YAML_PATH_SUB_VAR),
                        '--image={}'.format(image),
                        '--app=${}'.format(build_util._APP_NAME_SUB_VAR),
                        '--version=$COMMIT_SHA',
                        '--namespace=${}'.format(
                            build_util._K8S_NAMESPACE_SUB_VAR),
                        '--output=output',
                        '--annotation=gcb-build-id=$BUILD_ID,${}'.format(
                            build_util._K8S_ANNOTATIONS_SUB_VAR),
                        '--expose=${}'.format(build_util._EXPOSE_PORT_SUB_VAR),
                        '--create-application-cr',
                        '--links="Build details=https://console.cloud.google.com/cloud-build/builds/$BUILD_ID?project=$PROJECT_ID"',
                    ],
                ),
                self.build_msg.BuildStep(
                    id=build_util._SAVE_CONFIGS_BUILD_STEP_ID,
                    name='gcr.io/cloud-builders/gsutil',
                    entrypoint='bash',
                    args=[
                        '-c',
                        build_util._SAVE_CONFIGS_SCRIPT
                    ],
                ),
                self.build_msg.BuildStep(
                    id=build_util._APPLY_DEPLOY_BUILD_STEP_ID,
                    name=build_util._GKE_DEPLOY_PROD,
                    args=[
                        'apply',
                        '--filename=output/expanded',
                        '--namespace=${}'.format(
                            build_util._K8S_NAMESPACE_SUB_VAR),
                        '--cluster=${}'.format(build_util._GKE_CLUSTER_SUB_VAR),
                        '--location=${}'.format(
                            build_util._GKE_LOCATION_SUB_VAR),
                        '--timeout=24h'
                    ],
                )
            ],
            substitutions=cloudbuild_util.EncodeSubstitutions(
                substitutions_dict, self.build_msg
            ),
            images=[image],
            artifacts=self.build_msg.Artifacts(
                objects=self.build_msg.ArtifactObjects(
                    location='gs://' +
                    build_util._EXPANDED_CONFIGS_PATH_DYNAMIC,
                    paths=['output/expanded/*']
                )
            )
        )
    )

  def DefaultPRPreviewBuildTriggerCreate(
      self, name, description, repo_owner='test-owner', repo_name='test-repo',
      pr_pattern='test-pr-pattern', preview_expiry='3', comment_control=False,
      image='gcr.io/my-project/github.com/test-owner/test-repo:$COMMIT_SHA',
      dockerfile='Dockerfile', app_name='test-repo', config='', expose='0',
      cluster='test-cluster', location='us-central1',
      config_staging_dir='my-project_cloudbuild/deploy/config',
      build_timeout=None,
  ):
    substitutions_dict = {
        build_util._DOCKERFILE_PATH_SUB_VAR: dockerfile,
        build_util._APP_NAME_SUB_VAR: app_name,
        build_util._K8S_YAML_PATH_SUB_VAR: config,
        build_util._EXPOSE_PORT_SUB_VAR: expose,
        build_util._GKE_CLUSTER_SUB_VAR: cluster,
        build_util._GKE_LOCATION_SUB_VAR: location,
        build_util._OUTPUT_BUCKET_PATH_SUB_VAR: config_staging_dir,
        build_util._K8S_ANNOTATIONS_SUB_VAR: '',
        build_util._PREVIEW_EXPIRY_SUB_VAR: preview_expiry,
    }
    trigger_tags = build_util._DEFAULT_PR_PREVIEW_TAGS[:]
    trigger_tags.append(app_name)
    build_tags = build_util._DEFAULT_PR_PREVIEW_TAGS[:]
    build_tags.append(app_name)
    github_config = self.build_msg.GitHubEventsConfig(
        owner=repo_owner,
        name=repo_name,
        pullRequest=self.build_msg.PullRequestFilter(
            branch=pr_pattern
        )
    )
    if comment_control:
      github_config.pullRequest.commentControl = \
        self.build_msg.PullRequestFilter.CommentControlValueValuesEnum.COMMENTS_ENABLED

    return self.build_msg.BuildTrigger(
        name=name,
        description=description,
        github=github_config,
        tags=trigger_tags,
        substitutions=cloudbuild_util.EncodeTriggerSubstitutions(
            substitutions_dict, self.build_msg
        ),
        build=self.build_msg.Build(
            timeout=build_timeout,
            tags=build_tags,
            options=self.build_msg.BuildOptions(
                substitutionOption=self._sub_options.ALLOW_LOOSE
            ),
            steps=[
                self.build_msg.BuildStep(
                    id=build_util._BUILD_BUILD_STEP_ID,
                    name='gcr.io/cloud-builders/docker',
                    args=[
                        'build', '--network', 'cloudbuild', '--no-cache', '-t',
                        image, '-f',
                        '${}'.format(build_util._DOCKERFILE_PATH_SUB_VAR), '.'
                    ],
                ),
                self.build_msg.BuildStep(
                    id=build_util._PUSH_BUILD_STEP_ID,
                    name='gcr.io/cloud-builders/docker',
                    args=['push', image]
                ),
                self.build_msg.BuildStep(
                    id=build_util._PREPARE_DEPLOY_BUILD_STEP_ID,
                    name=build_util._GKE_DEPLOY_PROD,
                    entrypoint='sh',
                    args=[
                        '-c',
                        build_util._PREPARE_PREVIEW_DEPLOY_SCRIPT.format(
                            image=image,
                            cluster=build_util._GKE_CLUSTER_SUB_VAR,
                            location=build_util._GKE_LOCATION_SUB_VAR,
                            k8s_yaml_path=build_util._K8S_YAML_PATH_SUB_VAR,
                            app_name=build_util._APP_NAME_SUB_VAR,
                            k8s_annotations=build_util._K8S_ANNOTATIONS_SUB_VAR,
                            expose_port=build_util._EXPOSE_PORT_SUB_VAR,
                        )
                    ],
                ),
                self.build_msg.BuildStep(
                    id=build_util._SAVE_CONFIGS_BUILD_STEP_ID,
                    name='gcr.io/cloud-builders/gsutil',
                    entrypoint='bash',
                    args=[
                        '-c',
                        build_util._SAVE_CONFIGS_SCRIPT
                    ],
                ),
                self.build_msg.BuildStep(
                    id=build_util._APPLY_DEPLOY_BUILD_STEP_ID,
                    name=build_util._GKE_DEPLOY_PROD,
                    entrypoint='sh',
                    args=[
                        '-c',
                        build_util._APPLY_PREVIEW_DEPLOY_SCRIPT
                    ],
                ),
                self.build_msg.BuildStep(
                    id=build_util._ANNOTATE_PREVIEW_NAMESPACE_BUILD_STEP_ID,
                    name='gcr.io/cloud-builders/kubectl',
                    entrypoint='sh',
                    args=[
                        '-c',
                        build_util._ANNOTATE_PREVIEW_NAMESPACE_SCRIPT
                    ],
                )
            ],
            substitutions=cloudbuild_util.EncodeSubstitutions(
                substitutions_dict, self.build_msg
            ),
            images=[image],
            artifacts=self.build_msg.Artifacts(
                objects=self.build_msg.ArtifactObjects(
                    location='gs://' +
                    build_util._EXPANDED_CONFIGS_PATH_DYNAMIC,
                    paths=['output/expanded/*']
                )
            )
        )
    )

  def DefaultCleanPreviewBuildTriggerCreate(
      self, name, description, repo_owner='test-owner', repo_name='test-repo',
      app_name='test-repo',
      cluster='test-cluster', location='us-central1'):
    substitutions_dict = {
        build_util._GKE_CLUSTER_SUB_VAR: cluster,
        build_util._GKE_LOCATION_SUB_VAR: location,
    }
    trigger_tags = build_util._DEFAULT_CLEAN_PREVIEW_TAGS[:]
    trigger_tags.append(app_name)
    build_tags = build_util._DEFAULT_CLEAN_PREVIEW_TAGS[:]
    build_tags.append(app_name)
    github_config = self.build_msg.GitHubEventsConfig(
        owner=repo_owner,
        name=repo_name,
        push=self.build_msg.PushFilter(
            branch='$manual-only^',
        )
    )
    return self.build_msg.BuildTrigger(
        name=name,
        description=description,
        github=github_config,
        tags=trigger_tags,
        substitutions=cloudbuild_util.EncodeTriggerSubstitutions(
            substitutions_dict, self.build_msg
        ),
        build=self.build_msg.Build(
            timeout='600s',
            tags=build_tags,
            steps=[
                self.build_msg.BuildStep(
                    id=build_util._CLEANUP_PREVIEW_BUILD_STEP_ID,
                    name='gcr.io/cloud-builders/kubectl',
                    entrypoint='bash',
                    args=[
                        '-c',
                        build_util._CLEANUP_PREVIEW_SCRIPT
                    ],
                )
            ],
            substitutions=cloudbuild_util.EncodeSubstitutions(
                substitutions_dict, self.build_msg
            )
        )
    )

  def DefaultCleanPreviewSchedulerJobCreate(
      self, job_id, description, repo_name='test-repo'):
    return self.scheduler_msg.Job(
        name='projects/my-project/locations/us-east1/jobs/{}'.format(job_id),
        description=description,
        schedule=gke._CLEAN_PREVIEW_SCHEDULE,
        timeZone='UTC',
        httpTarget=self.scheduler_msg.HttpTarget(
            uri='https://cloudbuild.googleapis.com/v1/projects/my-project/triggers/555-555-555:run',
            httpMethod=self.scheduler_msg.HttpTarget.HttpMethodValueValuesEnum
            .POST,
            body=bytes(
                '{{"projectId":"my-project","repoName":"{}","branchName":"main"}}'
                .format(repo_name).encode('utf-8')),
            oauthToken=self.scheduler_msg.OAuthToken(
                serviceAccountEmail='my-project@appspot.gserviceaccount.com'
            )
        )
    )

  def RepoSource(self, name, branch_pattern=None, tag_pattern=None):
    return self.build_msg.RepoSource(
        projectId='my-project',
        repoName=name,
        branchName=branch_pattern,
        tagName=tag_pattern
    )

  def GitHubEventsConfig(self, owner, name, branch_pattern=None,
                         tag_pattern=None):
    return self.build_msg.GitHubEventsConfig(
        owner=owner,
        name=name,
        push=self.build_msg.PushFilter(
            branch=branch_pattern,
            tag=tag_pattern
        )
    )

  def DefaultBuildTriggerCreateResponse(self, bt_create,
                                        trigger_id='123-456-789'):
    bt_create_resp = copy.deepcopy(bt_create)
    bt_create_resp.id = trigger_id
    return bt_create_resp

  def DefaultBuildTriggerPatch(self, bt_create_resp):
    bt_patch = copy.deepcopy(bt_create_resp)

    annotations_substitution = next((
        x for x in bt_patch.substitutions.additionalProperties
        if x.key == build_util._K8S_ANNOTATIONS_SUB_VAR
    ), None)
    annotations_substitution.value = ',gcb-trigger-id=' + bt_create_resp.id
    annotations_substitution = next((
        x for x in bt_patch.build.substitutions.additionalProperties
        if x.key == build_util._K8S_ANNOTATIONS_SUB_VAR
    ), None)
    annotations_substitution.value = ',gcb-trigger-id=' + bt_create_resp.id

    return bt_patch

  def DefaultBuildTriggerPatchResp(self, bt_patch):
    bt_patch_resp = copy.deepcopy(bt_patch)
    return bt_patch_resp

  def TriggerSetTags(self, trigger, tags):
    trigger_copy = copy.deepcopy(trigger)
    trigger_copy.tags = tags
    trigger_copy.build.tags = tags
    return trigger_copy

  def testGitHubRepoBranch(self):
    self.ExpectInitialMessagesForConfigure()

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', branch_pattern='test-branch-pattern')
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
    ])

  def testGitHubRepoTag(self):
    self.ExpectInitialMessagesForConfigure()

    bt_name = 'gpgat-test-owner-test-repo-test-tag-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on "test-tag-pattern" tag',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', tag_pattern='test-tag-pattern')
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--tag-pattern=test-tag-pattern'
    ])

  def testGitHubRepoRequiresRepoOwner(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--repo-owner]: '
        'Repo owner is required for --repo-type=github.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github', '--repo-name=test-repo',
          '--branch-pattern=test-branch-pattern'
      ])

  def testBitbucketMirroredRepoBranch(self):
    self.ExpectInitialMessagesForConfigure(repo_type='bitbucket_mirrored',
                                           repo_owner='test-owner',
                                           repo_name='test-repo')

    bt_name = 'gpbmb-bitbucket-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        repo_source=self.RepoSource('bitbucket_test-owner_test-repo',
                                    branch_pattern='test-branch-pattern'),
        image='gcr.io/my-project/bitbucket.org/test-owner/test-repo:$COMMIT_SHA'
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=bitbucket_mirrored', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
    ])

  def testBitbucketMirroredRepoTag(self):
    self.ExpectInitialMessagesForConfigure(repo_type='bitbucket_mirrored',
                                           repo_owner='test-owner',
                                           repo_name='test-repo')

    bt_name = 'gpbmt-bitbucket-test-owner-test-repo-test-tag-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on "test-tag-pattern" tag',
        repo_source=self.RepoSource('bitbucket_test-owner_test-repo',
                                    tag_pattern='test-tag-pattern'),
        image='gcr.io/my-project/bitbucket.org/test-owner/test-repo:$COMMIT_SHA'
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=bitbucket_mirrored', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--tag-pattern=test-tag-pattern'
    ])

  def testBitbucketMirroredRepoRequiresRepoOwner(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--repo-owner]: '
        'Repo owner is required for --repo-type=bitbucket_mirrored.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=bitbucket_mirrored', '--repo-name=test-repo',
          '--branch-pattern=test-branch-pattern'
      ])

  def testBitbucketMirroredRepoNoMirrorConfig(self):
    self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
        self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
            name='projects/my-project/repos/bitbucket_test-owner_test-repo'),
        response=self.sourcerepo_msg.Repo()
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-type]: '
        "Repo 'test-owner/test-repo' is found but the resolved repo name "
        "'bitbucket_test-owner_test-repo' is a regular "
        'CSR repo. Reference it with --repo-type=csr and '
        '--repo-name=bitbucket_test-owner_test-repo.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=bitbucket_mirrored', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testBitbucketMirroredRepoBadMirrorURLConfig(self):
    self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
        self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
            name='projects/my-project/repos/bitbucket_test-owner_test-repo'),
        response=self.sourcerepo_msg.Repo(
            mirrorConfig=self.sourcerepo_msg.MirrorConfig(
                url='asdf'
            )
        )
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-type]: '
        "Repo 'test-owner/test-repo' is found but the resolved repo name "
        "'bitbucket_test-owner_test-repo' is not "
        'connected to a Bitbucket repo. Specify the correct value for '
        '--repo-type.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=bitbucket_mirrored', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testBitbucketMirroredRepoNotFound(self):
    self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
        self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
            name='projects/my-project/repos/bitbucket_test-owner_test-repo'),
        exception=http_error.MakeHttpError(404, 'not found')
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-name]: '
        "Bitbucket repo 'test-owner/test-repo' is not connected to CSR.\n\n"
        'Visit https://console.cloud.google.com/cloud-build/triggers/connect?project=my-project '
        'to connect a repository to your project.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=bitbucket_mirrored', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testGitHubMirroredRepoBranch(self):
    self.ExpectInitialMessagesForConfigure(repo_type='github_mirrored',
                                           repo_owner='test-owner',
                                           repo_name='test-repo')

    bt_name = 'gpgmb-github-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        repo_source=self.RepoSource(
            'github_test-owner_test-repo', branch_pattern='test-branch-pattern')
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github_mirrored', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
    ])

  def testGitHubMirroredRepoTag(self):
    self.ExpectInitialMessagesForConfigure(repo_type='github_mirrored',
                                           repo_owner='test-owner',
                                           repo_name='test-repo')

    bt_name = 'gpgmt-github-test-owner-test-repo-test-tag-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on "test-tag-pattern" tag',
        repo_source=self.RepoSource('github_test-owner_test-repo',
                                    tag_pattern='test-tag-pattern')
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github_mirrored', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--tag-pattern=test-tag-pattern'
    ])

  def testGitHubMirroredRepoRequiresRepoOwner(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--repo-owner]: '
        'Repo owner is required for --repo-type=github_mirrored.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github_mirrored', '--repo-name=test-repo',
          '--branch-pattern=test-branch-pattern'
      ])

  def testGitHubMirroredRepoNoMirrorConfig(self):
    self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
        self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
            name='projects/my-project/repos/github_test-owner_test-repo'),
        response=self.sourcerepo_msg.Repo()
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-type]: '
        "Repo 'test-owner/test-repo' is found but the resolved repo name "
        "'github_test-owner_test-repo' is a regular "
        'CSR repo. Reference it with --repo-type=csr and '
        '--repo-name=github_test-owner_test-repo.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github_mirrored', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testGitHubMirroredRepoBadMirrorURLConfig(self):
    self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
        self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
            name='projects/my-project/repos/github_test-owner_test-repo'),
        response=self.sourcerepo_msg.Repo(
            mirrorConfig=self.sourcerepo_msg.MirrorConfig(
                url='asdf'
            )
        )
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-type]: '
        "Repo 'test-owner/test-repo' is found but the resolved repo name 'github_test-owner_test-repo' is not "
        'connected to a GitHub repo. Specify the correct value for '
        '--repo-type.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github_mirrored', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testGitHubMirroredRepoNotFound(self):
    self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
        self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
            name='projects/my-project/repos/github_test-owner_test-repo'),
        exception=http_error.MakeHttpError(404, 'not found')
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-name]: '
        "GitHub repo 'test-owner/test-repo' is not connected to CSR.\n\n"
        'Visit https://console.cloud.google.com/cloud-build/triggers/connect?project=my-project '
        'to connect a repository to your project.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github_mirrored', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testCSRRepoBranch(self):
    self.ExpectInitialMessagesForConfigure(repo_type='csr',
                                           repo_name='test-repo')

    bt_name = 'gpcsb-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        repo_source=self.RepoSource('test-repo',
                                    branch_pattern='test-branch-pattern'),
        image='gcr.io/my-project/test-repo:$COMMIT_SHA'
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=csr', '--repo-name=test-repo',
        '--branch-pattern=test-branch-pattern'
    ])

  def testCSRRepoTag(self):
    self.ExpectInitialMessagesForConfigure(repo_type='csr',
                                           repo_name='test-repo')

    bt_name = 'gpcst-test-repo-test-tag-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on "test-tag-pattern" tag',
        repo_source=self.RepoSource('test-repo',
                                    tag_pattern='test-tag-pattern'),
        image='gcr.io/my-project/test-repo:$COMMIT_SHA'
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=csr', '--repo-name=test-repo',
        '--tag-pattern=test-tag-pattern'
    ])

  def testCSRRepoShouldNotHaveRepoOwner(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-owner]: '
        'Repo owner must not be provided for --repo-type=csr.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=csr', '--repo-name=test-repo', '--repo-owner=test-owner',
          '--branch-pattern=test-branch-pattern'
      ])

  def testCSRRepoHasMirrorConfig(self):
    self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
        self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
            name='projects/my-project/repos/test-repo'),
        response=self.sourcerepo_msg.Repo(
            mirrorConfig=self.sourcerepo_msg.MirrorConfig(
                url='asdf'
            )
        )
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-type]: '
        "Repo 'test-repo' is found but is connected to asdf. Specify the "
        'correct value for --repo-type, along with appropriate values for '
        '--repo-owner and --repo-name.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=csr', '--repo-name=test-repo',
          '--branch-pattern=test-branch-pattern'
      ])

  def testCSRRepoNotFound(self):
    self.mocked_sourcerepo_v1.projects_repos.Get.Expect(
        self.sourcerepo_msg.SourcerepoProjectsReposGetRequest(
            name='projects/my-project/repos/test-repo'),
        exception=http_error.MakeHttpError(404, 'not found')
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        "Invalid value for [--repo-name]: Repo 'test-repo' is not found on "
        'CSR'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=csr', '--repo-name=test-repo',
          '--branch-pattern=test-branch-pattern'
      ])

  def testClusterNotFound(self):
    self.mocked_container_v1.projects_locations_clusters.Get.Expect(
        self.container_msg.ContainerProjectsLocationsClustersGetRequest(
            name='projects/my-project/locations/us-central1/clusters/test-cluster'
        ),
        exception=http_error.MakeHttpError(404, 'not found')
    )

    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        "Invalid value for [--cluster]: No cluster 'test-cluster' in location "
        "'us-central1' in project my-project.\n\n"
        'Visit https://console.cloud.google.com/kubernetes/list?project=my-project '
        'to create a cluster.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testOutputContainsTriggerUILink(self):
    self.ExpectInitialMessagesForConfigure()

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', branch_pattern='test-branch-pattern')
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
    ])

    self.AssertErrContains(
        'Visit https://console.cloud.google.com/cloud-build/triggers/edit/{trigger_id}?project=my-project '
        'to view the trigger.\n\n'
        'You can visit https://console.cloud.google.com/cloud-build/triggers?project=my-project '
        'to view all Cloud Build triggers.'
        .format(trigger_id=bt_create_resp.id),
        normalize_space=True
    )

  def testAppName(self):
    self.ExpectInitialMessagesForConfigure()

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', branch_pattern='test-branch-pattern'),
        app_name='override',
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern',
        '--app-name=override'
    ])

  def testGCSConfigStagingDir(self):
    self.ExpectInitialMessagesForConfigure(bucket_name_override='test-bucket')

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', branch_pattern='test-branch-pattern'),
        config_staging_dir='test-bucket',
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern',
        '--gcs-config-staging-dir=gs://test-bucket'
    ])

  def testGCSConfigStagingDirWithSubdirectory(self):
    self.ExpectInitialMessagesForConfigure(bucket_name_override='test-bucket')

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', branch_pattern='test-branch-pattern'),
        config_staging_dir='test-bucket/path',
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern',
        '--gcs-config-staging-dir=gs://test-bucket/path'
    ])

  def testDefaultGCSConfigStagingBucketNotInUserProject(self):
    cluster_name = 'projects/my-project/locations/us-central1/clusters/test-cluster'
    self.mocked_container_v1.projects_locations_clusters.Get.Expect(
        self.container_msg.ContainerProjectsLocationsClustersGetRequest(
            name=cluster_name,
        ),
        response=self.container_msg.Cluster(
            name=cluster_name,
            status=self.container_msg.Cluster.StatusValueValuesEnum.RUNNING)
    )

    b = self.storage_msg.Bucket(id='my-project_cloudbuild')
    self.mocked_storage_v1.buckets.Get.Expect(
        self.storage_msg.StorageBucketsGetRequest(bucket=b.id), response=b)
    self.mocked_storage_v1.buckets.List.Expect(
        self.storage_msg.StorageBucketsListRequest(
            project='my-project',
            prefix=b.id,
        ),
        response=self.storage_msg.Buckets(items=[]))

    with self.AssertRaisesExceptionMatches(
        exceptions.RequiredArgumentException,
        'Missing required argument [--gcs-config-staging-dir]: '
        'A bucket with name my-project_cloudbuild already exists and is owned '
        'by another project. Specify a bucket using '
        '--gcs-config-staging-dir.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testTimeout(self):
    self.ExpectInitialMessagesForConfigure()

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', branch_pattern='test-branch-pattern'),
        build_timeout='60s',
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern',
        '--timeout=1m'
    ])

  def testTimeoutNoUnits(self):
    self.ExpectInitialMessagesForConfigure()

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', branch_pattern='test-branch-pattern'),
        build_timeout='60s'
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern',
        '--timeout=60'
    ])

  def testExpose(self):
    self.ExpectInitialMessagesForConfigure()

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_create = self.DefaultGitPushBuildTriggerCreate(
        bt_name,
        'Build and deploy on push to "test-branch-pattern"',
        github_events_config=self.GitHubEventsConfig(
            'test-owner', 'test-repo', branch_pattern='test-branch-pattern'),
        expose='80',
    )

    bt_create_resp = self.DefaultBuildTriggerCreateResponse(bt_create)
    bt_patch = self.DefaultBuildTriggerPatch(bt_create_resp)
    bt_patch_resp = self.DefaultBuildTriggerPatchResp(bt_patch)

    self.ExpectMessagesForTriggerDoesNotExist(bt_name, bt_create,
                                              bt_create_resp, bt_patch,
                                              bt_patch_resp)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern',
        '--expose=80'
    ])

  def testGitPushTriggerExists(self):
    self.ExpectInitialMessagesForConfigure()

    bt_name = 'gpgab-test-owner-test-repo-test-branch-pattern'
    bt_get_resp = self.DefaultBuildTriggerPatch(
        self.DefaultBuildTriggerCreateResponse(
            self.DefaultGitPushBuildTriggerCreate(
                bt_name,
                'Build and deploy on push to '
                '"test-branch-pattern"',
                github_events_config=self.GitHubEventsConfig(
                    'test-owner',
                    'test-repo', branch_pattern='test-branch-pattern')
            )))

    bt_patch = copy.deepcopy(bt_get_resp)
    bt_patch.id = None
    bt_patch_res = copy.deepcopy(bt_get_resp)

    self.ExpectMessagesForTriggerExists(bt_name, bt_get_resp,
                                        bt_patch, bt_patch_res)
    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
    ])

  def testPullRequestPreviewRequiresGithubRepoType(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--repo-type]: '
        "Repo type must be 'github' to configure pull request previewing."):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=csr', '--repo-name=test-repo',
          '--pull-request-preview', '--pull-request-pattern=test-pr-pattern'
      ])

  def testPullRequestPreviewNamespaceShouldNotBeProvided(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--namespace]: '
        'Namespace must not be provided to configure pull request '
        'previewing. --namespace must only be provided when configuring '
        'automated deployments with the --branch-pattern or --tag-pattern '
        'flags.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github', '--repo-name=test-repo',
          '--pull-request-preview', '--pull-request-pattern=test-pr-pattern',
          '--namespace=foobar'
      ])

  def testPullRequestPreviewPreviewExpiryMustBeGE0(self):
    with self.AssertRaisesExceptionMatches(
        exceptions.InvalidArgumentException,
        'Invalid value for [--preview-expiry]: '
        'Preview expiry must be > 0.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github', '--repo-name=test-repo',
          '--pull-request-preview', '--pull-request-pattern=test-pr-pattern',
          '--preview-expiry=0',
      ])

  def testPullRequestPreview(self):
    self.ExpectInitialMessagesForConfigure()
    self.ExpectMessagesPRPreviewDoesNotExist()

    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--pull-request-pattern=test-pr-pattern',
        '--pull-request-preview',
    ])

  def testPullRequestPreviewTimeout(self):
    self.ExpectInitialMessagesForConfigure()
    self.ExpectMessagesPRPreviewDoesNotExist(build_timeout='120s')

    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--pull-request-pattern=test-pr-pattern',
        '--pull-request-preview', '--timeout=2m',
    ])

  def testPullRequestPreviewTimeoutNoUnits(self):
    self.ExpectInitialMessagesForConfigure()
    self.ExpectMessagesPRPreviewDoesNotExist(build_timeout='55s')

    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--pull-request-pattern=test-pr-pattern',
        '--pull-request-preview', '--timeout=55',
    ])

  def testPullRequestPreviewCommentControl(self):
    self.ExpectInitialMessagesForConfigure()
    self.ExpectMessagesPRPreviewDoesNotExist(comment_control=True)

    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--pull-request-pattern=test-pr-pattern',
        '--pull-request-preview', '--comment-control',
    ])

  def testPullRequestPreviewPreviewExpiry(self):
    self.ExpectInitialMessagesForConfigure()
    self.ExpectMessagesPRPreviewDoesNotExist(preview_expiry='100')

    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--pull-request-pattern=test-pr-pattern',
        '--pull-request-preview', '--preview-expiry=100',
    ])

  def testPullRequestPreviewPreviewLongRepoName(self):
    self.ExpectInitialMessagesForConfigure()
    self.ExpectMessagesPRPreviewDoesNotExist(
        pp_bt_name='ppgab-test-owner-' + 'a' * 47,
        pp_bt_description='Build and deploy on PR create/update against '
                          '"test-pr-pattern"',
        cp_bt_name='cpgab-test-owner-' + 'a' * 47,
        cp_bt_description='Clean expired preview deployments for PRs '
                          'against "test-pr-pattern"',
        cp_job_id='cpgab-test-owner-{}'.format('a' * 483),
        cp_job_description='Every day, run trigger to clean expired preview '
                           'deployments for PRs against "test-pr-pattern" in '
                           'test-owner/' + 'a' * 490,
        repo_name='a' * 490,
        image='gcr.io/my-project/github.com/test-owner/{}:$COMMIT_SHA'
        .format('a' * 490)
    )

    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=' + 'a' * 490,
        '--repo-owner=test-owner', '--pull-request-pattern=test-pr-pattern',
        '--pull-request-preview',
    ])

  def testPullRequestPreviewExists(self):
    self.ExpectInitialMessagesForConfigure()

    locations_res = self.scheduler_msg.ListLocationsResponse(locations=[
        self.scheduler_msg.Location(
            labels=self.scheduler_msg.Location.LabelsValue(
                additionalProperties=[
                    self.scheduler_msg.Location.LabelsValue.AdditionalProperty(
                        key='cloud.googleapis.com/region',
                        value='us-east1')]))])
    self.mocked_scheduler_v1.projects_locations.List.Expect(
        self.scheduler_msg.CloudschedulerProjectsLocationsListRequest(
            name='projects/my-project'),
        response=locations_res)

    pp_bt_name = 'ppgab-test-owner-test-repo'
    pp_bt_get_resp = self.DefaultBuildTriggerPatch(
        self.DefaultBuildTriggerCreateResponse(
            self.DefaultPRPreviewBuildTriggerCreate(
                pp_bt_name,
                'Build and deploy on PR create/update against '
                '"test-pr-pattern"'
            )))
    pp_bt_patch = copy.deepcopy(pp_bt_get_resp)
    pp_bt_patch.id = None
    pp_bt_patch_resp = copy.deepcopy(pp_bt_patch)

    self.ExpectMessagesForTriggerExists(pp_bt_name, pp_bt_get_resp,
                                        pp_bt_patch, pp_bt_patch_resp)

    cp_bt_name = 'cpgab-test-owner-test-repo'
    cp_bt_get_resp = self.DefaultBuildTriggerCreateResponse(
        self.DefaultCleanPreviewBuildTriggerCreate(
            cp_bt_name,
            'Clean expired preview deployments for PRs against '
            '"test-pr-pattern"'
        ), trigger_id='555-555-555')
    cp_bt_patch = copy.deepcopy(cp_bt_get_resp)
    cp_bt_patch.id = None
    cp_bt_patch_resp = copy.deepcopy(cp_bt_patch)
    cp_bt_patch_resp.id = '555-555-555'

    self.ExpectMessagesForTriggerExists(cp_bt_name, cp_bt_get_resp,
                                        cp_bt_patch, cp_bt_patch_resp)

    cp_job_id = 'cpgab-test-owner-test-repo'
    cp_job_patch = self.DefaultCleanPreviewSchedulerJobCreate(
        cp_job_id,
        'Every day, run trigger to clean expired preview deployments for PRs '
        'against "test-pr-pattern" in test-owner/test-repo'
    )
    self.ExpectMessagesForJobExists(cp_job_id, cp_job_patch)

    tags = build_util._DEFAULT_CLEAN_PREVIEW_TAGS[:]
    tags.append('test-repo')
    tags.append('cloudscheduler-job-location_us-east1')
    tags.append(
        'cloudscheduler-job-id_cpgab-test-owner-test-repo')
    cp_bt_patch = self.TriggerSetTags(cp_bt_patch_resp, tags)
    self.ExpectMessagesForTriggerPatch(cp_bt_patch)

    self.Run([
        'builds', 'deploy', 'configure', 'gke',
        '--cluster=test-cluster', '--location=us-central1',
        '--repo-type=github', '--repo-name=test-repo',
        '--repo-owner=test-owner', '--pull-request-pattern=test-pr-pattern',
        '--pull-request-preview',
    ])

  def testClusterStatusIsNotRunning(self):
    self.mocked_container_v1.projects_locations_clusters.Get.Expect(
        self.container_msg.ContainerProjectsLocationsClustersGetRequest(
            name='projects/my-project/locations/us-central1/clusters/test-cluster'
        ),
        response=self.container_msg.Cluster(
            name='test-cluster',
            status=self.container_msg.Cluster.StatusValueValuesEnum.PROVISIONING
        ))

    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'Cluster was found but status is not RUNNING. Status is PROVISIONING.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--branch-pattern=test-branch-pattern'
      ])

  def testSchedulerLocationNotFound(self):
    self.ExpectInitialMessagesForConfigure()

    self.mocked_scheduler_v1.projects_locations.List.Expect(
        self.scheduler_msg.CloudschedulerProjectsLocationsListRequest(
            name='projects/my-project'),
        exception=http_error.MakeHttpError(404, 'not found'))

    with self.AssertRaisesExceptionMatches(
        core_exceptions.Error,
        'You must create an App Engine application in your project to use Cloud '
        'Scheduler. Visit '
        'https://console.developers.google.com/appengine?project=my-project to '
        'add an App Engine application.'):
      self.Run([
          'builds', 'deploy', 'configure', 'gke',
          '--cluster=test-cluster', '--location=us-central1',
          '--repo-type=github', '--repo-name=test-repo',
          '--repo-owner=test-owner', '--pull-request-pattern=test-pr-pattern',
          '--pull-request-preview',
      ])


if __name__ == '__main__':
  test_case.main()
