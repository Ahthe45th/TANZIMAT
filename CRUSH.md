# TANZIMAT Codebase Guidelines

## Build/Lint/Test Commands
- **Python scripts**: `python script.py` (no formal testing framework)
- **Shell scripts**: `bash script.sh` or make executable with `chmod +x script.sh`
- **C++ (logkeys)**: `cd logger/logkeys && ./autogen.sh && ./configure && make`
- **TypeScript (MCP server)**: `cd template-mcp-server && npm install && npm run build`
- **Run single script**: `python scripts/script_name.py` or `bash scripts/script_name.sh`

## Code Style Guidelines
- **Python**: snake_case variables/functions, PascalCase classes, 4-space indentation
- **Shell**: lowercase_with_underscores, shebang `#!/bin/bash`, `set -euo pipefail`
- **Imports**: Group stdlib → third-party → local, one import per line
- **Error handling**: Use try/except with specific exceptions, proper exit codes

## Naming Conventions
- Files: descriptive_names.with_extension
- Variables: descriptive, avoid unnecessary abbreviations
- Functions: verb_based_names indicating action
- Scripts should be executable and include shebang

## Best Practices
- Include error handling in all scripts
- Use absolute paths for file operations
- Follow existing patterns in similar files
- Add minimal comments for complex logic only