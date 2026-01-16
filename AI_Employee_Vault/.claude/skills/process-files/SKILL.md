# Process Files Skill

## Purpose

This Agent Skill processes files in the `Needs_Action` folder by:
1. Reading file content
2. Analyzing and summarizing based on file type
3. Updating metadata with summary
4. Moving processed files to `Done` folder

## Usage

```bash
# Process all pending files in Needs_Action
claude-code --skill process-files

# Process specific file
claude-code --skill process-files --file "FILE_document_20260112.md"
```

## Requirements

- **Vault Structure**: Must have Inbox/, Needs_Action/, Done/, Logs/ folders
- **Company Handbook**: Company_Handbook.md must exist with processing rules
- **Metadata Files**: Files in Needs_Action must have corresponding FILE_*.md metadata
- **File Types Supported**:
  - Text files (.txt, .md)
  - PDF documents (.pdf)
  - Images (.png, .jpg, .jpeg)
  - Documents (.docx, .doc)
  - Unknown types (basic metadata only)

## Processing Rules

The skill follows rules defined in `Company_Handbook.md`:

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

## Error Handling

- **Corrupted files**: Moved to Needs_Action/Quarantine/ with error logged
- **Permission errors**: Logged and skipped, notification in Dashboard
- **Processing timeout**: Logged as failed, moved to Quarantine
- **Large files (>10MB)**: Warning logged, processing attempted with timeout

## Logging

All processing events are logged to `Logs/YYYY-MM-DD.json`:
- `file_processed` - Successful processing
- `file_processing_failed` - Processing error
- `file_quarantined` - Moved to Quarantine
- `summary_created` - Summary added to metadata

## Output

For each processed file:
1. **Metadata Updated**: Summary added to FILE_*.md in frontmatter and body
2. **File Moved**: Original file moved from Needs_Action/ to Done/
3. **Log Entry**: JSON log entry created with processing details
4. **Dashboard Updated**: Statistics and recent activity updated

## Example Workflow

```
1. User drops document.txt in Inbox/
2. Watcher detects file, creates FILE_document_20260112.md in Needs_Action/
3. Watcher moves document.txt to Needs_Action/
4. User invokes: claude-code --skill process-files
5. Skill reads document.txt content
6. Skill analyzes and creates summary
7. Skill updates FILE_document_20260112.md with summary
8. Skill moves document.txt to Done/
9. Skill logs processing event
10. Dashboard shows updated statistics
```

## Development Notes

- Uses Claude Code API for AI-powered analysis
- Follows Company_Handbook.md rules for consistency
- Implements graceful degradation for unsupported file types
- All operations are logged for audit trail
- Atomic file operations prevent data loss
