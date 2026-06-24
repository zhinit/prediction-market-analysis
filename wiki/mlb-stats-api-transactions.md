# MLB Stats API — Transactions

Player transactions: trades, signings, DFA, IL placements, call-ups, options.

## Endpoint

`GET /transactions` (verified)

## Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `startDate` | yes | YYYY-MM-DD |
| `endDate` | yes | YYYY-MM-DD |
| `teamId` | no | Filter to one team |
| `playerId` | no | Filter to one player |
| `sportId` | no | 1 = MLB |
| `limit` | no | Max records |
| `offset` | no | Pagination |
| `fields` | no | Selective fields |

## Examples

```bash
# All transactions in a date range
curl "https://statsapi.mlb.com/api/v1/transactions?startDate=2025-03-01&endDate=2025-03-10"

# Team-specific
curl "https://statsapi.mlb.com/api/v1/transactions?startDate=2025-02-15&endDate=2025-03-31&teamId=119"

# Player-specific
curl "https://statsapi.mlb.com/api/v1/transactions?startDate=2024-01-01&endDate=2024-12-31&playerId=660271"
```

## Response Fields

| Field | Description |
|-------|-------------|
| `id` | Transaction ID |
| `person` | `{ id, fullName, link }` |
| `toTeam` | Destination team |
| `fromTeam` | Origin team |
| `date` | Transaction date |
| `effectiveDate` | When it takes effect |
| `resolutionDate` | When resolved (e.g. IL return) |
| `typeCode` | Short code |
| `typeDesc` | Human-readable description |
| `description` | Full transaction description |

(source: mlb-stats-api-transactions.md)

## Transaction Type Codes

| Code | Description |
|------|-------------|
| SC | Signed as Free Agent |
| TE | Traded |
| DES | Designated for Assignment |
| RE | Released |
| PUR | Purchased from Minors |
| WV | Placed on Waivers |
| RET | Retired |
| TR | Transferred |
| SU | Called Up |
| OA | Optioned to Minors |
| OUT | Outrighted |
| IL | Placed on Injured List |
| ACT | Activated from IL |
| NRI | Non-Roster Invitee |
| PCT | Paternity List |
| RPC | Reinstated from Paternity |
| BRV | Bereavement List |
| RBL | Reinstated from Bereavement |
| EXC | Exhibition Contract |
| MIN | Minor League Contract |

(source: mlb-stats-api-transactions.md)

See also: [[mlb-stats-api]]
