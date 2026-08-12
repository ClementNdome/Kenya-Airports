# Management Commands

All commands live in `obstacle_compliance/management/commands/`. Run with `python manage.py <name> [args]`.

## Data Loading

| Command | Purpose | Options |
|---|---|---|
| `load_aerodromes` | Load KCAA aerodrome GeoJSON (`newdata/aerodromes-ke.geojson`); DMS → decimal conversion | — |
| `load_buffers` | Load precomputed buffers (`newdata/final_buffered/{3,5,10,15}km_buffer-wgs84.geojson`) via LayerMapping | — |
| `merge_airports_data` | Merge `airports_strips.Airports` into `Aerodrome` (iata, runway length, nearest city, airlines) | — |

## Buffer Generation & Maintenance

| Command | Purpose | Options |
|---|---|---|
| `add_threshold_buffers` | Backfill runway-threshold (capsule) buffers 3/5/10 km | `--icao`, `--radii` |
| `regenerate_buffers` | Regenerate ALL buffers in local UTM (EPSG 32636/32637/32736/32737) with corrected `area_km2` | `--radii 3 5 10`, `--type arp\|runway\|both`, `--icao` |

## Operations

| Command | Purpose | Options |
|---|---|---|
| `process_bulk_upload` | Process pending `BulkUploadJob`s | `--job <id>` |
| `send_notifications` | Notification utility (prints unread counts per user) | — |
| `verify_data` | Data sanity audit: counts, buffer completeness per radius, spatial sanity (point-in-buffer), missing geometry | — |

## Diagnostics

| Command | Purpose |
|---|---|
| `test_compliance` | Sample compliance checks — JKIA / Wilson / Mombasa / Kisumu / custom point |
| `test_elevation` | Elevation-parsing audit table (5 regex patterns) |
| `test_dem` | DEM sampling diagnostics |
| `test_dem_detailed` | Detailed DEM sampling diagnostics |

## Example

```sh
# Full local data bootstrap
python manage.py load_aerodromes
python manage.py load_buffers
python manage.py merge_airports_data
python manage.py regenerate_buffers --radii 3 5 10 --type both

# Verify
python manage.py verify_data
```
