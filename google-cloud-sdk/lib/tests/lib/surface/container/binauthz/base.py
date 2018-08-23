# -*- coding: utf-8 -*- #
# Copyright 2014 Google Inc. All Rights Reserved.

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
"""Base classes for Binary Authorization tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

import datetime
import random
import uuid

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.container.binauthz import containeranalysis
from googlecloudsdk.api_lib.util import apis
from googlecloudsdk.calliope import base
from googlecloudsdk.core import properties
from tests.lib import cli_test_base
from tests.lib import e2e_utils
from tests.lib import sdk_test_base
from tests.lib import test_case

import six


def GetNoteRelativeName(project_id, note_id):
  return 'projects/{project_id}/notes/{note_id}'.format(
      project_id=project_id,
      note_id=note_id,
  )


def CreateUtcIsoNowTimestamp():
  # Python's default isoformat doesn't include the Z without an external
  # pytz dependency or extra verbose code.  Probably the exact timestamp
  # format doesn't matter here, but for consistency this is what the prod API
  # actually returns.
  return '{}Z'.format(datetime.datetime.utcnow().isoformat())


class WithEarlyCleanup(test_case.TestCase):
  """A mixin that provides a cleanup method that can make e.g. gcloud calls.

  Functions registered with the normal addCleanup method will after all other
  TearDown calls have been invoked. Among the normal TearDown side-effects are
  closing the std I/O handles which makes many cleanup tasks impossible.
  Notably, one cannot use SdkBase.Run in a standard addCleanup context.

  This class provides an AddEarlyCleanup method to execute cleanup tasks before
  the I/O closing occurs.
  """

  def SetUp(self):
    self._cleanup_calls = []

  def TearDown(self):
    while self._cleanup_calls:
      func, args, kwargs = self._cleanup_calls.pop()
      func(*args, **kwargs)

  def AddEarlyCleanup(self, func, *args, **kwargs):
    self._cleanup_calls.append((func, args, kwargs))


class BinauthzUnitTestBase(sdk_test_base.SdkBase):
  """Base class for BinAuthz unit tests with common setup and helpers."""

  ARTIFACT_URL_TEMPLATE = (
      'https://gcr.io/{project}/{image_name}@sha256:{random_sha256}')

  def GenerateValidBogusLookingRandomSha256(self, size=2**64):
    # Create a valid sha256 that is all 0's followed by a random decimal number.
    # This should make it obvious to any casual observer that the sha256 is
    # bogus and not from a real image.
    random_int = random.randint(0, size)
    return '{:0>64d}'.format(random_int)

  def GenerateArtifactUrl(self,
                          project='cloud-sdk-integration-testing',
                          image_name='fake_image'):
    return self.ARTIFACT_URL_TEMPLATE.format(
        project=project,
        image_name=image_name,
        random_sha256=self.GenerateValidBogusLookingRandomSha256())

  def RunBinauthz(self, cmd):
    prefix = ['container', 'binauthz']
    if isinstance(cmd, six.string_types):
      return self.Run(' '.join(prefix + [cmd]))
    return self.Run(prefix + cmd)

  def SetUp(self):
    self.track = base.ReleaseTrack.ALPHA
    self.containeranalysis_messages = apis.GetMessagesModule(
        containeranalysis.API_NAME,
        containeranalysis.DEFAULT_VERSION)
    self.note_id_generator = e2e_utils.GetResourceNameGenerator(
        prefix='test-aa-note')
    # Convenience aliases for commonly used messages.
    # pylint: disable=invalid-name
    self.Note = self.containeranalysis_messages.Note
    self.AttestationAuthority = (
        self.containeranalysis_messages.AttestationAuthority)
    self.BuildType = self.containeranalysis_messages.BuildType
    self.BuildSignature = self.containeranalysis_messages.BuildSignature
    self.Attestation = self.containeranalysis_messages.Attestation
    self.PgpSignedAttestation = (
        self.containeranalysis_messages.PgpSignedAttestation)
    self.SIMPLE_SIGNING_JSON = (
        self.PgpSignedAttestation.ContentTypeValueValuesEnum.SIMPLE_SIGNING_JSON
    )
    self.ProjectsNotesCreateRequest = (
        self.containeranalysis_messages.
        ContaineranalysisProjectsNotesCreateRequest)
    self.ProjectsOccurrencesCreateRequest = (
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesCreateRequest)
    self.Occurrence = self.containeranalysis_messages.Occurrence
    self.BuildDetails = self.containeranalysis_messages.BuildDetails
    self.ProjectsOccurrencesListRequest = (
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesListRequest)
    self.ListOccurrencesResponse = (
        self.containeranalysis_messages.ListOccurrencesResponse)
    self.ProjectsOccurrencesGetNotesRequest = (
        self.containeranalysis_messages.
        ContaineranalysisProjectsOccurrencesGetNotesRequest)
    self.ListNoteOccurrencesRequest = (
        self.containeranalysis_messages.
        ContaineranalysisProjectsNotesOccurrencesListRequest)
    self.ListNoteOccurrencesResponse = (
        self.containeranalysis_messages.ListNoteOccurrencesResponse)
    # pylint: enable=invalid-name


class BinauthzMockedPolicyClientUnitTest(sdk_test_base.WithFakeAuth,
                                         BinauthzUnitTestBase,
                                         cli_test_base.CliTestBase):
  """Base class for BinAuthz unit tests with mocked policy service."""

  def SetUp(self):
    self.client = mock.Client(
        apis.GetClientClass('binaryauthorization', 'v1alpha2'),
        real_client=apis.GetClientInstance(
            'binaryauthorization', 'v1alpha2', no_http=True),
    )
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

    self.messages = self.client.MESSAGES_MODULE


class BinauthzMockedBetaPolicyClientUnitTest(sdk_test_base.WithFakeAuth,
                                             BinauthzUnitTestBase,
                                             cli_test_base.CliTestBase):
  """Base class for BinAuthz unit tests with mocked beta policy service."""

  def SetUp(self):
    self.track = base.ReleaseTrack.BETA
    self.client = mock.Client(
        apis.GetClientClass('binaryauthorization', 'v1beta1'),
        real_client=apis.GetClientInstance(
            'binaryauthorization', 'v1beta1', no_http=True),
    )
    self.client.Mock()
    self.addCleanup(self.client.Unmock)

    self.messages = self.client.MESSAGES_MODULE


class BinauthzMockedCAClientTestBase(sdk_test_base.WithFakeAuth,
                                     BinauthzUnitTestBase):
  """Base class for BinAuthz unit tests with mocked service dependencies."""

  def Project(self):
    return 'fake-project'

  def SetUp(self):
    properties.VALUES.core.project.Set(self.Project())
    # We could also pass the mocked containeranalysis client explicitly
    # to the ContainerAnalysisClient constructor, but in CLI tests we rely
    # on a non-explicitly constructed client still being mocked even though
    # it gets its underlying client in the normal way using
    # apis.GetClientInstance.
    self.mocked_containeranalysis_client = mock.Client(
        apis.GetClientClass('containeranalysis', 'v1alpha1'),
        real_client=apis.GetClientInstance(
            'containeranalysis', 'v1alpha1', no_http=True))
    self.mocked_containeranalysis_client.Mock()
    self.addCleanup(self.mocked_containeranalysis_client.Unmock)
    self.artifact_url = self.GenerateArtifactUrl()

  def CreateGenericResponseOccurrence(self, kind, note_name, resource_url,
                                      project_ref, **kwargs):
    """Create an Occurrence as expected from a call to projects_notes.Create.

    All arguments are just threaded through to the resulting occurrence.  This
      method is a utility for the common operation of generating a UUID and
      appropriate timestamps for mocked return occurrences.

    Args:
      kind: The kind of the occurrence. (self.Occurrence.KindValueValuesEnum)
      note_name: The note to which the occurrence is bound. (string)
      resource_url: The resource/artifact URL that the occurrence is attached
        to. (string)
      project_ref: Project where to expect created Occurrence.
        (cloudresourcemanager.projects Resource)
      **kwargs: The passed keyword arguments are threaded directly through to
        the Occurrence constructor.  These should be used to provide the values
        of any kind-specific one_ofs (e.g. `attestation` or `build_details`).

    Returns:
      Occurrence.
    """
    # The resulting name is the projects occurrences directory followed by a
    # UUID for this new Occurrence.
    # e.g.
    # 'projects/cloud-sdk-integration-testing/occurrences/'
    # 'cfc80669-e102-45b6-aec2-98501d0cc3e9'
    expected_name = '{project_dir}/occurrences/{occurrence_id}'.format(
        project_dir=project_ref.RelativeName(),
        occurrence_id=uuid.uuid4(),
    )
    now_timestamp = CreateUtcIsoNowTimestamp()
    return self.Occurrence(
        name=expected_name,
        createTime=now_timestamp,
        updateTime=now_timestamp,
        # The rest is identical to the passed arguments.
        kind=kind,
        noteName=note_name,
        resourceUrl=resource_url,
        **kwargs)

  def ExpectProjectsOccurrencesCreate(self, request_occurrence, project_ref):
    """Call projects_occurrences.Create.Expect on the mocked client.

    Args:
      request_occurrence: The Occurrence (as returned by
        `CreateRequestOccurrence`) to expect as an argument to
        projects_occurrences.Create. (containeranalysis_messages.Occurrence)
      project_ref: Project where to expect created Occurrence.
        (cloudresourcemanager.projects Resource)

    Returns:
      The occurrence that the mocked API call will return. (Occurrence)
    """
    parent = project_ref.RelativeName()
    response_occurrence = self.CreateResponseOccurrence(
        request_occurrence=request_occurrence,
        project_ref=project_ref,
    )
    self.mocked_containeranalysis_client.projects_occurrences.Create.Expect(
        request=self.ProjectsOccurrencesCreateRequest(
            name=None,
            occurrence=request_occurrence,
            parent=parent,
        ),
        response=response_occurrence,
    )
    return response_occurrence

  def ExpectProjectsOccurrencesList(
      self,
      project_ref,
      expected_filter_content=None,
      occurrences_to_return=None,
  ):
    """Call projects_occurrences.List.Expect with the provided params.

    Args:
      project_ref: Project where to expect listed Occurrences, as passed to
        `ProjectsOccurrencesListRequest`.
        (cloudresourcemanager.projects Resource)
      expected_filter_content: The expected value of `filter`, as passed to
        `ProjectsOccurrencesListRequest`. (string)
      occurrences_to_return: The mocked response.  If it is not passed,
        the response will be an empty list. (List of Occurrence)
    """
    occurrences_to_return = occurrences_to_return or []
    self.mocked_containeranalysis_client.projects_occurrences.List.Expect(
        request=self.ProjectsOccurrencesListRequest(
            parent=project_ref.RelativeName(),
            filter=expected_filter_content,
            pageSize=100,
        ),
        response=self.ListOccurrencesResponse(
            occurrences=occurrences_to_return),
    )

  def ExpectProjectsOccurrencesGetNotes(self, occurrence_name, expected_note):
    self.mocked_containeranalysis_client.projects_occurrences.GetNotes.Expect(
        request=self.ProjectsOccurrencesGetNotesRequest(name=occurrence_name),
        response=expected_note,
    )


class BinauthzMockedClientTestBase(BinauthzMockedCAClientTestBase):
  """Base class for BinAuthz unit tests with mocked CA client."""

  def SetUp(self):
    self.ca_client = containeranalysis.Client()

  def CreateRequestOccurrence(
      self,
      note_ref,
      pgp_key_fingerprint,
      signature,
      artifact_url,
      project_ref,
  ):
    """Creates an Occurrence object suitable to use in creation requests.

    Args:
      note_ref: The Note reference that the created Occurrence will be
        bound to. (containeranalysis.projects.notes Resource)
      pgp_key_fingerprint: The ID of the public key that will be used to verify
        the signature (string).
      signature: The content artifact's signature (string), in the gpg
        clearsigned, ASCII-armored format.  Normally this is generated by
        running
        `gpg -u attesting_user@example.com --armor --clearsign`
        over the output of `CreateSignaturePayload`.
      artifact_url: URL of artifact to which the signature is associated.
        (string)
      project_ref: Project where to create Occurrence.
        (cloudresourcemanager.projects Resource)

    Returns:
      Occurrence. This is linked to the appropriate Note, but does not
        have an ID set.
    """
    content_type = (
        self.PgpSignedAttestation.ContentTypeValueValuesEnum.SIMPLE_SIGNING_JSON
    )
    kind = self.Occurrence.KindValueValuesEnum.ATTESTATION_AUTHORITY
    attestation = self.Attestation(
        pgpSignedAttestation=self.PgpSignedAttestation(
            contentType=content_type,
            signature=signature,
            pgpKeyId=pgp_key_fingerprint,
        ))
    return self.Occurrence(
        attestation=attestation,
        kind=kind,
        noteName=note_ref.RelativeName(),
        resourceUrl=artifact_url,
    )

  def CreateResponseOccurrence(self, request_occurrence, project_ref):
    """Create an Occurrence as expected from a call to projects_notes.Create.

    Args:
      request_occurrence: The Occurrence (as returned by
        `CreateRequestOccurrence`) to expect as an argument to
        projects_occurrences.Create. (containeranalysis_messages.Occurrence)
      project_ref: Project where to expect created Occurrence.
        (cloudresourcemanager.projects Resource)

    Returns:
      Occurrence.  This has a randomly generated name in the `project_ref`
        namespace and `createTime`/`updateTime` set to approximately "now".  All
        other attributes are derived from the `request_occurrence`.
    """
    return self.CreateGenericResponseOccurrence(
        project_ref=project_ref,
        kind=request_occurrence.kind,
        note_name=request_occurrence.noteName,
        resource_url=request_occurrence.resourceUrl,
        attestation=request_occurrence.attestation,
    )

  def ExpectProjectsNotesOccurrencesList(
      self,
      note_relative_name,
      expected_filter_content=None,
      occurrences_to_return=None,
  ):
    """Call projects_occurrences.List.Expect with the provided params.

    Args:
      note_relative_name: The Note resource relative name that the Occurrence is
        bound to. (string)
      expected_filter_content: The expected value of `filter`, as passed to
        `ProjectsOccurrencesListRequest`. (string)
      occurrences_to_return: The mocked response.  If it is not passed,
        the response will be an empty list. (List of Occurrence)
    """
    occurrences_to_return = occurrences_to_return or []
    self.mocked_containeranalysis_client.projects_notes_occurrences.List.Expect(
        request=self.ListNoteOccurrencesRequest(
            name=note_relative_name,
            filter=expected_filter_content,
            pageSize=100),
        response=self.ListNoteOccurrencesResponse(
            occurrences=occurrences_to_return))
