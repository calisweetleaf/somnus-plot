# Siltline Fixture Source

This file defines the fictional project facts used by [`README.md`](README.md). It exists only to keep the exemplar internally consistent. Siltline is not a real or shipped application.

## Assumed model

- A site has a manifest and contains transects.
- A transect contains named stations.
- An observation belongs to one site, transect, and station and includes an observation timestamp, distance in metres, water depth in metres, and observer identifier.
- Notes are plain text and are not interpreted as measurements.
- Observations are stored as text files in the local site directory.
- Amendments are append-only events. They identify the observation, field, prior value, replacement value, reason, and amendment time.
- A current view applies amendments in order. An audit view retains the original and amendment sequence.
- Validation checks required fields, timestamp form, unit names, and referenced transect and station. It reports issues and never guesses or repairs missing values.
- CSV export requires successful validation and includes current values and observation identifiers. It omits amendment history and machine-specific paths.
- No network service, synchronization, identity resolution, or scientific judgment is part of the fixture.

## Assumed command surface

The example uses `siltline init`, `observe`, `validate`, `amend`, `history`, and `export`. These command names and flags are invented for this fixture, not recommendations for a real CLI.

## Evaluation boundary

This non-Somnus fixture tests whether the current composition can use GitHub-native structure without importing a palette or custom markup. It does not establish a real repository's unique identity or verify product behavior. For those checks, compare a future treatment with the target repository's existing reader-facing docs and confirm every behavior against its source.
