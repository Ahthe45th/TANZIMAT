#!/bin/bash

PROJECTS_DIR="/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH/Projects"

for file in "$PROJECTS_DIR"/*.md; do
    awk '
        BEGIN { printing = 0 }
        /^### Current Actions/ { printing = 1; next }
        /^###/ { printing = 0 }
        printing && /^- / {
            # Extract project name from file path
            project_name = FILENAME
            sub(".*/", "", project_name)
            sub(".md$", "", project_name)
            # Print the action with project name
            print $0 " (project: " project_name ")"
        }
    ' "$file"
done | grep -v '~'
