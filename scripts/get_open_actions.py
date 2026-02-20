import os

def get_open_actions():
    projects_dir = "/home/mehmet/Proyectos/TANZIMAT/NAFSIYYAH/Projects/"
    open_actions = []

    for filename in os.listdir(projects_dir):
        if filename.endswith(".md"):
            filepath = os.path.join(projects_dir, filename)
            project_name = filename.replace(".md", "")
            with open(filepath, 'r') as f:
                in_current_actions = False
                for line in f:
                    if "### Current Actions" in line:
                        in_current_actions = True
                        continue
                    if "###" in line and in_current_actions:
                        in_current_actions = False
                        continue
                    
                    if in_current_actions and line.strip().startswith("-") and "~" not in line:
                        action = line.strip()
                        open_actions.append(f"{action} (project: {project_name}) (type: current action)")

    for action in open_actions:
        print(action)

if __name__ == "__main__":
    get_open_actions()
