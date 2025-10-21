# EDI Parser to Structured Ontology - Web Playground

An interactive browser-based playground for transforming EDI files (837P Professional Claims and 835 Electronic Remittance Advice) into structured ontology schemas.

## Features

- 🚀 **Zero Installation**: Runs entirely in your browser using PyScript
- 📝 **Real-time Parsing**: Paste EDI content and see instant transformation
- 📊 **Multiple Views**: Summary statistics, formatted JSON, and interactive tables
- 🎯 **Two Transaction Types**: 837P Professional Claims and 835 Remittance Advice
- 💾 **Sample Data**: Preloaded examples to get started quickly

## Usage

1. Visit the playground at: [Your GitHub Pages URL]
2. Select transaction type (837P or 835) from the dropdown
3. Either:
   - Click "837P Sample" or "835 Sample" to load example data
   - Paste your own EDI file content
4. Click "Transform to Ontology" to parse
5. View results in three tabs:
   - **Summary**: Quick statistics and counts
   - **JSON**: Full structured output
   - **Tables**: Interactive data tables

## Output Schema

### 837P Professional Claims
Extracts:
- **Claims**: Patient info, providers, charges, dates
- **Services**: Procedure codes, modifiers, charges, units
- **Diagnoses**: ICD-10 codes with types (Principal, Secondary, etc.)
- **Providers**: Billing and rendering providers with NPIs
- **Payers**: Insurance company information

### 835 Remittance Advice
Extracts:
- **Denials**: Adjustment reasons, amounts, types
- **Reason Codes**: Unique CARC codes encountered
- **Payment Info**: Total payment, method, dates

## Technology

- **PyScript**: Run Python in the browser
- **Pure Python**: Uses lightweight EDI segment parsing
- **Responsive Design**: Works on desktop and mobile
- **No Backend**: All processing happens client-side

## Local Development

To run locally:

```bash
# Serve the docs directory
python -m http.server 8000 --directory docs

# Or use any static file server
cd docs
npx serve
```

Then open http://localhost:8000

## Future Enhancements

- [ ] Full Bots EDI parser integration
- [ ] Grammar-based validation
- [ ] Export to CSV/Excel
- [ ] Batch file processing
- [ ] Custom field mapping configuration
- [ ] Work queue item generation with priority scoring
