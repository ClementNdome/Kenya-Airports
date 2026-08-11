# ADR: Property Query Tool — Public Read-Only (Phase 1), User-Scoped Later

Created: 2026-08-11
Status: **Accepted — Phase 1 (public read-only)**

---

## Context

A spatial query tool is needed to search saved properties by aerodrome proximity and
attributes (radius, height range, compliance status, bounding box).

Django auth exists in the codebase but is not yet hardened or widely adopted by users;
requiring login would make the tool unusable for most visitors today.

## Decision

- The query tool ships **public read-only**: any visitor may query **all properties**
  in the system, subject only to KCAA/ICAO compliance rules and the tool's own rate limits.
- Queries are read-only (list/filter results). No write access is granted.
- **User-specific scoping is explicitly deferred** to a future phase.

## Future Phase (pending)

- Restrict `PropertyQueryAPI` to `request.user.properties` when authentication is mature
  (login required, verified emails, ownership enforcement).
- Add per-user saved queries / reports.
- Add `is_public` flag on `Property` for owners to opt out of public visibility.

## Data notes

- The legacy `runways-declared_distances` table stores `runway_pair` **whitespace-padded**
  (e.g. `' 08/26      '`). Joins to `aerodrome-runways` MUST use `TRIM(runway_pair)`.
- Verified 2026-08-11: 23/23 declared-distance rows join to runways on
  `(icao_code, TRIM(runway_pair))`, and all runway rows have a matching `Aerodrome` row.

## Related

- `docs/ADRs/ADR-buffer_OLS_NA_OA.md` (OLS engine status)
- `obstacle_compliance/views.py` — `PropertyQueryAPI`
