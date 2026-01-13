# Second Brain

Local personal knowledge management system with AI classification, voice input, and automated resurfacing.

## Tech Stack

- **Backend:** Python 3.10+, Flask
- **Frontend:** Single HTML file (vanilla JS, no build step)
- **Storage:** Obsidian vault (markdown + YAML frontmatter)
- **AI:** Anthropic Claude API (primary), OpenAI API (Whisper transcription)

## Project Structure

```
second-brain/
├── backend/
│   ├── app.py                 # Flask server, all routes
│   ├── config.py              # Environment config
│   ├── services/
│   │   ├── classifier.py      # AI classification
│   │   ├── transcriber.py     # Whisper transcription
│   │   ├── vault.py           # Obsidian read/write
│   │   ├── query.py           # Natural language queries
│   │   └── digest.py          # Daily/weekly digests
│   └── prompts/
│       ├── classification.txt
│       ├── query.txt
│       ├── daily_digest.txt
│       └── weekly_digest.txt
├── frontend/
│   └── index.html             # Complete UI (single file)
├── vault/                     # Obsidian vault
│   ├── People/
│   ├── Projects/
│   ├── Ideas/
│   ├── Admin/
│   ├── InboxLog/
│   └── _digests/
├── .env                       # API keys (never commit)
├── requirements.txt
└── CLAUDE.md
```

## API Routes

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Serve frontend |
| `/api/capture` | POST | Classify text → write to vault |
| `/api/transcribe` | POST | Audio file → text via Whisper |
| `/api/query` | POST | Natural language vault query |
| `/api/fix` | POST | Reclassify misclassified item |
| `/api/digest/daily` | GET | Generate daily digest |
| `/api/digest/weekly` | GET | Generate weekly digest |

## Obsidian File Conventions

All markdown files use YAML frontmatter. Required fields by type:

**People:**
```yaml
type: people
name: string
context: string
follow_ups: string
last_touched: YYYY-MM-DD
tags: [string]
confidence: float
source_id: string
```

**Projects:**
```yaml
type: project
name: string
status: active | waiting | blocked | someday | done
next_action: string
due_date: YYYY-MM-DD | null
last_touched: YYYY-MM-DD
tags: [string]
confidence: float
source_id: string
```

**Ideas:**
```yaml
type: idea
name: string
one_liner: string
last_touched: YYYY-MM-DD
tags: [string]
confidence: float
source_id: string
```

**Admin:**
```yaml
type: admin
name: string
due_date: YYYY-MM-DD | null
status: todo | done
last_touched: YYYY-MM-DD
confidence: float
source_id: string
```

**InboxLog:**
```yaml
type: inbox_log
original_text: string
filed_to: people | projects | ideas | admin | needs_review
destination_name: string
destination_file: string
confidence: float
status: filed | needs_review | fixed
created: ISO datetime
```

## Key Patterns

### Classification Flow
1. Receive text from `/api/capture`
2. Call Claude with `prompts/classification.txt`
3. Parse JSON response (handle markdown wrapping)
4. Write destination file to `vault/{Category}/`
5. Write audit entry to `vault/InboxLog/`
6. Return confirmation

### Query Flow
1. Receive question from `/api/query`
2. Read all vault contents via `vault.read_vault_contents()`
3. Format as context string
4. Call Claude with `prompts/query.txt`
5. Return natural language answer

### File Naming
- Sanitize names: alphanumeric, spaces, hyphens, underscores only
- Source ID format: `YYYY-MM-DD_HHMMSS`
- InboxLog files: `{source_id}.md`

### Confidence Threshold
- ≥0.6: Auto-file to destination
- <0.6: File to `needs_review`, prompt user to clarify

## Environment Variables

```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
CLAUDE_MODEL=claude-sonnet-4-20250514
OPENAI_MODEL=gpt-4o-mini
WHISPER_MODEL=whisper-1
VAULT_PATH=./vault
HOST=127.0.0.1
PORT=5000
```

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run server
cd backend && python app.py

# Create vault structure
mkdir -p vault/{People,Projects,Ideas,Admin,InboxLog,_digests}
```

## Dependencies

```
flask>=3.0.0
flask-cors>=4.0.0
anthropic>=0.40.0
openai>=1.50.0
python-dotenv>=1.0.0
pyyaml>=6.0.0
python-frontmatter>=1.1.0
```

## Rules

1. **Never commit `.env`** — contains API keys
2. **Always update `last_touched`** when modifying vault files
3. **Always create InboxLog entry** for every capture (audit trail)
4. **Prompts are in separate .txt files** — don't hardcode in Python
5. **Frontend is single HTML file** — no npm, no build step
6. **Frontmatter must be valid YAML** — use `python-frontmatter` library
7. **Classification JSON must be parsed defensively** — AI may wrap in markdown
8. **File operations use pathlib.Path** — cross-platform compatibility

## Extending

To add a new category (e.g., "Meetings"):
1. Add folder to vault structure
2. Add frontmatter schema to this doc
3. Update `classifier.py` folder mapping
4. Update `prompts/classification.txt` with new category
5. Update frontend fix dropdown

To add a new digest type:
1. Create `prompts/{type}_digest.txt`
2. Add function to `digest.py`
3. Add route to `app.py`
4. Add button to frontend
