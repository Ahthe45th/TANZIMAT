import os

PROJECTS_DIR = "/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH/Projects/"
CURRENT_HEADING = "### Current Actions"
COMPLETED_HEADING = "### Completed Actions"

def archive_completed_tasks():
    """
    Scans project files and moves struck-through tasks from 'Current Actions'
    to 'Completed Actions'.
    """
    print(f"Scanning files in {PROJECTS_DIR}...")
    total_files_modified = 0

    for filename in sorted(os.listdir(PROJECTS_DIR)):
        if not filename.endswith(".md"):
            continue

        file_path = os.path.join(PROJECTS_DIR, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except Exception as e:
            print(f"Error reading {filename}: {e}")
            continue

        new_lines = []
        moved_tasks = []
        in_current_section = False
        
        # Check if the completed section exists to determine insertion strategy later
        completed_section_exists = any(line.strip() == COMPLETED_HEADING for line in lines)

        # First pass: Separate lines, removing moved tasks from their original position
        for line in lines:
            if line.strip() == CURRENT_HEADING:
                in_current_section = True
            elif line.strip().startswith("###"):
                in_current_section = False

            # Identify struck-through tasks in the "Current Actions" section
            if in_current_section and line.strip().startswith("~~"):
                moved_tasks.append(line)
            else:
                new_lines.append(line)

        if not moved_tasks:
            continue

        total_files_modified += 1
        print(f"  - Archiving {len(moved_tasks)} task(s) in {filename}")

        # Second pass: Insert the moved tasks into the "Completed Actions" section
        final_lines = []
        if completed_section_exists:
            for line in new_lines:
                final_lines.append(line)
                if line.strip() == COMPLETED_HEADING:
                    final_lines.extend(moved_tasks)
        else:
            # If the completed section doesn't exist, add it at the end of the file
            final_lines = new_lines
            if final_lines and final_lines[-1].strip() != "":
                final_lines.append("\n")
            final_lines.append(f"{COMPLETED_HEADING}\n")
            final_lines.extend(moved_tasks)

        # Write the modified content back to the file
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.writelines(final_lines)
        except Exception as e:
            print(f"Error writing to {filename}: {e}")

    if total_files_modified > 0:
        print(f"\nArchive complete. Modified {total_files_modified} file(s).")
    else:
        print("\nNo completed tasks found to archive.")

if __name__ == "__main__":
    archive_completed_tasks()
