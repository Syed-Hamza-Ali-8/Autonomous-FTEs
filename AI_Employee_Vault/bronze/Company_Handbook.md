# Company Handbook

## Purpose and Scope
This AI Employee assists with file processing and organization. It monitors the Inbox folder, analyzes files, creates summaries, and maintains the Dashboard for visibility.

## Processing Rules

### Text Files (.txt, .md)
- Extract main topics and themes
- Summarize in 2-3 clear sentences
- Identify action items if present
- Note word count and key information

### PDF Documents (.pdf)
- Extract title and author if available
- Summarize key sections and findings
- Note page count and document length
- Identify document type (report, invoice, article, etc.)

### Images (.png, .jpg, .jpeg)
- Describe visual content and composition
- Identify any text visible in the image
- Note dimensions and file size
- Describe colors and style

### Documents (.docx, .doc)
- Extract title and metadata
- Summarize main content
- Note document structure (headings, sections)
- Identify document purpose

### Unknown File Types
- Record filename and size
- Note that detailed analysis is not available
- Move to Done without deep analysis
- Log the file type for future reference

## Logging Requirements
- Log all file detections with timestamp
- Log all processing attempts (success and failure)
- Log all errors with full details and stack traces
- Use JSON format for machine readability
- Include file size and type in all logs

## Error Handling Guidelines
- **Corrupted files:** Move to Quarantine subfolder, log error details
- **Permission errors:** Log error and skip file, notify in Dashboard
- **Unknown file types:** Create basic metadata only, no deep analysis
- **Processing timeout:** Log error, mark as failed, move to Quarantine
- **Large files (>10MB):** Log warning, attempt processing with timeout

## Quality Standards
- Summaries should be concise (2-3 sentences for text, 1-2 for images)
- Always include file metadata (size, type, date)
- Use clear, professional language
- Highlight actionable information when present
- Maintain consistent formatting

## Privacy & Security
- All data remains local in this vault
- No external API calls except Claude Code
- No credentials stored in files
- Logs contain no sensitive personal information
