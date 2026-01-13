# Second Brain

A local personal knowledge management system with AI classification, voice input, and automated resurfacing.

## What It Does

- **Capture** text or voice notes
- **AI classifies** into People, Projects, Ideas, or Admin
- **Stores** as markdown in an Obsidian-compatible vault
- **Query** your vault with natural language
- **Digests** generate daily/weekly summaries

## Tech Stack

- **Backend:** Python/Flask
- **Frontend:** Single HTML file (no build step)
- **Storage:** Obsidian vault (markdown + YAML frontmatter)
- **AI:** Claude (classification/queries), Whisper (transcription)

## Quick Start

1. Clone this repo
2. Copy `.env.example` to `.env` and add your API keys
3. Install dependencies: `pip install -r requirements.txt`
4. Create vault folders: `mkdir -p vault/{People,Projects,Ideas,Admin,InboxLog,_digests}`
5. Run the server: `cd backend && python app.py`
6. Open `http://localhost:5000` in your browser

## Requirements

- Python 3.10+
- Anthropic API key (Claude)
- OpenAI API key (Whisper transcription)

## Documentation

- `CLAUDE.md` - Full project spec and API reference

## License

MIT
