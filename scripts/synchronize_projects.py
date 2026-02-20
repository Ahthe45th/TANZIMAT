import os
import re
import sys

NAFSIYYAH_DIR = "/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH"
OVERVIEW_FILE = os.path.join(NAFSIYYAH_DIR, "Overview.md")
PROJECTS_DIR = os.path.join(NAFSIYYAH_DIR, "Projects")
os.environ['DISPLAY'] = ':1'

def synchronize_projects():
    """
    Synchronizes struck-through tasks from Overview.md to their respective project files.
    1. Finds all struck-through lines in Overview.md.
    2. For each unique task, finds the corresponding project file and strikes through the task there.
    3. Removes all struck-through lines from Overview.md.
    """
    if not os.path.exists(OVERVIEW_FILE):
        print(f"Error: Overview file not found at {OVERVIEW_FILE}")
        sys.exit(1)

    with open(OVERVIEW_FILE, 'r', encoding='utf-8') as f:
        overview_lines = f.readlines()

    lines_to_keep = []
    tasks_by_project = {}
    task_pattern = re.compile(r'~~(- .*?)\(project: (.*?)\)\s*\(type: .*?\)~~')
    
    num_struck_lines = 0
    for line in overview_lines:
        match = task_pattern.match(line.strip())
        if match:
            num_struck_lines += 1
            task_content = match.group(1).strip()
            project_name = match.group(2).strip()
            if project_name not in tasks_by_project:
                tasks_by_project[project_name] = set()
            tasks_by_project[project_name].add(task_content)
        else:
            lines_to_keep.append(line)

    if not tasks_by_project:
        print("No tasks to synchronize.")
        os.system(f"notify-send 'No tasks to synchronize'")
        os.system(f"python {os.environ['HOME']}/Proyectos/TANZIMAT/scripts/get_open_actions.py > {os.environ['HOME']}/Proyectos/TANZIMAT/NAFSIYYAH/Overview.md")
        os.system(f"notify-send 'Refreshed overview file with new tasks.'")
        return

    print(f"Found {num_struck_lines} struck-through tasks. Processing unique tasks per project.")
    os.system(f"notify-send 'Found {num_struck_lines} struck-through tasks. Processing unique tasks per project.'")
    for project_name, tasks_to_strike in tasks_by_project.items():
        project_file_path = os.path.join(PROJECTS_DIR, f"{project_name}.md")

        if not os.path.exists(project_file_path):
            print(f"Warning: Project file not found for '{project_name}' at {project_file_path}")
            continue

        with open(project_file_path, 'r', encoding='utf-8') as f:
            project_lines = f.readlines()

        updated_project_lines = []
        tasks_found_this_project = set()

        for proj_line in project_lines:
            stripped_line = proj_line.strip()
            if stripped_line in tasks_to_strike:
                if not stripped_line.startswith('~~'):
                    updated_project_lines.append("~~" + stripped_line + "~~\n")
                    tasks_found_this_project.add(stripped_line)
                else:
                    updated_project_lines.append(proj_line)
                    tasks_found_this_project.add(stripped_line)
            else:
                updated_project_lines.append(proj_line)
        
        if tasks_found_this_project:
            print(f"  - In '{project_name}.md':")
            for task in tasks_found_this_project:
                 print(f"    - Struck through: {task}")
            with open(project_file_path, 'w', encoding='utf-8') as f:
                f.writelines(updated_project_lines)

        unfound_tasks = tasks_to_strike - tasks_found_this_project
        if unfound_tasks:
            print(f"  - In '{project_name}.md':")
            for task in unfound_tasks:
                print(f"    - Warning: Task not found: {task}")

    with open(OVERVIEW_FILE, 'w', encoding='utf-8') as f:
        f.writelines(lines_to_keep)

    print(f"\nSynchronization complete.")
    os.system(f"notify-send 'Sync Complete.'")
    print(f"Removed {num_struck_lines} struck-through lines from Overview.md.")
    os.system(f"notify-send 'Removed {num_struck_lines} struck-through lines from Overview.md.'")
    os.system(f"python {os.environ['HOME']}/Proyectos/TANZIMAT/scripts/get_open_actions.py > {os.environ['HOME']}/Proyectos/TANZIMAT/NAFSIYYAH/Overview.md")
    os.system(f"notify-send 'Refreshed overview file with new tasks.'")
if __name__ == "__main__":
    synchronize_projects()

