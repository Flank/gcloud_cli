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
from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.command_lib.util.apis import arg_utils
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import parameterized
from tests.lib import sdk_test_base


class DlpUnitTestBase(sdk_test_base.WithFakeAuth,
                      cli_test_base.CliTestBase,
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

  def MakeShortMessages(self):
    """Shorten message names for convenience."""
    # Inspect
    self.content_inspect_req = self.messages.DlpProjectsContentInspectRequest
    self.inspect_content_req = (
        self.messages.GooglePrivacyDlpV2InspectContentRequest)
    self.content_item = self.messages.GooglePrivacyDlpV2ContentItem
    self.inspect_config = self.messages.GooglePrivacyDlpV2InspectConfig
    self.info_type_msg = self.messages.GooglePrivacyDlpV2InfoType
    self.finding_limit_msg = self.messages.GooglePrivacyDlpV2FindingLimits
    self.minlikelihood_enum = (self.messages.GooglePrivacyDlpV2InspectConfig.
                               MinLikelihoodValueValuesEnum)
    self.content_inspect_resp = (self.messages.
                                 GooglePrivacyDlpV2InspectContentResponse)
    self.inspect_result = self.messages.GooglePrivacyDlpV2InspectResult
    self.privacy_finding = self.messages.GooglePrivacyDlpV2Finding
    self.likelihoodvalue_enum = (self.privacy_finding.LikelihoodValueValuesEnum)
    self.finding_location = self.messages.GooglePrivacyDlpV2Location
    self.finding_range = self.messages.GooglePrivacyDlpV2Range
    self.content_location = (
        self.messages.GooglePrivacyDlpV2ContentLocation)
    self.image_location = self.messages.GooglePrivacyDlpV2ImageLocation
    self.bounds = self.messages.GooglePrivacyDlpV2BoundingBox
    self.byte_item = self.messages.GooglePrivacyDlpV2ByteContentItem
    self.file_type_enum = self.byte_item.TypeValueValuesEnum

    # Deidentify/Redact
    self.content_redact_req = self.messages.DlpProjectsContentDeidentifyRequest
    self.redact_content_req = (
        self.messages.GooglePrivacyDlpV2DeidentifyContentRequest)

    self.deidentify_config = self.messages.GooglePrivacyDlpV2DeidentifyConfig
    self.infotype_transforms = (
        self.messages.GooglePrivacyDlpV2InfoTypeTransformations)
    self.info_transform = self.messages.GooglePrivacyDlpV2InfoTypeTransformation
    self.primitive_transform = (
        self.messages.GooglePrivacyDlpV2PrimitiveTransformation)
    self.redact_config = self.messages.GooglePrivacyDlpV2RedactConfig
    self.replace_config = self.messages.GooglePrivacyDlpV2ReplaceValueConfig
    self.infotype_replace_config = (
        self.messages.GooglePrivacyDlpV2ReplaceWithInfoTypeConfig)

    self.content_redact_resp = (
        self.messages.GooglePrivacyDlpV2DeidentifyContentResponse)
    self.redact_resp_overview = (
        self.messages.GooglePrivacyDlpV2TransformationOverview)
    self.transform_summary = (
        self.messages.GooglePrivacyDlpV2TransformationSummary)
    self.tansform_summary_result = self.messages.GooglePrivacyDlpV2SummaryResult
    self.result_code_enum = self.tansform_summary_result.CodeValueValuesEnum
    self.value_holder = self.messages.GooglePrivacyDlpV2Value

    self.dlp_redact_image_request = self.messages.DlpProjectsImageRedactRequest
    self.image_redact_request = (
        self.messages.GooglePrivacyDlpV2RedactImageRequest)
    self.image_redact_config = (
        self.messages.GooglePrivacyDlpV2ImageRedactionConfig)
    self.image_redact_response = (
        self.messages.GooglePrivacyDlpV2RedactImageResponse)
    self.redact_color = self.messages.GooglePrivacyDlpV2Color

  def SetUp(self):
    properties.VALUES.core.user_output_enabled.Set(False)
    self.messages = apis.GetMessagesModule('dlp', 'v2')
    self.client = mock.Client(apis.GetClientClass('dlp', 'v2'))
    self.client.Mock()
    self.addCleanup(self.client.Unmock)
    self.zone = 'us-central1-c'
    properties.VALUES.compute.zone.Set(self.zone)
    self.StartPatch('time.sleep')
    self.MakeShortMessages()

  def _GetInspectConfig(self, info_types, min_likelihood, limit,
                        include_quote, exclude_info_types):
    limits = self.finding_limit_msg(maxFindingsPerRequest=limit or 1000)
    return self.inspect_config(
        excludeInfoTypes=exclude_info_types,
        includeQuote=include_quote,
        infoTypes=[self.info_type_msg(name=v) for v in info_types],
        limits=limits,
        minLikelihood=arg_utils.ChoiceToEnum(min_likelihood,
                                             self.minlikelihood_enum))

  def MakeTextInspectRequest(self, content, info_types,
                             min_likelihood, limit,
                             include_quote=False, exclude_info_types=False):

    inner_request = self.inspect_content_req(
        inspectConfig=self._GetInspectConfig(info_types, min_likelihood, limit,
                                             include_quote, exclude_info_types),
        item=self.content_item(value=content))

    return self.content_inspect_req(
        parent='projects/' + self.Project(),
        googlePrivacyDlpV2InspectContentRequest=inner_request)

  def _MakeTextFindings(self, likelihood, info_types, count,
                        include_quote=False, exclude_info_types=False):
    findings = []
    count = count or 1000
    for x in range(count):
      quote = 'finding {}'.format(x+1) if include_quote else None
      infotype = self.info_type_msg(name=info_types[x % len(info_types)])
      f = self.privacy_finding(
          createTime='2018-01-01T00:00:{}0.000Z'.format(x),
          infoType=None if exclude_info_types else infotype,
          likelihood=arg_utils.ChoiceToEnum(likelihood,
                                            self.likelihoodvalue_enum),
          location=self.finding_location(
              byteRange=self.finding_range(end=23, start=11),
              codepointRange=self.finding_range(end=23, start=11)),
          quote=quote)
      findings.append(f)
    return findings

  def MakeTextInspectResponse(self, likelihood, info_types, limit,
                              include_quote=False, exclude_info_types=False):
    info_types = info_types
    response = self.content_inspect_resp(
        result=self.inspect_result(
            findings=self._MakeTextFindings(
                likelihood, info_types, exclude_info_types=exclude_info_types,
                include_quote=include_quote, count=limit)))
    return response

  def _GetTransform(self, redaction_type, replacement=None):
    if redaction_type == 'info-type':
      primative_transform = self.primitive_transform(
          replaceWithInfoTypeConfig=self.infotype_replace_config())
    elif redaction_type == 'text':
      primative_transform = self.primitive_transform(
          replaceConfig=self.replace_config(newValue=self.value_holder(
              stringValue=replacement)))
    else:
      primative_transform = self.primitive_transform(
          redactConfig=self.redact_config())

    return self.info_transform(primitiveTransformation=primative_transform)

  def _GetDeidentifyConfig(self, redaction_type, replacement=None):
    transform = self._GetTransform(redaction_type, replacement)
    transform_wrapper = self.infotype_transforms(transformations=[transform])
    return self.deidentify_config(infoTypeTransformations=transform_wrapper)

  def MakeTextRedactRequest(self, content, info_types, min_likelihood,
                            redaction_type, replacement=None):
    inspect_config = self._GetInspectConfig(info_types, min_likelihood, None,
                                            None, None)
    inspect_config.limits = None
    inner_request = self.redact_content_req(
        inspectConfig=inspect_config,
        deidentifyConfig=self._GetDeidentifyConfig(redaction_type,
                                                   replacement),
        item=self.content_item(value=content))

    return self.content_redact_req(
        parent='projects/' + self.Project(),
        googlePrivacyDlpV2DeidentifyContentRequest=inner_request)

  def _MakeTransformSummaries(self, info_types, transform, count=3):
    summaries = []
    for x in range(count):
      infotype = self.info_type_msg(name=info_types[x % len(info_types)])
      summary = self.transform_summary(
          infoType=infotype,
          results=[self.tansform_summary_result(
              code=self.result_code_enum.SUCCESS, count=1)],
          transformation=transform,
          transformedBytes=33)
      summaries.append(summary)
    return summaries

  def MakeTextRedactResponse(self, content, likelihood, info_types,
                             redaction_type, replacement):
    info_type_tf = self._GetTransform(redaction_type, replacement)
    transform = info_type_tf.primitiveTransformation
    overview = self.redact_resp_overview(
        transformationSummaries=self._MakeTransformSummaries(info_types,
                                                             transform),
        transformedBytes=255)
    return self.content_redact_resp(item=self.content_item(value=content),
                                    overview=overview)

  def _MakeImageFindings(self, likelihood, info_types, count,
                         include_quote=False, exclude_info_types=False):
    findings = []
    count = count or 1000
    for x in range(count):
      quote = 'finding {}'.format(x+1) if include_quote else None
      infotype = self.info_type_msg(name=info_types[x % len(info_types)])
      f = self.privacy_finding(
          createTime='2018-01-01T00:00:{}0.000Z'.format(x),
          infoType=None if exclude_info_types else infotype,
          likelihood=arg_utils.ChoiceToEnum(likelihood,
                                            self.likelihoodvalue_enum),
          location=self.finding_location(
              contentLocations=[
                  self.content_location(
                      imageLocation=self.image_location(
                          boundingBoxes=[self.bounds(height=46, left=150,
                                                     top=179, width=122)]))
              ]),
          quote=quote)
      findings.append(f)
    return findings

  def MakeImageInspectRequest(self, content, info_types, min_likelihood, limit,
                              include_quote=False, exclude_info_types=False,
                              file_type='IMAGE'):
    image_content_item = self.byte_item(data=content,
                                        type=arg_utils.ChoiceToEnum(
                                            file_type, self.file_type_enum))
    inner_request = self.inspect_content_req(
        inspectConfig=self._GetInspectConfig(info_types, min_likelihood, limit,
                                             include_quote, exclude_info_types),
        item=self.content_item(byteItem=image_content_item))

    return self.content_inspect_req(
        parent='projects/' + self.Project(),
        googlePrivacyDlpV2InspectContentRequest=inner_request)

  def MakeImageInspectResponse(self, likelihood, info_types, limit,
                               include_quote=False, exclude_info_types=False):
    info_types = info_types
    response = self.content_inspect_resp(
        result=self.inspect_result(
            findings=self._MakeImageFindings(
                likelihood, info_types, exclude_info_types=exclude_info_types,
                include_quote=include_quote, count=limit)))
    return response

  def _MakeRedactColor(self, color_string):
    if not color_string:
      return None
    red, green, blue = [float(x) for x in color_string.split(',')]
    return self.redact_color(red=red, green=green, blue=blue)

  def MakeImageRedactRequest(self, file_type, info_types, min_likelihood,
                             include_quote, remove_text=False,
                             redact_color_string=None):
    image_content_item = self.byte_item(data=self.TEST_IMG_CONTENT,
                                        type=arg_utils.ChoiceToEnum(
                                            file_type, self.file_type_enum))
    image_redaction_config = self.image_redact_config(
        redactAllText=remove_text,
        redactionColor=self._MakeRedactColor(redact_color_string))
    inner_request = self.image_redact_request(
        byteItem=image_content_item,
        inspectConfig=self._GetInspectConfig(info_types, min_likelihood, None,
                                             include_quote, None),
        imageRedactionConfigs=[image_redaction_config]
    )
    inner_request.inspectConfig.limits = None
    return self.dlp_redact_image_request(
        googlePrivacyDlpV2RedactImageRequest=inner_request,
        parent='projects/' + self.Project())

  def MakeImageRedactResponse(self):
    return self.image_redact_response(extractedText='Foo',
                                      redactedImage=self.TEST_IMG_CONTENT)
