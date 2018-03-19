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
"""Update rotation schedule and/or labels on a key."""

from apitools.base.py import exceptions as apitools_exceptions
from googlecloudsdk.api_lib.cloudkms import base as cloudkms_base
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.command_lib.kms import flags
from googlecloudsdk.command_lib.util.args import labels_util


@base.ReleaseTracks(base.ReleaseTrack.GA, base.ReleaseTrack.BETA)
class Update(base.UpdateCommand):
  r"""Update a key.

  1. Update the rotation schedule for the given key.

  Updates the rotation schedule for the given key. The schedule
  automatically creates a new primary version for the key
  according to the `--next-rotation-time` and `--rotation-period` flags.

  The flag `--next-rotation-time` must be in ISO or RFC3339 format,
  and `--rotation-period` must be in the form INTEGER[UNIT], where units
  can be one of seconds (s), minutes (m), hours (h) or days (d).

  Key rotations performed manually via `update-primary-version` and the
  version `create` do not affect the stored `--next-rotation-time`.

  2. Remove the rotation schedule for the given key with
  --remove-rotation-schedule.

  3. Update/Remove the labels for the given key with --update-labels and/or
  --remove-labels.

  4. Update the primary version for the given key with --primary-version.

  ## EXAMPLES

  The following command sets a 30 day rotation period for the key
  named `frodo` within the keyring `fellowship` and location `global`
  starting at the specified time:

    $ {command} frodo \
        --location global \
        --keyring fellowship \
        --rotation-period 30d \
        --next-rotation-time 2017-10-12T12:34:56.1234Z

  The following command removes the rotation schedule for the key
  named `frodo` within the keyring `fellowship` and location `global`:

    $ {command} frodo \
        --location global \
        --keyring fellowship \
        --remove-rotation-schedule

  The following command updates the labels value for the key
  named `frodo` within the keyring `fellowship` and location `global`. If the
  label key does not exist at the time, it will be added:

    $ {command} frodo \
        --location global \
        --keyring fellowship \
        --update-labels k1=v1

  The following command removes labels k1 and k2 from the key
  named `frodo` within the keyring `fellowship` and location `global`:

    $ {command} frodo \
        --location global \
        --keyring fellowship \
        --remove-labels k1,k2

  The following command updates the primary version for the key
  named `frodo` within the keyring `fellowship` and location `global`:

    $ {command} frodo \
        --location global \
        --keyring fellowship \
        --primary-version 1
  """

  @staticmethod
  def Args(parser):
    flags.AddCryptoKeyArgument(parser, 'to update')
    flags.AddRotationPeriodFlag(parser)
    flags.AddNextRotationTimeFlag(parser)
    flags.AddRemoveRotationScheduleFlag(parser)
    flags.AddCryptoKeyPrimaryVersionFlag(parser, 'to make primary')
    labels_util.AddUpdateLabelsFlags(parser)

  def ProcessFlags(self, args):
    fields_to_update = []

    labels_diff = labels_util.Diff.FromUpdateArgs(args)
    if labels_diff.MayHaveUpdates():
      fields_to_update.append('labels')
    if args.remove_rotation_schedule:
      if args.rotation_period or args.next_rotation_time:
        raise exceptions.ToolException(
            'You cannot set and remove rotation schedule at the same time.')
      fields_to_update.append('rotationPeriod')
      fields_to_update.append('nextRotationTime')
    if args.rotation_period:
      fields_to_update.append('rotationPeriod')
    if args.next_rotation_time:
      fields_to_update.append('nextRotationTime')

    # Raise an exception when no update field is specified.
    if not args.primary_version and not fields_to_update:
      raise exceptions.ToolException(
          'At least one of --primary-version or --update-labels or --remove-'
          'labels or --clear-labels or --rotation-period or --next-rotation-'
          'time or --remove-rotation-schedule must be specified.')

    return fields_to_update

  def UpdatePrimaryVersion(self, args):
    # pylint: disable=line-too-long
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    crypto_key_ref = flags.ParseCryptoKeyName(args)
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysUpdatePrimaryVersionRequest(
        name=crypto_key_ref.RelativeName(),
        updateCryptoKeyPrimaryVersionRequest=(
            messages.UpdateCryptoKeyPrimaryVersionRequest(
                cryptoKeyVersionId=args.primary_version)))

    try:
      response = client.projects_locations_keyRings_cryptoKeys.UpdatePrimaryVersion(req)
    except apitools_exceptions.HttpError:
      return None

    return response

  def UpdateOthers(self, args, crypto_key, fields_to_update):
    # pylint: disable=line-too-long
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    crypto_key_ref = flags.ParseCryptoKeyName(args)
    req = messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysPatchRequest(
        name=crypto_key_ref.RelativeName(),
        cryptoKey=messages.CryptoKey(
            labels=labels_util.Diff.FromUpdateArgs(args).Apply(
                messages.CryptoKey.LabelsValue, crypto_key.labels).GetOrNone()))
    req.updateMask = ','.join(fields_to_update)
    flags.SetNextRotationTime(args, req.cryptoKey)
    flags.SetRotationPeriod(args, req.cryptoKey)

    try:
      response = client.projects_locations_keyRings_cryptoKeys.Patch(req)
    except apitools_exceptions.HttpError:
      return None

    return response

  def HandleErrors(self, args,
                   set_primary_version_succeeds,
                   other_updates_succeed,
                   fields_to_update):
    err = 'An Error occurred:'
    if not set_primary_version_succeeds:
      err += ' Failed to update field \'primaryVersion\'.'
    elif args.primary_version:
      err += ' Field \'primaryVersion\' was updated.'
    if not other_updates_succeed:
      err += ' Failed to update field(s) \'{}\'.'.format(
          '\', \''.join(fields_to_update))
    elif fields_to_update:
      err += ' Field(s) \'{}\' were updated.'.format(
          '\', \''.join(fields_to_update))
    raise exceptions.ToolException(err)

  def Run(self, args):
    # Check the flags and raise an exception if any check fails.
    fields_to_update = self.ProcessFlags(args)

    # Try to get the cryptoKey and raise an exception if the key doesn't exist.
    client = cloudkms_base.GetClientInstance()
    messages = cloudkms_base.GetMessagesModule()
    crypto_key_ref = flags.ParseCryptoKeyName(args)
    crypto_key = client.projects_locations_keyRings_cryptoKeys.Get(
        messages.CloudkmsProjectsLocationsKeyRingsCryptoKeysGetRequest(
            name=crypto_key_ref.RelativeName()))

    # Try to update the key's primary version.
    set_primary_version_succeeds = True
    if args.primary_version:
      response = self.UpdatePrimaryVersion(args)
      if response:
        crypto_key = response  # If call succeeds, update the crypto_key.
      else:
        set_primary_version_succeeds = False

    # Try other updates.
    other_updates_succeed = True
    if fields_to_update:
      response = self.UpdateOthers(args, crypto_key, fields_to_update)
      if response:
        crypto_key = response  # If call succeeds, update the crypto_key.
      else:
        other_updates_succeed = False

    if (not set_primary_version_succeeds) or (not other_updates_succeed):
      self.HandleErrors(args,
                        set_primary_version_succeeds,
                        other_updates_succeed,
                        fields_to_update)
    else:
      return crypto_key
