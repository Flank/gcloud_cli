# -*- coding: utf-8 -*- #
# Copyright 2014 Google LLC. All Rights Reserved.

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
import functools
import random
import uuid

from apitools.base.py.testing import mock
from googlecloudsdk.api_lib.util import apis
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case

import six

ARTIFACT_URL_TEMPLATE = (
    'https://gcr.io/{project}/{image_name}@sha256:{random_sha256}')


def GenerateValidBogusLookingRandomSha256(size=2**64):
  # Create a valid sha256 that is all 0's followed by a random decimal number.
  # This should make it obvious to any casual observer that the sha256 is
  # bogus and not from a real image.
  random_int = random.randint(0, size)
  return '{:0>64d}'.format(random_int)


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
  """A mixin that allows adding cleanup methods for things like gcloud calls.

  Functions registered with the normal addCleanup method will after all other
  TearDown calls have been invoked. Among the normal TearDown side-effects are
  closing the std I/O handles which makes many cleanup tasks impossible.
  Notably, one cannot use SdkBase.Run in a standard addCleanup context.

  This class provides an AddEarlyCleanup method to execute cleanup tasks before
  the I/O closing occurs.
  """

  def SetUp(self):
    self._cleanup_callbacks = []

  def TearDown(self):
    while self._cleanup_callbacks:
      self._cleanup_callbacks.pop()()

  def AddEarlyCleanup(self, func, *args, **kwargs):
    self._cleanup_callbacks.append(functools.partial(func, *args, **kwargs))


class BinauthzTestBase(cli_test_base.CliTestBase):
  """Base class for BinAuthz unit tests with common setup and helpers."""

  def GenerateArtifactUrl(self, project=None, image_name='fake_image'):
    if project is None:
      project = self.Project()
    return ARTIFACT_URL_TEMPLATE.format(
        project=project,
        image_name=image_name,
        random_sha256=GenerateValidBogusLookingRandomSha256())

  def RunBinauthz(self, cmd, track=None):
    prefix = ['container', 'binauthz']
    if isinstance(cmd, six.string_types):
      return self.Run(' '.join(prefix + [cmd]), track=track)
    return self.Run(prefix + cmd, track=track)


class _MockClientMixin(sdk_test_base.WithFakeAuth):

  def CreateMockClient(self, api_name, api_version):
    client = mock.Client(
        apis.GetClientClass(api_name, api_version),
        real_client=apis.GetClientInstance(api_name, api_version, no_http=True))
    client.Mock()
    self.addCleanup(client.Unmock)
    return client


class WithMockAlphaBinauthz(_MockClientMixin):
  """Base class for BinAuthz unit tests with mocked policy service."""

  def PreSetUp(self):
    self.mock_client = self.CreateMockClient('binaryauthorization', 'v1alpha2')
    self.messages = self.mock_client.MESSAGES_MODULE


class WithMockBetaBinauthz(_MockClientMixin):
  """Base class for BinAuthz unit tests with mocked beta policy service."""

  def PreSetUp(self):
    self.mock_client = self.CreateMockClient('binaryauthorization', 'v1beta1')
    self.messages = self.mock_client.MESSAGES_MODULE


class WithMockGaBinauthz(_MockClientMixin):
  """Base class for BinAuthz unit tests with mocked beta policy service."""

  def PreSetUp(self):
    self.mock_client = self.CreateMockClient('binaryauthorization', 'v1')
    self.messages = self.mock_client.MESSAGES_MODULE


