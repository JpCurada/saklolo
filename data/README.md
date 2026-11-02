# data

| File | Contents |
|---|---|
| `households.jsonl` | Ground truth per household: location, members, senders |
| `messages.jsonl` | Synthetic messages + labels, with `split` = dev / eval / calibration |
| `archive.jsonl` | Synthetic "past typhoon" posts that recycled messages copy |
| `fake_people.json` | Fake first names and surnames for the generator |
| `psgc/` | PSGC barangay list for geocoding (public data) |
| `hazards/` | Flood hazard polygons for verification |

**Synthetic only.** Never add real names, phone numbers, or posts.
