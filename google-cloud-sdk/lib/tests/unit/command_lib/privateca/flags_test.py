# Lint as: python3
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
"""Tests for google3.third_party.py.googlecloudsdk.command_lib.privateca.flags."""

from __future__ import absolute_import
from __future__ import division
from __future__ import unicode_literals

from googlecloudsdk.api_lib.privateca import base as privateca_base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.privateca import flags
from googlecloudsdk.command_lib.privateca import resource_args
from googlecloudsdk.command_lib.util.concepts import concept_parsers
from tests.lib import cli_test_base
from tests.lib import sdk_test_base
from tests.lib import test_case
from tests.lib.calliope import util


class FlagsTest(cli_test_base.CliTestBase, sdk_test_base.WithLogCapture):

  def SetUp(self):
    self.parser = util.ArgumentParser()
    self.messages = privateca_base.GetMessagesModule()

  def testPublishCaCertFlag(self):
    flags.AddPublishCaCertFlag(self.parser)
    args = self.parser.parse_args(['--no-publish-ca-cert'])
    self.assertFalse(args.publish_ca_cert)

  def testPublishCrlFlag(self):
    flags.AddPublishCrlFlag(self.parser)
    args = self.parser.parse_args(['--no-publish-crl'])
    self.assertFalse(args.publish_crl)

  def testPublishFlagsDefault(self):
    flags.AddPublishCaCertFlag(self.parser)
    flags.AddPublishCrlFlag(self.parser)
    args = self.parser.parse_args(['--publish-ca-cert'])
    self.assertTrue(args.publish_ca_cert)
    self.assertTrue(args.publish_crl)

    args = self.parser.parse_args(['--publish-crl'])
    self.assertTrue(args.publish_ca_cert)
    self.assertTrue(args.publish_crl)

  def testAddEmailSan(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(['--email-san', 'test'])
    self.assertEqual(args.email_san, ['test'])

  def testAddMultipleEmailSans(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(
        ['--email-san', 'test1@tld, test2@bar.net, test3@baz.bar.org'])
    self.assertEqual(args.email_san,
                     ['test1@tld', 'test2@bar.net', 'test3@baz.bar.org'])

  def testEmailValidation(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(['--email-san', 'test'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      flags.ValidateEmailSanFlag(args.email_san[0])

    args = self.parser.parse_args(['--email-san', 'test@test'])
    flags.ValidateEmailSanFlag(args.email_san[0])

    args = self.parser.parse_args(['--email-san', 'test@test@'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      flags.ValidateEmailSanFlag(args.email_san[0])

  def testAddDnsSan(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(['--dns-san', 'test'])
    self.assertEqual(args.dns_san, ['test'])

  def testAddMultipleDnsSans(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(
        ['--dns-san', 'tld, test2.net, test3.tld.org'])
    self.assertEqual(args.dns_san, ['tld', 'test2.net', 'test3.tld.org'])

  def testDnsValidation(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(['--dns-san', 'test.'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      flags.ValidateDnsSanFlag(args.dns_san[0])

    args = self.parser.parse_args(['--dns-san', 'te-st.com'])
    flags.ValidateDnsSanFlag(args.dns_san[0])

    args = self.parser.parse_args(['--dns-san', 'com'])
    flags.ValidateDnsSanFlag(args.dns_san[0])

  def testAddIpSan(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(['--ip-san', 'test'])
    self.assertEqual(args.ip_san, ['test'])

  def testAddMultipleIpSans(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(
        ['--ip-san', '1.2.3.4,127.0.0.1,2620:0:1008:10:9dda:7dd8:2ec6:273d'])
    self.assertEqual(
        args.ip_san,
        ['1.2.3.4', '127.0.0.1', '2620:0:1008:10:9dda:7dd8:2ec6:273d'])

  def testIpValidation(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(['--ip-san', '1.1.1.1'])
    flags.ValidateIpSanFlag(args.ip_san[0])

    args = self.parser.parse_args(['--ip-san', '1::1:1'])
    flags.ValidateIpSanFlag(args.ip_san[0])

    args = self.parser.parse_args(['--ip-san', '2323232'])
    with self.assertRaises(exceptions.InvalidArgumentException):
      flags.ValidateIpSanFlag(args.ip_san[0])

  def testAddUriSan(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(['--uri-san', 'test'])
    self.assertEqual(args.uri_san, ['test'])

  def testAddMultipleUriSans(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(
        ['--uri-san', 'https://test1.com/foo?bar=baz,spiffe://idns/1/2/3/4'])
    self.assertEqual(args.uri_san,
                     ['https://test1.com/foo?bar=baz', 'spiffe://idns/1/2/3/4'])

  def testSubjectFlagInvalidKey(self):
    flags.AddSubjectFlags(self.parser)
    with self.AssertRaisesExceptionMatches(
        Exception,
        'Invalid value for [--subject]: Unrecognized subject attribute.'):
      args = self.parser.parse_args([
          '--subject',
          'C=US, CN=something, ST=Washington, LU=Kirkland, O=Google LLC, OU=Cloud, postalCode=98033, streetAddress=6th Ave'
      ])
      flags.ParseSubject(args)

  def testSubjectParseAllFields(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args([
        '--subject',
        'C=US, ST=Washington, L=Kirkland, O=Google LLC, CN=google.com, OU=Cloud, postalCode=98033, streetAddress=6th Ave'
    ])
    common_name, subject = flags.ParseSubject(args)
    self.assertEqual(common_name, 'google.com')
    self.assertEqual(subject.countryCode, 'US')
    self.assertEqual(subject.province, 'Washington')
    self.assertEqual(subject.organization, 'Google LLC')
    self.assertEqual(subject.locality, 'Kirkland')
    self.assertEqual(subject.organizationalUnit, 'Cloud')
    self.assertEqual(subject.postalCode, '98033')
    self.assertEqual(subject.streetAddress, '6th Ave')

  def testSubjectKeyValStrip(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(
        ['--subject', 'CN=google.com,C=US,ST=Washington'])
    common_name, subject = flags.ParseSubject(args)
    self.assertEqual(common_name, 'google.com')
    self.assertEqual(subject.countryCode, 'US')
    self.assertEqual(subject.province, 'Washington')

    args = self.parser.parse_args(
        ['--subject', 'CN=google.com , C=US,ST=Washington'])
    common_name, subject = flags.ParseSubject(args)
    self.assertEqual(common_name, 'google.com')
    self.assertEqual(subject.countryCode, 'US')
    self.assertEqual(subject.province, 'Washington')

    args = self.parser.parse_args(
        ['--subject', 'CN=google.com, C=US, ST=Washington'])
    common_name, subject = flags.ParseSubject(args)
    self.assertEqual(common_name, 'google.com')
    self.assertEqual(subject.countryCode, 'US')
    self.assertEqual(subject.province, 'Washington')

  def testSubjectParsePartialFields(self):
    flags.AddSubjectFlags(self.parser)
    args = self.parser.parse_args(
        ['--subject', 'O=Google LLC,CN=google.com,OU=Cloud'])
    common_name, subject = flags.ParseSubject(args)
    self.assertEqual(common_name, 'google.com')
    self.assertEqual(subject.organization, 'Google LLC')
    self.assertEqual(subject.organizationalUnit, 'Cloud')

  def testSubjectFlagNoOrganizationFailure(self):
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'organization'):
      flags.ValidateSubjectConfig(
          self.messages.SubjectConfig(
              commonName='google.com',
              subject=self.messages.Subject(),
              subjectAltName=self.messages.SubjectAltNames()),
          is_ca=True)

  def testSubjectNoNameFailure(self):
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'subject'):
      flags.ValidateSubjectConfig(
          self.messages.SubjectConfig(
              subject=self.messages.Subject(
                  countryCode='US', organization='Google LLC'),
              subjectAltName=self.messages.SubjectAltNames()),
          is_ca=False)

  def testSubjectFlagNoCnFailure(self):
    with self.AssertRaisesExceptionMatches(exceptions.InvalidArgumentException,
                                           'common name'):
      flags.ValidateSubjectConfig(
          self.messages.SubjectConfig(
              subject=self.messages.Subject(
                  countryCode='US', organization='Google LLC'),
              subjectAltName=self.messages.SubjectAltNames()),
          is_ca=False)

  def testRevocationReasonFlag(self):
    flags.AddRevocationReasonFlag(self.parser)
    args = self.parser.parse_args(['--reason', 'key-compromise'])
    self.assertEqual(args.reason, 'key-compromise')

  def testParseRevocationChoice(self):
    self.assertEqual(
        flags.ParseRevocationChoiceToEnum('key-compromise'),
        privateca_base.GetMessagesModule().RevokeCertificateRequest
        .ReasonValueValuesEnum.KEY_COMPROMISE)

  def testRevocationReasonFlagInvalid(self):
    flags.AddRevocationReasonFlag(self.parser)
    with self.assertRaises(cli_test_base.MockArgumentError):
      self.parser.parse_args(['--reason', 'invalid'])

  def testAddValidityFlagPassthroughValue(self):
    flags.AddValidityFlag(self.parser, 'CA', 'P10Y')
    args = self.parser.parse_args(['--validity', 'P1Y'])
    self.assertEqual(args.validity, 'P1Y')

  def testAddValidityFlagDefaultValue(self):
    flags.AddValidityFlag(self.parser, 'CA', 'P10Y')
    args = self.parser.parse_args([])
    self.assertEqual(args.validity, 'P10Y')

  def testAddReusableConfigFlagsKeyUsages(self):
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args(['--key-usages', 'cert_sign,crl_sign'])
    self.assertEqual(args.key_usages, ['cert_sign', 'crl_sign'])

  def testAddReusableConfigFlagsKeyUsagesWithSpaces(self):
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args(['--key-usages', 'cert_sign, crl_sign'])
    self.assertEqual(args.key_usages, ['cert_sign', 'crl_sign'])

  def testAddReusableConfigFlagsInvalidKeyUsages(self):
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    with self.AssertRaisesExceptionMatches(Exception, 'argument --key-usages'):
      self.parser.parse_args(['--key-usages', 'not_crl_sign'])

  def testAddReusableConfigFlagsExtendedKeyUsages(self):
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args(
        ['--extended-key-usages', 'server_auth,client_auth'])
    self.assertEqual(args.extended_key_usages, ['server_auth', 'client_auth'])

  def testAddReusableConfigFlagsExtendedKeyUsagesWithSpaces(self):
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args(
        ['--extended-key-usages', 'server_auth, client_auth'])
    self.assertEqual(args.extended_key_usages, ['server_auth', 'client_auth'])

  def testAddReusableConfigFlagsInvalidExtendedKeyUsages(self):
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    with self.AssertRaisesExceptionMatches(Exception,
                                           'argument --extended-key-usages'):
      self.parser.parse_args(['--extended-key-usages', 'not_server_auth'])

  def testAddReusableConfigFlagsMaxChainLength(self):
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args(['--max-chain-length', '1'])
    self.assertEqual(args.max_chain_length, '1')

  def testParseReusableConfigFullyQualifiedResourceArg(self):
    reusable_config_id = 'projects/foo/locations/us-west1/reusableConfigs/rc1'
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args(['--reusable-config', reusable_config_id])

    # We expect the parser to ignore the 'us-central1' hint here since the
    # resource name explicitly specifies 'us-west1'.
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-central1', is_ca=True)
    self.assertEqual(reusable_config_wrapper.reusableConfig, reusable_config_id)
    self.assertIsNone(reusable_config_wrapper.reusableConfigValues)

  def testParseReusableConfigShortResourceArg(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args(['--reusable-config', 'rc1'])
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-central1', is_ca=True)
    self.assertEqual(
        reusable_config_wrapper.reusableConfig,
        'projects/privateca-data/locations/us-central1/reusableConfigs/rc1')
    self.assertIsNone(reusable_config_wrapper.reusableConfigValues)

  def testParseReusableConfigMaxChainLength(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args(['--max-chain-length', '1'])
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-west1', is_ca=True)
    self.assertTrue(
        reusable_config_wrapper.reusableConfigValues.caOptions.isCa)
    self.assertEqual(
        reusable_config_wrapper.reusableConfigValues.caOptions
        .maxIssuerPathLength, 1)
    self.assertTrue(
        reusable_config_wrapper.reusableConfigValues.keyUsage.baseKeyUsage
        .certSign)
    self.assertTrue(
        reusable_config_wrapper.reusableConfigValues.keyUsage.baseKeyUsage
        .crlSign)

  def testParseReusableConfigIsCa(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args([])
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-west1', is_ca=True)
    self.assertTrue(
        reusable_config_wrapper.reusableConfigValues.caOptions.isCa)
    self.assertTrue(
        reusable_config_wrapper.reusableConfigValues.keyUsage.baseKeyUsage
        .certSign)
    self.assertTrue(
        reusable_config_wrapper.reusableConfigValues.keyUsage.baseKeyUsage
        .crlSign)

  def testParseReusableConfigMaxChainLengthIgnored(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=False)
    args = self.parser.parse_args(
        ['--no-is-ca-cert', '--max-chain-length', '1'])
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-west1', is_ca=False)
    self.assertEqual(
        reusable_config_wrapper.reusableConfigValues.caOptions.isCa, False)
    self.assertIsNone(
        reusable_config_wrapper.reusableConfigValues.caOptions
        .maxIssuerPathLength)

  def testParseReusableConfigResourceAndInlineValues(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args([
        '--reusable-config', 'projects/foo/locations/us/reusableConfigs/rc1',
        '--key-usages', 'cert_sign,crl_sign'
    ])
    with self.AssertRaisesExceptionMatches(Exception, 'Invalid value'):
      flags.ParseReusableConfig(args, 'us-west1', is_ca=True)

  def testParseReusableConfigNoResourceAndNoInlineValues(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args([])
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-west', is_ca=True)

    self.assertIsNone(reusable_config_wrapper.reusableConfig)
    self.assertTrue(
        reusable_config_wrapper.reusableConfigValues.caOptions.isCa)

  def testParseReusableConfigNoResourceAndNoInlineCertificateValues(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=False)
    args = self.parser.parse_args([])
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-west', is_ca=False)

    self.assertIsNone(reusable_config_wrapper.reusableConfig)
    self.assertEqual(
        reusable_config_wrapper.reusableConfigValues.caOptions.isCa, False)

  def testParseReusableConfigInlineValues(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this CA.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=True)
    args = self.parser.parse_args([
        '--key-usages', 'cert_sign,crl_sign', '--extended-key-usages',
        'server_auth,client_auth', '--max-chain-length', '2'
    ])
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-west1', is_ca=True)
    self.assertIsNone(reusable_config_wrapper.reusableConfig)
    values = reusable_config_wrapper.reusableConfigValues
    self.assertTrue(values.keyUsage.baseKeyUsage.certSign)
    self.assertTrue(values.keyUsage.baseKeyUsage.crlSign)
    self.assertIsNone(values.keyUsage.baseKeyUsage.digitalSignature)
    self.assertIsNone(values.keyUsage.baseKeyUsage.contentCommitment)
    self.assertIsNone(values.keyUsage.baseKeyUsage.keyEncipherment)
    self.assertIsNone(values.keyUsage.baseKeyUsage.dataEncipherment)
    self.assertIsNone(values.keyUsage.baseKeyUsage.keyAgreement)
    self.assertIsNone(values.keyUsage.baseKeyUsage.encipherOnly)
    self.assertIsNone(values.keyUsage.baseKeyUsage.decipherOnly)

    self.assertTrue(values.keyUsage.extendedKeyUsage.serverAuth)
    self.assertTrue(values.keyUsage.extendedKeyUsage.clientAuth)
    self.assertIsNone(values.keyUsage.extendedKeyUsage.codeSigning)
    self.assertIsNone(values.keyUsage.extendedKeyUsage.emailProtection)
    self.assertIsNone(values.keyUsage.extendedKeyUsage.timeStamping)
    self.assertIsNone(values.keyUsage.extendedKeyUsage.ocspSigning)

    self.assertEqual(values.caOptions.maxIssuerPathLength, 2)
    self.assertTrue(values.caOptions.isCa)

  def testParseReusableConfigInlineCertificateValues(self):
    concept_parsers.ConceptParser.ForResource(
        '--reusable-config',
        resource_args.CreateReusableConfigResourceSpec(),
        'Reusable config for this certificate.',
        prefixes=True).AddToParser(self.parser)
    flags.AddInlineReusableConfigFlags(self.parser, is_ca=False)
    args = self.parser.parse_args([
        '--key-usages', 'cert_sign,crl_sign', '--extended-key-usages',
        'server_auth,client_auth', '--no-is-ca-cert'
    ])
    reusable_config_wrapper = flags.ParseReusableConfig(
        args, 'us-west1', is_ca=False)
    self.assertEqual(
        reusable_config_wrapper.reusableConfigValues.caOptions.isCa, False)

  def testParseValidityFlag(self):
    flags.AddValidityFlag(self.parser, 'certificate')
    args = self.parser.parse_args(['--validity', 'P30D'])
    duration = flags.ParseValidityFlag(args)
    self.assertEqual(duration, '2592000s')

  def testParseValidityFlagDefaultValue(self):
    flags.AddValidityFlag(self.parser, 'certificate')
    args = self.parser.parse_args([])
    duration = flags.ParseValidityFlag(args)
    self.assertEqual(duration, '315569261s')

  def testParseIssuingOptionsDefaultsAllToTrueForEnterpriseTier(self):
    flags.AddPublishCaCertFlag(self.parser)
    flags.AddPublishCrlFlag(self.parser)
    flags.AddTierFlag(self.parser)
    args = self.parser.parse_args(['--tier=enterprise'])
    issuing_options = flags.ParseIssuingOptions(args)
    self.assertTrue(issuing_options.includeCaCertUrl)
    self.assertTrue(issuing_options.includeCrlAccessUrl)

  def testParseIssuingOptionsDefaultsPublishCrlToFalseForDevOpsTier(self):
    flags.AddPublishCaCertFlag(self.parser)
    flags.AddPublishCrlFlag(self.parser)
    flags.AddTierFlag(self.parser)
    args = self.parser.parse_args(['--tier=devops'])
    issuing_options = flags.ParseIssuingOptions(args)
    self.assertTrue(issuing_options.includeCaCertUrl)
    self.assertFalse(issuing_options.includeCrlAccessUrl)

  def testParseIssuingOptionsAcceptsExplicitPublishCrlForEnterpriseTier(self):
    flags.AddPublishCaCertFlag(self.parser)
    flags.AddPublishCrlFlag(self.parser)
    flags.AddTierFlag(self.parser)
    args = self.parser.parse_args(['--tier=enterprise', '--publish-crl'])
    issuing_options = flags.ParseIssuingOptions(args)
    self.assertTrue(issuing_options.includeCaCertUrl)
    self.assertTrue(issuing_options.includeCrlAccessUrl)

  def testParseIssuingOptionsRejectsExplicitPublishCrlForDevOpsTier(self):
    flags.AddPublishCaCertFlag(self.parser)
    flags.AddPublishCrlFlag(self.parser)
    flags.AddTierFlag(self.parser)
    args = self.parser.parse_args(['--tier=devops', '--publish-crl'])
    with self.assertRaisesRegex(exceptions.InvalidArgumentException,
                                '--publish-crl.*DevOps.*'):
      flags.ParseIssuingOptions(args)

  def testParseIssuancePolicy(self):
    flags.AddCertificateAuthorityIssuancePolicyFlag(self.parser)
    policy_issuance_path = self.Resource('tests', 'unit', 'surface',
                                         'privateca', 'test_data',
                                         'issuance_policy_example_small.yaml')
    args = self.parser.parse_args(['--issuance-policy', policy_issuance_path])
    issuance_policy = flags.ParseIssuancePolicy(args)
    self.assertEqual(issuance_policy.maximumLifetime, '825d')

  def testParseIssuancePolicyMissingIsNone(self):
    flags.AddCertificateAuthorityIssuancePolicyFlag(self.parser)
    args = self.parser.parse_args([])
    issuance_policy = flags.ParseIssuancePolicy(args)
    self.assertIsNone(issuance_policy)

  def testParseKeySpecWithKeyAlgorithm(self):
    concept_parsers.ConceptParser.ForResource(
        '--kms-key-version',
        resource_args.CreateKmsKeyVersionResourceSpec(),
        'KMS key version.'
    ).AddToParser(self.parser)
    flags.AddKeyAlgorithmFlag(self.parser)
    args = self.parser.parse_args(['--key-algorithm=ec-p384-sha384'])
    key_spec = flags.ParseKeySpec(args)
    self.assertIsNone(key_spec.cloudKmsKeyVersion)
    self.assertEqual(
        key_spec.algorithm,
        self.messages.KeyVersionSpec.AlgorithmValueValuesEnum.EC_P384_SHA384)

  def testParseKeySpecWithKeyVersion(self):
    concept_parsers.ConceptParser.ForResource(
        '--kms-key-version',
        resource_args.CreateKmsKeyVersionResourceSpec(),
        'KMS key version.'
    ).AddToParser(self.parser)
    flags.AddKeyAlgorithmFlag(self.parser)
    key_version_resource = 'projects/foo/locations/bar/keyRings/kr1/cryptoKeys/k1/cryptoKeyVersions/1'
    args = self.parser.parse_args(['--kms-key-version', key_version_resource])
    key_spec = flags.ParseKeySpec(args)
    self.assertIsNone(key_spec.algorithm)
    self.assertEqual(key_spec.cloudKmsKeyVersion, key_version_resource)

  def testParseKeySpecUsesDefaultKeyAlgorithmIfNotSpecified(self):
    concept_parsers.ConceptParser.ForResource(
        '--kms-key-version',
        resource_args.CreateKmsKeyVersionResourceSpec(),
        'KMS key version.'
    ).AddToParser(self.parser)
    flags.AddKeyAlgorithmFlag(self.parser, default='rsa-pkcs1-3072-sha256')
    args = self.parser.parse_args([])
    key_spec = flags.ParseKeySpec(args)
    self.assertIsNone(key_spec.cloudKmsKeyVersion)
    self.assertEqual(key_spec.algorithm,
                     self.messages.KeyVersionSpec
                     .AlgorithmValueValuesEnum.RSA_PKCS1_3072_SHA256)


if __name__ == '__main__':
  test_case.main()