class WithMockBetaContaineranalysis(_MockClientMixin):
  """Base class for BinAuthz unit tests with mocked service dependencies."""

  def PreSetUp(self):
    self.mock_ca_client = self.CreateMockClient('containeranalysis', 'v1beta1')
    self.ca_messages = apis.GetMessagesModule('containeranalysis', 'v1beta1')

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
    return self.ca_messages.Occurrence(
        name=expected_name,
        createTime=now_timestamp,
        updateTime=now_timestamp,
        # The rest is identical to the passed arguments.
        kind=kind,
        noteName=note_name,
        resource=self.ca_messages.Resource(uri=resource_url),
        **kwargs)

  def ExpectProjectsOccurrencesCreate(self, request_occurrence, project_ref):
    """Call projects_occurrences.Create.Expect on the mocked client.

    Args:
      request_occurrence: The Occurrence (as returned by
        `CreateRequestOccurrence`) to expect as an argument to
        projects_occurrences.Create. (ca_messages.Occurrence)
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
    self.mock_ca_client.projects_occurrences.Create.Expect(
        request=self.ca_messages
        .ContaineranalysisProjectsOccurrencesCreateRequest(
            occurrence=request_occurrence,
            parent=parent,
        ),
        response=response_occurrence,
    )
    return response_occurrence

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
      note_ref: The Note reference that the created Occurrence will be bound to.
        (containeranalysis.projects.notes Resource)
      pgp_key_fingerprint: The ID of the public key that will be used to verify
        the signature (string).
      signature: The content artifact's signature (string), in the gpg
        clearsigned, ASCII-armored format.  Normally this is generated by
        running `gpg -u attesting_user@example.com --armor --clearsign` over the
        output of `CreateSignaturePayload`.
      artifact_url: URL of artifact to which the signature is associated.
        (string)
      project_ref: Project where to create Occurrence.
        (cloudresourcemanager.projects Resource)

    Returns:
      Occurrence. This is linked to the appropriate Note, but does not
        have an ID set.
    """
    attestation = self.ca_messages.Attestation(
        pgpSignedAttestation=self.ca_messages.PgpSignedAttestation(
            contentType=(self.ca_messages.PgpSignedAttestation
                         .ContentTypeValueValuesEnum.SIMPLE_SIGNING_JSON),
            signature=signature,
            pgpKeyId=pgp_key_fingerprint,
        ))
    return self.ca_messages.Occurrence(
        attestation=self.ca_messages.Details(attestation=attestation),
        kind=(self.ca_messages.Occurrence.KindValueValuesEnum.ATTESTATION),
        noteName=note_ref.RelativeName(),
        resource=self.ca_messages.Resource(uri=artifact_url),
    )

  def CreateGenericRequestOccurrence(
      self,
      note_ref,
      plaintext,
      signatures,
      artifact_url,
      project_ref,
  ):
    """Creates a GenericSignedAttestation Occurrence object for use in creation requests.

    Args:
      note_ref: The Note reference that the created Occurrence will be bound to.
        (containeranalysis.projects.notes Resource)
      plaintext: The data that was signed by the provided signatures.
      signatures: List[Tuple[string, string]] The key_id-signature pairs
        comprising the containeranalysis Signatures to be added to the
        Occurrence.
      artifact_url: URL of artifact to which the signature is associated.
        (string)
      project_ref: Project where to create Occurrence.
        (cloudresourcemanager.projects Resource)

    Returns:
      Occurrence. This is linked to the appropriate Note, but does not
        have an ID set.
    """
    attestation = self.ca_messages.Attestation(
        genericSignedAttestation=self.ca_messages.GenericSignedAttestation(
            contentType=(self.ca_messages.GenericSignedAttestation
                         .ContentTypeValueValuesEnum.SIMPLE_SIGNING_JSON),
            serializedPayload=plaintext,
            signatures=[
                self.ca_messages.Signature(publicKeyId=key_id, signature=sig)
                for (key_id, sig) in signatures
            ],
        ),)
    return self.ca_messages.Occurrence(
        attestation=self.ca_messages.Details(attestation=attestation),
        kind=(self.ca_messages.Occurrence.KindValueValuesEnum.ATTESTATION),
        noteName=note_ref.RelativeName(),
        resource=self.ca_messages.Resource(uri=artifact_url),
    )

  # TODO(b/138859339): Remove this line once all binauthz commands use v1
  # Occurrences.
  CreateRequestAttestationOccurrence = CreateGenericRequestOccurrence  # pylint: disable=invalid-name

  def CreateResponseOccurrence(self, request_occurrence, project_ref):
    """Create an Occurrence as expected from a call to projects_notes.Create.

    Args:
      request_occurrence: The Occurrence (as returned by
        `CreateRequestOccurrence`) to expect as an argument to
        projects_occurrences.Create. (ca_messages.Occurrence)
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
        resource_url=request_occurrence.resource.uri,
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
      occurrences_to_return: The mocked response.  If it is not passed, the
        response will be an empty list. (List of Occurrence)
    """
    occurrences_to_return = occurrences_to_return or []
    self.mock_ca_client.projects_notes_occurrences.List.Expect(
        request=self.ca_messages
        .ContaineranalysisProjectsNotesOccurrencesListRequest(
            name=note_relative_name,
            filter=expected_filter_content,
            pageSize=100),
        response=self.ca_messages.ListNoteOccurrencesResponse(
            occurrences=occurrences_to_return))


