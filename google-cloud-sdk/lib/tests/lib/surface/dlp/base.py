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
"""Base classes for all gcloud dlp tests."""
from __future__ import absolute_import
from __future__ import unicode_literals
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base
from six.moves import range


class DlpUnitTestBase(sdk_test_base.WithFakeAuth, cli_test_base.CliTestBase,
                      parameterized.TestCase):
  """Base class for all TPU unit tests."""

  TEST_CONTENT = """\
Now that we know who you are, I know who I am. I'm not a mistake! It all makes
sense! In a comic, you know how you can tell who the arch-villain's going to be?
He's the exact opposite of the hero. (Glass@madcriminal.com) And most times
they're friends, like you and me! I should've known way back when...
You know why, David? Because of the kids. They called me Mr Glass@555-99-5599
"""

  TEST_CSV_CONTENT = """\
Test Name,Test Data
Bob Jones,555-1212
Jane Jones,222-11-2233
Jim Jones,jim23@testemail.com
Mike Jones,555-1212
Kate Jones,Katherine k. Jones
"""

  TEST_IMG_CONTENT = b'iVBORw0KGgoAAAANSUhEUgAAAlgAAAGQBAMAAACAGwOrAAAAG1BMVEX'

  def MakeTestTextFile(self, file_name='tmp.txt', contents=TEST_CONTENT):
    return self.Touch(self.root_path, file_name, contents=contents)

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.msg = apis.GetMessagesModule('dlp', 'v2')
    self.client = mock.Client(apis.GetClientClass('dlp', 'v2'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.zone = 'us-central1-c'
    properties.VALUES.compute.zone.Set(self.zone)
    self.StartPatch('time.sleep')

  def _GetInspectConfig(self, info_types, min_likelihood, limit,
                        include_quote=False, exclude_info_types=False,
                        item_limit=None):
    """Make test text DlpV2InspectConfig for text inspect request."""
    limits = self.msg.GooglePrivacyDlpV2FindingLimits(
        maxFindingsPerRequest=limit or 1000, maxFindingsPerItem=item_limit)
    return self.msg.GooglePrivacyDlpV2InspectConfig(
        excludeInfoTypes=exclude_info_types or False,
        includeQuote=include_quote or False,
        infoTypes=[
            self.msg.GooglePrivacyDlpV2InfoType(name=v) for v in info_types
        ],
        limits=limits,
        minLikelihood=arg_utils.ChoiceToEnum(
            min_likelihood, self.msg.GooglePrivacyDlpV2InspectConfig.
            MinLikelihoodValueValuesEnum))

  def MakeAnalysisConfig(self, dataset, table, project, cat_stat_field=None,
                         num_stat_field=None, quasi_ids=None,
                         sensitive_field=None, output_topics=None,
                         output_tables=None):
    """Build Dlp risk analysis job config."""
    if output_topics:
      actions = self._MakeTopicJobTriggerActions(output_topics)
    else:
      actions = self._MakeTableJobTriggerActions(output_tables)

    privacy_metric = self.msg.GooglePrivacyDlpV2PrivacyMetric()

    if cat_stat_field:
      field = self.msg.GooglePrivacyDlpV2FieldId(name=cat_stat_field)
      cat_stat_config = self.msg.GooglePrivacyDlpV2CategoricalStatsConfig(
          field=field)
      privacy_metric.categoricalStatsConfig = cat_stat_config
    elif num_stat_field:
      field = self.msg.GooglePrivacyDlpV2FieldId(name=num_stat_field)
      num_stat_config = self.msg.GooglePrivacyDlpV2NumericalStatsConfig(
          field=field)
      privacy_metric.numericalStatsConfig = num_stat_config
    elif quasi_ids:
      privacy_metric.lDiversityConfig = (
          self.msg.GooglePrivacyDlpV2LDiversityConfig())
      qids = [self.msg.GooglePrivacyDlpV2FieldId(name=qid) for qid in quasi_ids]
      privacy_metric.lDiversityConfig.quasiIds = qids
      if sensitive_field:
        privacy_metric.lDiversityConfig.sensitiveAttribute = (
            self.msg.GooglePrivacyDlpV2FieldId(name=sensitive_field))

    big_query_table = self.msg.GooglePrivacyDlpV2BigQueryTable(
        datasetId=dataset,
        projectId=project,
        tableId=table)

    return self.msg.GooglePrivacyDlpV2RiskAnalysisJobConfig(
        actions=actions, privacyMetric=privacy_metric,
        sourceTable=big_query_table)

  def MakeTextInspectRequest(self, content, info_types, min_likelihood, limit,
                             include_quote=False, exclude_info_types=False):
    """Make test text ContentInspectRequest message."""
    inner_request = self.msg.GooglePrivacyDlpV2InspectContentRequest(
        inspectConfig=self._GetInspectConfig(info_types, min_likelihood, limit,
                                             include_quote, exclude_info_types),
        item=self.msg.GooglePrivacyDlpV2ContentItem(value=content))

    return self.msg.DlpProjectsContentInspectRequest(
        parent='projects/' + self.Project(),
        googlePrivacyDlpV2InspectContentRequest=inner_request)

  def _MakeTextFindings(self, likelihood, info_types, count,
                        include_quote=False, exclude_info_types=False):
    """Make list of test text DlpV2Findings for text inspect response."""
    findings = []
    count = count or 1000
    for x in range(count):
      quote = 'finding {}'.format(x + 1) if include_quote else None
      infotype = self.msg.GooglePrivacyDlpV2InfoType(
          name=info_types[x % len(info_types)])
      f = self.msg.GooglePrivacyDlpV2Finding(
          createTime='2018-01-01T00:00:{}0.000Z'.format(x),
          infoType=None if exclude_info_types else infotype,
          likelihood=arg_utils.ChoiceToEnum(
              likelihood,
              self.msg.GooglePrivacyDlpV2Finding.LikelihoodValueValuesEnum),
          location=self.msg.GooglePrivacyDlpV2Location(
              byteRange=self.msg.GooglePrivacyDlpV2Range(end=23, start=11),
              codepointRange=self.msg.GooglePrivacyDlpV2Range(
                  end=23, start=11)),
          quote=quote)
      findings.append(f)
    return findings

  def MakeTextInspectResponse(self, likelihood, info_types, limit,
                              include_quote=False, exclude_info_types=False):
    """Make test text InspectContentResponset message."""
    info_types = info_types
    response = self.msg.GooglePrivacyDlpV2InspectContentResponse(
        result=self.msg.GooglePrivacyDlpV2InspectResult(
            findings=self._MakeTextFindings(
                likelihood,
                info_types,
                exclude_info_types=exclude_info_types,
                include_quote=include_quote,
                count=limit)))
    return response

  def _GetTransform(self, redaction_type, replacement=None):
    """Make PrimitiveTransformation message based on redaction type."""
    if redaction_type == 'info-type':
      primative_transform = (
          self.msg.GooglePrivacyDlpV2PrimitiveTransformation(
              replaceWithInfoTypeConfig=self.msg.
              GooglePrivacyDlpV2ReplaceWithInfoTypeConfig()))
    elif redaction_type == 'text':
      primative_transform = self.msg.GooglePrivacyDlpV2PrimitiveTransformation(
          replaceConfig=self.msg.GooglePrivacyDlpV2ReplaceValueConfig(
              newValue=self.msg.GooglePrivacyDlpV2Value(
                  stringValue=replacement)))
    else:
      primative_transform = self.msg.GooglePrivacyDlpV2PrimitiveTransformation(
          redactConfig=self.msg.GooglePrivacyDlpV2RedactConfig())

    return self.msg.GooglePrivacyDlpV2InfoTypeTransformation(
        primitiveTransformation=primative_transform)

  def _GetDeidentifyConfig(self, redaction_type, replacement=None):
    """Make test text DeidentifyConfig for text redact request."""
    transform = self._GetTransform(redaction_type, replacement)
    transform_wrapper = self.msg.GooglePrivacyDlpV2InfoTypeTransformations(
        transformations=[transform])
    return self.msg.GooglePrivacyDlpV2DeidentifyConfig(
        infoTypeTransformations=transform_wrapper)

  def MakeTextRedactRequest(self, content, info_types, min_likelihood,
                            redaction_type, replacement=None):
    """Make text DeidentifyContentRequest messages for testing."""
    inspect_config = self._GetInspectConfig(info_types, min_likelihood, None,
                                            None, None)
    inspect_config.limits = None
    inspect_config.excludeInfoTypes = None
    inspect_config.includeQuote = None
    inner_request = self.msg.GooglePrivacyDlpV2DeidentifyContentRequest(
        inspectConfig=inspect_config,
        deidentifyConfig=self._GetDeidentifyConfig(redaction_type, replacement),
        item=self.msg.GooglePrivacyDlpV2ContentItem(value=content))

    return self.msg.DlpProjectsContentDeidentifyRequest(
        parent='projects/' + self.Project(),
        googlePrivacyDlpV2DeidentifyContentRequest=inner_request)

  def _MakeTransformSummaries(self, info_types, transform, count=3):
    """Build list of test TransformationSummary messages for redact response."""
    summaries = []
    for x in range(count):
      infotype = self.msg.GooglePrivacyDlpV2InfoType(
          name=info_types[x % len(info_types)])
      summary = self.msg.GooglePrivacyDlpV2TransformationSummary(
          infoType=infotype,
          results=[
              self.msg.GooglePrivacyDlpV2SummaryResult(
                  code=self.msg.GooglePrivacyDlpV2SummaryResult.
                  CodeValueValuesEnum.SUCCESS,
                  count=1)
          ],
          transformation=transform,
          transformedBytes=33)
      summaries.append(summary)
    return summaries

  def MakeTextRedactResponse(self, content, likelihood, info_types,
                             redaction_type, replacement):
    """Make text DeidentifyContentResponse messages for testing."""
    info_type_tf = self._GetTransform(redaction_type, replacement)
    transform = info_type_tf.primitiveTransformation
    overview = self.msg.GooglePrivacyDlpV2TransformationOverview(
        transformationSummaries=self._MakeTransformSummaries(
            info_types, transform),
        transformedBytes=255)
    return self.msg.GooglePrivacyDlpV2DeidentifyContentResponse(
        item=self.msg.GooglePrivacyDlpV2ContentItem(value=content),
        overview=overview)

  def _MakeImageFindings(self,
                         likelihood,
                         info_types,
                         count,
                         include_quote=False,
                         exclude_info_types=False):
    """Make list of test image DlpV2Findings for image inspect response."""
    findings = []
    count = count or 1000
    for x in range(count):
      quote = 'finding {}'.format(x + 1) if include_quote else None
      infotype = self.msg.GooglePrivacyDlpV2InfoType(
          name=info_types[x % len(info_types)])
      f = self.msg.GooglePrivacyDlpV2Finding(
          createTime='2018-01-01T00:00:{}0.000Z'.format(x),
          infoType=None if exclude_info_types else infotype,
          likelihood=arg_utils.ChoiceToEnum(likelihood,
                                            self.msg.GooglePrivacyDlpV2Finding.
                                            LikelihoodValueValuesEnum),
          location=self.msg.GooglePrivacyDlpV2Location(contentLocations=[
              self.msg.GooglePrivacyDlpV2ContentLocation(
                  imageLocation=self.msg.GooglePrivacyDlpV2ImageLocation(
                      boundingBoxes=[
                          self.msg.GooglePrivacyDlpV2BoundingBox(
                              height=46, left=150, top=179, width=122)
                      ]))
          ]),
          quote=quote)
      findings.append(f)
    return findings

  def MakeImageInspectRequest(self,
                              content,
                              info_types,
                              min_likelihood,
                              limit,
                              include_quote=False,
                              exclude_info_types=False,
                              file_type='IMAGE'):
    """Make image ContentInspectRequest message for testing."""
    image_content_item = self.msg.GooglePrivacyDlpV2ByteContentItem(
        data=content,
        type=arg_utils.ChoiceToEnum(
            file_type,
            self.msg.GooglePrivacyDlpV2ByteContentItem.TypeValueValuesEnum))
    inner_request = self.msg.GooglePrivacyDlpV2InspectContentRequest(
        inspectConfig=self._GetInspectConfig(info_types, min_likelihood, limit,
                                             include_quote, exclude_info_types),
        item=self.msg.GooglePrivacyDlpV2ContentItem(
            byteItem=image_content_item))

    return self.msg.DlpProjectsContentInspectRequest(
        parent='projects/' + self.Project(),
        googlePrivacyDlpV2InspectContentRequest=inner_request)

  def MakeImageInspectResponse(self,
                               likelihood,
                               info_types,
                               limit,
                               include_quote=False,
                               exclude_info_types=False):
    """Make image InspectContentResponse message for testing."""
    info_types = info_types
    response = self.msg.GooglePrivacyDlpV2InspectContentResponse(
        result=self.msg.GooglePrivacyDlpV2InspectResult(
            findings=self._MakeImageFindings(
                likelihood,
                info_types,
                exclude_info_types=exclude_info_types,
                include_quote=include_quote,
                count=limit)))
    return response

  def _MakeRedactColor(self, color_string):
    """Make DlpV2Color message form r,g,b color string."""
    if not color_string:
      return None
    red, green, blue = [float(x) for x in color_string.split(',')]
    return self.msg.GooglePrivacyDlpV2Color(red=red, green=green, blue=blue)

  def MakeImageRedactRequest(self,
                             file_type,
                             info_types,
                             min_likelihood,
                             include_quote,
                             remove_text=False,
                             redact_color_string=None):
    """Create ImageRedactRequest message for testing."""
    image_content_item = self.msg.GooglePrivacyDlpV2ByteContentItem(
        data=self.TEST_IMG_CONTENT,
        type=arg_utils.ChoiceToEnum(
            file_type,
            self.msg.GooglePrivacyDlpV2ByteContentItem.TypeValueValuesEnum))
    inspect_config = self._GetInspectConfig(info_types, min_likelihood, None,
                                            include_quote, None)
    inspect_config.excludeInfoTypes = None
    image_redaction_config = self.msg.GooglePrivacyDlpV2ImageRedactionConfig(
        redactAllText=remove_text,
        redactionColor=self._MakeRedactColor(redact_color_string))
    inner_request = self.msg.GooglePrivacyDlpV2RedactImageRequest(
        byteItem=image_content_item,
        inspectConfig=inspect_config,
        imageRedactionConfigs=[image_redaction_config])
    inner_request.inspectConfig.limits = None
    return self.msg.DlpProjectsImageRedactRequest(
        googlePrivacyDlpV2RedactImageRequest=inner_request,
        parent='projects/' + self.Project())

  def MakeImageRedactResponse(self):
    """Create a RedactImageResponse message for testing."""
    return self.msg.GooglePrivacyDlpV2RedactImageResponse(
        extractedText='Foo', redactedImage=self.TEST_IMG_CONTENT)

  def _MakeTopicJobTriggerActions(self, output_topics):
    """Build list of GooglePrivacyDlpV2Actions from list of PubSub topics."""
    output_topics = output_topics or []
    topic_actions = []
    for topic in output_topics:
      pubsub_action = self.msg.GooglePrivacyDlpV2PublishToPubSub(topic=topic)
      topic_actions.append(
          self.msg.GooglePrivacyDlpV2Action(pubSub=pubsub_action))
    return topic_actions or None

  def _MakeTableJobTriggerActions(self, output_tables):
    """Build list of GooglePrivacyDlpV2Actions from list of BigTable names."""
    output_tables = output_tables or []
    storage_actions = []
    for table_spec in output_tables:
      project_id, data_set_id, table_id = table_spec.split('.')
      big_query_table = self.msg.GooglePrivacyDlpV2BigQueryTable(
          datasetId=data_set_id, projectId=project_id, tableId=table_id)
      output_config = self.msg.GooglePrivacyDlpV2OutputStorageConfig(
          table=big_query_table)
      save_findings = self.msg.GooglePrivacyDlpV2SaveFindings(
          outputConfig=output_config)
      storage_actions.append(
          self.msg.GooglePrivacyDlpV2Action(saveFindings=save_findings))
    return storage_actions or None

  def _GetJobInputConfig(self, input_params, input_type):
    """Builds a GooglePrivacyDlpV2StorageConfig job input.

    Args:
     input_params: dict, dictionary of storage configuration options for
        provided input_type.
     input_type: str, type of job input to create: gcs, datastore
       or table.

    Returns:
     GooglePrivacyDlpV2StorageConfig, storage config for job input.
    """
    project_id = input_params.get('project_id')
    storage_config = self.msg.GooglePrivacyDlpV2StorageConfig()
    if input_type == 'gcs':
      file_set = self.msg.GooglePrivacyDlpV2FileSet(
          url=input_params.get('gcs_bucket'))
      gcs_option = self.msg.GooglePrivacyDlpV2CloudStorageOptions(
          fileSet=file_set, bytesLimitPerFile=input_params.get('size_limit'))
      storage_config.cloudStorageOptions = gcs_option
    elif input_type == 'table':
      table = self.msg.GooglePrivacyDlpV2BigQueryTable(
          datasetId=input_params.get('bt_data_set_id'),
          projectId=project_id,
          tableId=input_params.get('bt_table_id'))
      big_query_option = self.msg.GooglePrivacyDlpV2BigQueryOptions(
          tableReference=table)
      if input_params.get('input_bq_fields'):
        fields = input_params.get('input_bq_fields')
        identifying_fields = [
            self.msg.GooglePrivacyDlpV2FieldId(name=x) for x in fields]
        big_query_option.identifyingFields = identifying_fields
      storage_config.bigQueryOptions = big_query_option
    else:  # datastore
      kind_exp = self.msg.GooglePrivacyDlpV2KindExpression(
          name=input_params.get('ds_kind'))
      partition = self.msg.GooglePrivacyDlpV2PartitionId(
          namespaceId=input_params.get('ds_namespace_id'), projectId=project_id)
      datastore_option = self.msg.GooglePrivacyDlpV2DatastoreOptions(
          kind=kind_exp, partitionId=partition)
      storage_config.datastoreOptions = datastore_option

    return storage_config

  def MakeJobTrigger(self,
                     description,
                     display_name,
                     info_types,
                     min_likelihood,
                     request_limit,
                     item_limit,
                     input_params,
                     input_type,
                     include_quote=False,
                     exclude_info_types=False,
                     output_tables=None,
                     output_topics=None,
                     duration=None):
    """Create a JobTrigger message for testing."""
    if output_topics:
      actions = self._MakeTopicJobTriggerActions(output_topics)
    else:
      actions = self._MakeTableJobTriggerActions(output_tables)
    inspect_config = self._GetInspectConfig(info_types, min_likelihood,
                                            request_limit, include_quote,
                                            exclude_info_types)
    inspect_config.limits.maxFindingsPerItem = item_limit
    trigger_input_config = self._GetJobInputConfig(input_params, input_type)
    inspect_job = self.msg.GooglePrivacyDlpV2InspectJobConfig(
        actions=actions,
        inspectConfig=inspect_config,
        storageConfig=trigger_input_config)
    trigger_schedule = [
        self.msg.GooglePrivacyDlpV2Trigger(
            schedule=self.msg.GooglePrivacyDlpV2Schedule(
                recurrencePeriodDuration=duration))
    ]

    return self.msg.GooglePrivacyDlpV2JobTrigger(
        description=description,
        displayName=display_name,
        inspectJob=inspect_job,
        triggers=trigger_schedule,
        status=self.msg.GooglePrivacyDlpV2JobTrigger.StatusValueValuesEnum.
        HEALTHY)

  def MakeJobTriggerCreateRequest(self, trigger_name, job_trigger):
    """Create test JobTriggersCreateRequest message."""
    create_request = self.msg.GooglePrivacyDlpV2CreateJobTriggerRequest(
        jobTrigger=job_trigger, triggerId=trigger_name)
    return self.msg.DlpProjectsJobTriggersCreateRequest(
        googlePrivacyDlpV2CreateJobTriggerRequest=create_request,
        parent='projects/' + self.Project())

  def MakeJobTriggerListRequest(self, order_by=None):
    """Create JobTriggersListRequest message."""
    return self.msg.DlpProjectsJobTriggersListRequest(
        parent='projects/' + self.Project(), orderBy=order_by)

  def MakeJobTriggerListResponse(self, count=3):
    """Create test ListJobTriggersResponse message."""
    job_triggers = []
    for i in range(count):
      job_trigger = self.MakeJobTrigger(
          description='My description{}'.format(i),
          display_name='Display_Name_{}'.format(i),
          input_params={
              'gcs_bucket': 'gs://my-bucket/',
              'project_id': self.Project()
          },
          input_type='gcs',
          info_types=['PHONE_NUMBER', 'PERSON_NAME'],
          min_likelihood='POSSIBLE',
          request_limit=100,
          item_limit=2,
          output_topics=['topic1', 'topic2'],
          duration='4500s')
      job_trigger.createTime = '2018-01-01T00:00:00.000000Z'
      job_trigger.updateTime = '2018-01-01T00:00:00.000000Z'
      job_triggers.append(job_trigger)
    return self.msg.GooglePrivacyDlpV2ListJobTriggersResponse(
        jobTriggers=job_triggers)

  def MakeJob(self, name, info_types=None, input_gcs_path=None,
              input_bq_table=None, input_bq_dataset=None, input_ds_kind=None,
              input_ds_namespace=None, output_topics=None, output_tables=None,
              file_size_limit=1024, exclude_info_types=False,
              include_quote=False, max_findings=1000, min_likelihood='POSSIBLE',
              max_findings_per_item=None, maxtime='2018-01-31T12:00:00.0000Z',
              mintime='2018-01-01T12:00:00.0000Z', input_bq_fields=None):
    """Make test Job."""
    info_types = info_types or ['LAST_NAME', 'EMAIL_ADDRESS']
    job = self.msg.GooglePrivacyDlpV2DlpJob()
    input_params = {
        'project_id': self.Project()
    }
    if input_gcs_path:
      input_params['gcs_bucket'] = input_gcs_path
      input_params['size_limit'] = file_size_limit
      input_type = 'gcs'
    elif input_bq_table:
      input_params['bt_data_set_id'] = input_bq_dataset
      input_params['bt_table_id'] = input_bq_table
      input_params['input_bq_fields'] = input_bq_fields
      input_type = 'table'
    else:
      input_params['ds_kind'] = input_ds_kind
      input_params['ds_namespace_id'] = input_ds_namespace
      input_type = 'datastore'

    if output_topics:
      actions = self._MakeTopicJobTriggerActions(output_topics)
    else:
      actions = self._MakeTableJobTriggerActions(output_tables)

    job.createTime = '2018-01-01T00:00:00.0000Z'
    job.inspectDetails = self.msg.GooglePrivacyDlpV2InspectDataSourceDetails(
        requestedOptions=self.msg.GooglePrivacyDlpV2RequestedOptions(
            jobConfig=self.msg.GooglePrivacyDlpV2InspectJobConfig(
                actions=actions,
                inspectConfig=self._GetInspectConfig(
                    info_types, min_likelihood, limit=max_findings,
                    include_quote=include_quote,
                    exclude_info_types=exclude_info_types,
                    item_limit=max_findings_per_item),
                storageConfig=self._GetJobInputConfig(input_params, input_type)
            )
        ),
        result=None,
    )
    if mintime or maxtime:
      (job.inspectDetails.requestedOptions.jobConfig.storageConfig.
       timespanConfig) = self.msg.GooglePrivacyDlpV2TimespanConfig(
           startTime=mintime, endTime=maxtime)
    job.name = name
    job.state = self.msg.GooglePrivacyDlpV2DlpJob.StateValueValuesEnum.DONE
    job.type = (
        self.msg.GooglePrivacyDlpV2DlpJob.TypeValueValuesEnum.INSPECT_JOB)
    return job

  def MakeJobListResponse(self, count=5):
    """Make test jobs list response."""
    jobs = []
    for i in range(count):
      jobs.append(self.MakeJob(name='Job_{}'.format(i),
                               input_gcs_path='gs://my-bucket/',
                               output_topics=['my_topic']))
    return self.msg.GooglePrivacyDlpV2ListDlpJobsResponse(jobs=jobs)

  def MakeJobListRequest(self):
    return self.msg.DlpProjectsDlpJobsListRequest(
        type=(
            self.msg.DlpProjectsDlpJobsListRequest.
            TypeValueValuesEnum.INSPECT_JOB),
        parent='projects/'+self.Project())

  def MakeJobCreateRequest(self, job_id, inspect_config=None,
                           risk_config=None):
    inner_request = self.msg.GooglePrivacyDlpV2CreateDlpJobRequest(
        inspectJob=inspect_config,
        jobId=job_id,
        riskJob=risk_config
    )
    return self.msg.DlpProjectsDlpJobsCreateRequest(
        googlePrivacyDlpV2CreateDlpJobRequest=inner_request,
        parent='projects/' + self.Project()
    )

  def MakeAnalysisJob(self, name, dataset, table, project, cat_stat_field=None,
                      num_stat_field=None, quasi_ids=None,
                      sensitive_field=None):
    """Build Dlp risk analysis job."""
    privacy_metric = self.msg.GooglePrivacyDlpV2PrivacyMetric()
    if cat_stat_field:
      field = self.msg.GooglePrivacyDlpV2FieldId(name=cat_stat_field)
      cat_stat_config = self.msg.GooglePrivacyDlpV2CategoricalStatsConfig(
          field=field)
      privacy_metric.categoricalStatsConfig = cat_stat_config
    elif num_stat_field:
      field = self.msg.GooglePrivacyDlpV2FieldId(name=num_stat_field)
      num_stat_config = self.msg.GooglePrivacyDlpV2NumericalStatsConfig(
          field=field)
      privacy_metric.numericalStatsConfig = num_stat_config
    elif quasi_ids:
      privacy_metric.lDiversityConfig = (
          self.msg.GooglePrivacyDlpV2LDiversityConfig())
      qids = [self.msg.GooglePrivacyDlpV2FieldId(name=qid) for qid in quasi_ids]
      privacy_metric.lDiversityConfig.quasiIds = qids
      if sensitive_field:
        privacy_metric.lDiversityConfig.sensitiveAttribute = (
            self.msg.GooglePrivacyDlpV2FieldId(name=sensitive_field))

    big_query_table = self.msg.GooglePrivacyDlpV2BigQueryTable(
        datasetId=dataset,
        projectId=project,
        tableId=table)

    job = self.msg.GooglePrivacyDlpV2DlpJob()
    job.createTime = '2018-01-01T00:00:00.0000Z'
    job.name = name
    job.state = self.msg.GooglePrivacyDlpV2DlpJob.StateValueValuesEnum.DONE
    job.type = (
        self.msg.GooglePrivacyDlpV2DlpJob.TypeValueValuesEnum.RISK_ANALYSIS_JOB)
    job.riskDetails = self.msg.GooglePrivacyDlpV2AnalyzeDataSourceRiskDetails()
    job.riskDetails.requestedSourceTable = big_query_table
    job.riskDetails.requestedPrivacyMetric = privacy_metric

    return job
