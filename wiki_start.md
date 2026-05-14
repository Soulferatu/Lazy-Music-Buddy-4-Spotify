# Wiki Start

This project uses an LLM-friendly wiki structure. The goal is to keep source material, processed knowledge, and navigation separate so future updates are easy to search, audit, and extend.

## Folder Structure

- `raw/` stores original source documents, copied references, meeting notes, prompts, exports, or rough captures.
- `wiki/` stores processed knowledge pages written for clarity and reuse.
- `index.md` is the master index of wiki pages and their relationships.
- `log.md` records every ingest operation.
- `Start.MD` remains the original project brief and roadmap source.

## How The Workflow Works

1. Add source material to `raw/`.
2. Read the source and create a focused processed page in `wiki/`.
3. Link the processed page from `index.md`.
4. Record the operation in `log.md`.
5. Keep processed pages concise, searchable, and connected to related pages.

## What Belongs In `raw/`

Use `raw/` for material that should remain close to its original form:

- Original prompts.
- Research notes.
- API documentation excerpts or links.
- Planning notes.
- User decisions.
- Imported lineup or festival source data.

Do not rewrite source material in `raw/`. If it needs interpretation, summarize it into a `wiki/` page instead.

## What Belongs In `wiki/`

Use `wiki/` for stable, processed knowledge:

- Product decisions.
- Architecture notes.
- API integration summaries.
- Data model explanations.
- Development stage summaries.
- Open questions and resolved answers.

Each wiki page should start with a short purpose statement and should link back to its source material when possible.

## How To Search

From the project root, use these commands:

```powershell
rg "spotify" raw wiki index.md log.md Start.MD
rg "OAuth" raw wiki index.md log.md Start.MD
rg "Stage 3" raw wiki index.md log.md Start.MD
```

Search tips:

- Search `raw/` when you need the original wording.
- Search `wiki/` when you need the cleaned-up project knowledge.
- Search `index.md` when you need to discover which page owns a topic.
- Search `log.md` when you need to know when and why something changed.

## How To Update The Wiki

When adding new knowledge:

1. Put the original material in `raw/` when there is a durable source to preserve.
2. Create or update one focused page in `wiki/`.
3. Add the page to `index.md`.
4. Add related pages in the `Related Pages` column.
5. Add an entry to `log.md`.

When changing existing knowledge:

1. Find the current page through `index.md` or `rg`.
2. Update the smallest relevant section.
3. Preserve links back to the source material.
4. Record the change in `log.md`.

## Naming Conventions

- Use lowercase filenames in `wiki/`.
- Use underscores between words, for example `spotify_integration.md`.
- Keep one main topic per wiki page.
- Prefer links over duplicated explanations.

## Completed Initial Ingests

- `wiki/project_overview.md` summarizes the stable product goal and current scope.
- `wiki/development_stages.md` summarizes the staged roadmap.
- `wiki/spotify_integration.md` captures Spotify constraints, ownership modes, and OAuth risks.
- `wiki/pwa_requirements.md` captures installability, mobile behavior, and deployment-related PWA notes.

## Next Suggested Ingests

- Extract setlist.fm lookup, matching, fallback rules, and API risks into `wiki/setlistfm_integration.md`.
- Extract previous Wacken year support, source attribution, and curation rules into `wiki/historical_lineup_data.md`.
