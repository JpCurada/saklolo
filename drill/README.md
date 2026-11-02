# Tabletop drill: manual triage vs Saklolo

A 45 to 60 minute session with 2 or 3 volunteers. Each volunteer sorts rescue requests
twice, once by hand and once with Saklolo. It fills the Drill table in
`eval/results.md`: critical cases missed, messages triaged in 15 minutes, and
duplicates missed.

All messages are synthetic. No real people or rescue requests are involved.

## People and materials

- **Facilitator:** runs the clock and the computer, and doesn't help sort.
- **2 or 3 volunteers:** responders or community volunteers are best. Say who took part
  when you report the results.
- One laptop per round, a spreadsheet app, a timer, and a signed copy of
  [consent.md](consent.md) from each volunteer.
- Keep `keys/` closed until scoring. Volunteers must never see it.

## Files

| File | Use |
|---|---|
| `sets/set-a.csv`, `sets/set-b.csv` | The message sheets volunteers read in a manual round |
| `sets/set-a.jsonl`, `sets/set-b.jsonl` | The same messages, fed to Saklolo |
| `keys/*-key.json` | Answer keys, for scoring only |
| `manual-template.csv` | The sheet volunteers fill in during a manual round |
| `consent.md` | Consent form |
| `results/` | Your round outputs. Not committed |

The two sets are equivalent, and no household appears in both:

| Set | Messages | Households | Critical | Duplicates | Recycled |
|---|---|---|---|---|---|
| A | 75 | 38 | 15 | 23 | 4 |
| B | 75 | 37 | 13 | 22 | 4 |

To rebuild them exactly, run `uv run python -m saklolo.drill.sets` from `api/`.

## Who does what

Each volunteer sees each set once, so nobody meets the same messages twice. Order and
set both rotate, so practice doesn't favor either method.

| Volunteer | Round 1 | Round 2 |
|---|---|---|
| V1 | Manual, set A | Saklolo, set B |
| V2 | Saklolo, set A | Manual, set B |
| V3 | Manual, set B | Saklolo, set A |
| V4, if any | Saklolo, set B | Manual, set A |

Use V1, V2, and so on in file names and on screen, never real names.

## Setup (10 minutes before)

1. From the repo root, start the API with `make demo`, and the dashboard with
   `make demo-web` in a second terminal. Both need AWS credentials unless an offline
   mode is available; if so, use it, and note that in the results.
2. Open <http://127.0.0.1:3000> and check that it loads.

## Briefing (5 minutes)

Read this aloud:

> You are a volunteer dispatcher during a typhoon in Marikina. Requests are coming in.
> Your job is to find who needs help first. P1 is a threat to life now: water at neck
> or roof, a medical emergency, or an infant, senior, pregnant, or disabled person
> trapped in high or rising water. P2 is trapped but stable. P3 can wait. P4 isn't a
> rescue. Some messages repeat the same household, and some are old posts. You have 15
> minutes. You won't finish everything, and that's expected. Most urgent first.

Allow one or two questions, then give no more help.

## Manual round (15 minutes)

1. Give the volunteer the set's CSV and a copy of `manual-template.csv`, saved as
   `results/v1-manual.csv`.
2. Start the timer. For each message handled, the volunteer fills in one row:

   | Column | Meaning |
   |---|---|
   | `message_id` | From the sheet, such as `msg-0042` |
   | `minute` | Minutes on the timer when they filed it |
   | `case_label` | Any label for the household. Same household, same label |
   | `priority` | P1, P2, P3, or P4 |
   | `suspicious` | Y if it looks like an old post or spam |
   | `barangay`, `people`, `notes` | Optional |

3. Stop at 15:00. Rows with a `minute` over 15 don't count.

## Saklolo round (15 minutes)

1. Restart `make demo`, so the round starts empty.
2. Start the timer, and in a third terminal, from `api/`, feed the set. The agents' work
   counts toward the 15 minutes:

   ```bash
   uv run python -m saklolo.drill.api_round feed ../drill/sets/set-b.jsonl
   ```

3. The volunteer starts a shift as `V1`, works through the queue, and overrides any
   priority they disagree with. They use the dashboard only.
4. At 15:00, export the state:

   ```bash
   uv run python -m saklolo.drill.api_round export ../drill/results/v1-saklolo.json
   ```

If the feed hasn't finished at 15:00, export anyway. Unfinished messages count as not
triaged.

## Debrief (5 minutes)

Ask what was hardest, what they didn't trust, and what they'd change. Take notes. A quote
goes in the video only if they agreed on the consent form.

## Scoring

From `api/`, pass one `--round` per round, as mode, key, and file:

```bash
uv run python -m saklolo.drill.score \
  --round manual ../drill/keys/set-a-key.json ../drill/results/v1-manual.csv \
  --round saklolo ../drill/keys/set-b-key.json ../drill/results/v1-saklolo.json
```

It prints the table for `eval/results.md`, plus each round's detail.

| Measure | What counts |
|---|---|
| **Critical case missed** | A critical household with no message at P1 in time |
| **Messages triaged in 15 min** | Messages with a priority in time |
| **Duplicate missed** | A triaged message filed under a different case from most of its household |

With Saklolo, the priority that counts is the case's final one, after any override.
Recycled posts flagged also appear in the round detail.

## Report it honestly

- **Saklolo's "triaged" count is the agents' work.** It shows messages given a priority,
  not messages the volunteer read. Say so when you report it.
- **This is a small drill,** not a study. Report the number of volunteers and who they
  were, and don't state percentages as general findings. If no responder took part,
  change the video narration, which says "a responder".
- **The sets come from the dev split,** which Saklolo was tuned on, and that favors it.
  Rebuild from the held-out eval split once it exists, by filtering on that split in
  `sets.py`, or disclose this.
- **The keys are provisional.** Their priorities are the data generator's intent until
  human labels exist. Rebuild the keys after labeling, then score again.
