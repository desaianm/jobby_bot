# Jobby Bot Documentation

Welcome to the Jobby Bot documentation! This directory contains technical documentation for developers working on or with the Jobby Bot system.

## Quick Links

- **[CLAUDE.md](../CLAUDE.md)** - Main project documentation with development conventions, architecture, and best practices
- **[README.md](../README.md)** - User-facing guide with installation, usage, and setup instructions
- **[pyproject.toml](../pyproject.toml)** - Project dependencies and configuration

## Documentation Structure

### For Users
Start with the [main README](../README.md) to:
- Install and set up Jobby Bot
- Configure your environment
- Learn basic usage patterns
- Set up Notion integration

### For Developers
Read [CLAUDE.md](../CLAUDE.md) to understand:
- Multi-agent architecture
- Development conventions
- How to add new agents
- Common patterns and best practices
- Debugging and troubleshooting

## Key Concepts

### Multi-Agent System
Jobby Bot uses a lead orchestrator agent (Sonnet 4.5) that spawns specialized subagents (Haiku 4.5) for specific tasks:
- **job-finder**: Searches jobs via JobSpy
- **resume-writer**: Creates ATS-optimized resumes
- **cover-letter**: Generates personalized cover letters
- **notion-agent**: Tracks applications in Notion

### File-Based Communication
Agents communicate through the file system:
- Input: `user_data/` (resume, preferences)
- Output: `output/` (job listings, resumes, cover letters)
- Logs: `logs/session_*/` (transcripts, tool calls)

### Session Tracking
All agent actions are tracked via hooks and logged to:
- `transcript.txt` - Human-readable conversation
- `tool_calls.jsonl` - Structured tool invocation records

## Getting Help

1. **Setup issues**: Check [README.md](../README.md) troubleshooting section
2. **Development questions**: Reference [CLAUDE.md](../CLAUDE.md)
3. **Architecture details**: Review `jobby_bot/agent.py` and agent prompts
4. **Session debugging**: Examine logs in `logs/session_TIMESTAMP/`

## Contributing

When adding new features:
1. Follow conventions in [CLAUDE.md](../CLAUDE.md)
2. Update relevant documentation
3. Add agent prompts to `jobby_bot/prompts/`
4. Test thoroughly with session logs
5. Keep changes minimal and focused

## Project Structure Overview

```
jobby_bot/
├── CLAUDE.md              # Main developer documentation
├── README.md              # User guide and setup
├── docs/                  # This directory
├── jobby_bot/             # Main package
│   ├── agent.py           # Entry point and orchestrator
│   ├── prompts/           # Agent system prompts
│   ├── tools/             # Custom tool implementations
│   └── utils/             # Shared utilities
├── scripts/               # Utility scripts (PDF conversion)
├── user_data/             # User configuration and resume
├── output/                # Generated materials
└── logs/                  # Session tracking and debugging
```

## Additional Resources

- [Claude Agent SDK](https://github.com/anthropics/claude-agent-sdk)
- [JSON Resume Format](https://jsonresume.org/)
- [JobSpy](https://github.com/Bunsly/JobSpy)
- [Notion API](https://developers.notion.com/)
