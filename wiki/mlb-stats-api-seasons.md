# MLB Stats API — Seasons

Season date windows: regular season, preseason, postseason, All-Star.

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /seasons/all` or `GET /seasons` | All seasons (filter by sport/division) |
| `GET /seasons/{seasonId}` | Single season details |

Parameters: `sportId` (optional), `divisionId` (optional), `fields` (optional).

(source: mlb-stats-api-seasons.md)

## Response Fields

- `seasonId` — year
- `regularSeasonStartDate` / `regularSeasonEndDate`
- `preSeasonStartDate` / `preSeasonEndDate`
- `postSeasonStartDate` / `postSeasonEndDate`
- `allStarDate`

Example: the 2025 MLB season runs March 27 – September 28 for regular play,
with preseason starting February 21 and postseason beginning October 1.
(source: mlb-stats-api-seasons.md)

See also: [[mlb-stats-api]]
