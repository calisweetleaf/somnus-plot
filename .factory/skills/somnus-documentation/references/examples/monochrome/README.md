# Siltline

**FIELD RECORD SYSTEM** · `PROJECT GUIDE / 01`

> A local-first record book for repeatable coastal transects.

**Document status:** Illustrative design fixture. Siltline is fictional; its commands and behavior exist only to demonstrate this documentation style.

Siltline keeps field observations attached to the site and transect where they were made. It validates records before export and retains corrections as dated events, so a later reader can distinguish an observation from its amendment.

This guide introduces the record model, walks through one collection route, and explains where validation, amendments, and export sit. It does not describe a deployed product.

## Reading this guide

| If you need to… | Start here |
| --- | --- |
| Understand what belongs in a Siltline record | [The record](#the-record) |
| Create and validate an observation | [A collection route](#a-collection-route) |
| Correct a value without erasing history | [Amendments](#amendments) |
| Know what an export contains | [Export boundary](#export-boundary) |
| See the fixture assumptions behind this example | [`fixture-source.md`](fixture-source.md) |

## The record

Siltline treats a field observation as a statement with a location, a time, a measurement, and a person or instrument responsible for making it. A site groups transects; a transect orders stations; each station may hold multiple observations made at different times.

```text
site
└── transect
    └── station
        └── observation
            └── amendment events
```

The hierarchy answers a practical question before a measurement is interpreted: *where does this record belong?* A depth value without its station and observation time is incomplete. Siltline reports that gap during validation rather than supplying a guess.

An observation is stored as a plain-text record:

```toml
site = "bay-07"
transect = "north"
station = "01"
observed_at = "2026-05-18T08:40:00Z"
distance_m = 12.4
water_depth_m = 1.2
observer = "field-team-a"
note = "Seagrass edge begins west of station marker."
```

The timestamp is UTC. Distances and depth use metres. Notes preserve the observer's wording; they are not parsed as measurements.

## A collection route

Start by creating the local record space. The command creates a site manifest and an empty observation directory; it does not contact a service.

```console
siltline init bay-07
```

Add an observation to a named transect and station:

```console
siltline observe bay-07 \
  --transect north \
  --station 01 \
  --observed-at 2026-05-18T08:40:00Z \
  --distance-m 12.4 \
  --water-depth-m 1.2 \
  --observer field-team-a \
  --note "Seagrass edge begins west of station marker."
```

The command writes one record and returns its local path. Review the record before validating the site:

```console
siltline validate bay-07
```

Validation checks required fields, timestamp form, unit names, and whether the referenced transect and station exist in the site manifest. A failed check names the record and field. It does not repair values or infer missing locations.

## Amendments

Field records sometimes need correction. Siltline does not overwrite the original measurement. An amendment stores the record identifier, the changed field, the prior value, the replacement value, the reason, and the amendment time.

```console
siltline amend bay-07 obs-014 \
  --field water_depth_m \
  --value 1.3 \
  --reason "Re-read against the calibrated staff."
```

The original observation remains available in the record history. A current view applies amendments in order; an audit view shows the initial value and each later change. Use the audit view when provenance matters:

```console
siltline history bay-07 obs-014
```

An amendment records what changed and why. It does not establish that the replacement value is correct; that judgment remains with the field team.

## Export boundary

Exports contain observations and their applied amendments. They omit machine-specific paths. The export command requires validation to pass first:

```console
siltline export bay-07 --format csv --out bay-07.csv
```

The CSV includes the current value and an observation identifier. It does not include the full event history. Keep the site directory when later review needs the original and amendment sequence.

| Output | Includes | Use it for |
| --- | --- | --- |
| CSV export | Current validated observations | Analysis in a tabular tool |
| Site directory | Manifest, records, and amendment events | Review, correction, and audit |

## Boundaries and care

Siltline is designed for a team to keep its records locally. It does not synchronize sites, identify observers, or decide whether a measurement is scientifically sound. Store only the observer identifier your team needs, and keep any identity key under the team's own control.

The site directory is the source record. Copy it using the team's approved backup process before moving or renaming it. Do not edit observation files while a Siltline command is changing the same site.

## Further reading

The fixture's assumed behavior and terminology are recorded in [`fixture-source.md`](fixture-source.md). For a real project, replace this guide's fictional contract with verified behavior, repository paths, tested commands, and the project's own identity. Preserve this page's reading sequence only where it helps that project's readers.
