# data

| File | Contents |
|---|---|
| `households.jsonl` | Ground truth per household: location, members, senders |
| `messages.jsonl` | Synthetic messages + labels, with `split` = dev / eval / calibration |
| `archive.jsonl` | Synthetic "past typhoon" posts that recycled messages copy |
| `fake_people.json` | Fake first names and surnames for the generator |
| `psgc/` | PSGC barangay list for geocoding (public data) |
| `hazards/` | Flood hazard polygons for verification |

**Synthetic only.** Format and labeling: [docs/dataset-spec.md](../docs/dataset-spec.md).
Definitions: [docs/triage-rubric.md](../docs/triage-rubric.md). Never add anything
[security-privacy rules](../.agents/rules/security-privacy.md) forbid.