class WithMockV1Containeranalysis(_MockClientMixin):
  """Base class for BinAuthz unit tests with mocked service dependencies."""

  def PreSetUp(self):
    self.mock_ca_client = self.CreateMockClient('containeranalysis', 'v1')
    self.ca_messages = apis.GetMessagesModule('containeranalysis', 'v1')

  def ExpectProjectsOccurrencesCreate(self, request_occurrence, project_ref):
    """Call projects_occurrences.Create.Expect on the mocked client.

    Args:
      request_occurrence: The V1 Occurrence (as returned by
        `CreateRequestOccurrence`) to expect as an argument to
        projects_occurrences.Create. (ca_messages.Occurrence)
      project_ref: Project where to expect created Occurrence.
        (cloudresourcemanager.projects Resource)

    Returns:
      The v1 occurrence that the mocked API call will return. (Occurrence)
    """
    parent = project_ref.RelativeName()
    response_occurrence = self.CreateResponseOccurrence(
        request_occurrence=request_occurrence,
        project_ref=project_ref,
    )
    self.mock_ca_client.projects_occurrences.Create.Expect(
        request=self.ca_messages
        .ContaineranalysisProjectsOccurrencesCreateRequest(
            occurrence=request_occurrence,
            parent=parent,
        ),
        response=response_occurrence,
    )
    return response_occurrence

  def CreateRequestAttestationOccurrence(
      self,
      note_ref,
      plaintext,
      signatures,
      artifact_url,
      project_ref,
  ):
    """Creates a v1 AttestationOccurrence Occurrence object.

    Args:
      note_ref: The Note reference that the created Occurrence will be bound to.
        (containeranalysis.projects.notes Resource)
      plaintext: The data that was signed by the provided signatures.
      signatures: List[Tuple[string, string]] The key_id-signature pairs
        comprising the containeranalysis Signatures to be added to the
        Occurrence.
      artifact_url: URL of artifact to which the signature is associated.
        (string)
      project_ref: Project where to create Occurrence.
        (cloudresourcemanager.projects Resource)

    Returns:
      Occurrence. This is linked to the appropriate Note, but does not
        have an ID set.
    """
    attestation = self.ca_messages.AttestationOccurrence(
        serializedPayload=plaintext,
        signatures=[
            self.ca_messages.Signature(publicKeyId=key_id, signature=sig)
            for (key_id, sig) in signatures
        ],
    )
    return self.ca_messages.Occurrence(
        attestation=attestation,
        kind=(self.ca_messages.Occurrence.KindValueValuesEnum.ATTESTATION),
        noteName=note_ref.RelativeName(),
        resourceUri=artifact_url,
    )

  # TODO(b/138859339): Remove this line once all binauthz commands use v1
  # Occurrences.
  CreateGenericRequestOccurrence = CreateRequestAttestationOccurrence  # pylint: disable=invalid-name

  def CreateResponseAttestationOccurrence(self, kind, note_name, resource_url,
                                          project_ref, **kwargs):
    """Create a v1 Occurrence as expected from a call to projects_notes.Create.

    All arguments are just threaded through to the resulting occurrence. This
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
    return self.ca_messages.Occurrence(
        name=expected_name,
        createTime=now_timestamp,
        updateTime=now_timestamp,
        # The rest is identical to the passed arguments.
        kind=kind,
        noteName=note_name,
        resourceUri=resource_url,
        **kwargs)

  def CreateResponseOccurrence(self, request_occurrence, project_ref):
    """Create a v1 Occurrence as expected from a call to projects_notes.Create.

    Args:
      request_occurrence: The v1 Occurrence (as returned by
        `CreateRequestOccurrence`) to expect as an argument to
        projects_occurrences.Create. (ca_messages.Occurrence)
      project_ref: Project where to expect created v1 Occurrence.
        (cloudresourcemanager.projects Resource)

    Returns:
      Occurrence.  This has a randomly generated name in the `project_ref`
        namespace and `createTime`/`updateTime` set to approximately "now".  All
        other attributes are derived from the `request_occurrence`.
    """
    return self.CreateResponseAttestationOccurrence(
        project_ref=project_ref,
        kind=request_occurrence.kind,
        note_name=request_occurrence.noteName,
        resource_url=request_occurrence.resourceUri,
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
      occurrences_to_return: The mocked response.  If it is not passed, the
        response will be an empty list. (List of Occurrence)
    """
    occurrences_to_return = occurrences_to_return or []
    self.mock_ca_client.projects_notes_occurrences.List.Expect(
        request=self.ca_messages
        .ContaineranalysisProjectsNotesOccurrencesListRequest(
            name=note_relative_name,
            filter=expected_filter_content,
            pageSize=100),
        response=self.ca_messages.ListNoteOccurrencesResponse(
            occurrences=occurrences_to_return))


class WithMockKms(_MockClientMixin):
  """Base class for BinAuthz unit tests with mocked service dependencies."""

  def PreSetUp(self):
    self.mock_kms_client = self.CreateMockClient('cloudkms', 'v1')
    self.kms_messages = apis.GetMessagesModule('cloudkms', 'v1')
