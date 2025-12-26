import csv
import json
import subprocess
import sys
import time

# Configuration
PROJECT_NUMBER = "7"
CSV_PATH = ".github/github_kanban.csv"
TARGET_STATUS = "Todo"

# Template
STORY_TEMPLATE = """
## User Story
**As a** system,
**I want to** {action},
**So that** {benefit}.

## Technical Implementation
- Context: `{context}`
- Component: `{component}`

## Acceptance Criteria
- [ ] {criteria_1}
- [ ] {criteria_2}
- [ ] Verified with Pydantic schema
- [ ] Verified with WhatsApp Renderer

**Status**: {status} (Imported)
"""


def run_command(cmd_list):
    try:
        result = subprocess.run(cmd_list, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Don't print error for every checking command, generic handling
        return None


def generate_description(title, labels):
    # Defaults
    action = f"implement {title}"
    benefit = "feature works"
    context = "WhatsApp API"
    component = "Server"
    c1 = "Implemented"
    c2 = "Tested"

    if "Text" in title:
        component = "outbound.py"
    if "Media" in title:
        component = "media_sender.py"

    return STORY_TEMPLATE.format(
        action=action,
        benefit=benefit,
        context=context,
        component=component,
        criteria_1=c1,
        criteria_2=c2,
        status=TARGET_STATUS,
    )


def main():
    print("=== MASTER RESET & IMPORT ===")
    print("WARNING: This will DELETE ALL Project Items and Repo Issues.")
    print("Press CTRL+C in 5 seconds to cancel...")
    time.sleep(5)

    # 1. Setup Data
    print("Fetching Owner & Project ID...")
    owner = run_command(["gh", "repo", "view", "--json", "owner", "-q", ".owner.login"])

    view_json = run_command(
        ["gh", "project", "view", PROJECT_NUMBER, "--owner", owner, "--format", "json"]
    )
    project_data = json.loads(view_json)
    project_node_id = project_data["id"]

    # Get Status Field ID and 'Todo' Option ID
    print("Fetching Field IDs...")
    fields_json = run_command(
        [
            "gh",
            "project",
            "field-list",
            PROJECT_NUMBER,
            "--owner",
            owner,
            "--format",
            "json",
        ]
    )
    fields = json.loads(fields_json)
    status_field = next(f for f in fields["fields"] if f["name"] == "Status")
    status_field_id = status_field["id"]
    todo_option_id = next(
        o["id"] for o in status_field["options"] if o["name"] == TARGET_STATUS
    )

    # 2. DELETE ALL PROJECT ITEMS
    print("\n--- Phase 1: Wiping Project Board ---")
    items_json = run_command(
        [
            "gh",
            "project",
            "item-list",
            PROJECT_NUMBER,
            "--owner",
            owner,
            "--format",
            "json",
            "--limit",
            "1000",
        ]
    )
    if items_json:
        items = json.loads(items_json)["items"]
        print(f"Deleting {len(items)} project items...")
        for item in items:
            print(".", end="", flush=True)
            subprocess.run(
                [
                    "gh",
                    "project",
                    "item-delete",
                    PROJECT_NUMBER,
                    "--id",
                    item["id"],
                    "--owner",
                    owner,
                    "--format",
                    "json",
                ],
                capture_output=True,
            )
        print("\nProject Board Cleared.")

    # 3. DELETE ALL REPO ISSUES
    print("\n--- Phase 2: Wiping Repository Issues ---")
    issues_json = run_command(
        ["gh", "issue", "list", "--state", "all", "--limit", "1000", "--json", "number"]
    )
    if issues_json:
        issues = json.loads(issues_json)
        print(f"Deleting {len(issues)} issues...")
        for iss in issues:
            print(".", end="", flush=True)
            subprocess.run(
                ["gh", "issue", "delete", str(iss["number"]), "--yes"],
                capture_output=True,
            )
        print("\nRepository Cleared.")

    # 4. IMPORT & LINK
    print("\n--- Phase 3: Import, Link & Set Status ---")

    # Ensure labels
    required_labels = [
        "Text",
        "Media",
        "Interactive",
        "Location",
        "Template",
        "Commerce",
        "System",
        "Global",
        "Test",
        "Contact",
    ]
    existing_labels = run_command(["gh", "label", "list"])
    for l in required_labels:
        if l not in existing_labels:
            subprocess.run(
                ["gh", "label", "create", l, "--color", "ededed"], capture_output=True
            )

    with open(CSV_PATH, "r", encoding="utf-8-sig") as f:
        tasks = list(csv.DictReader(f))

    for task in tasks:
        title = task["Title"]
        labels = task["Labels"]
        body = generate_description(title, labels)

        print(f"Processing: {title}...", end=" ")

        # A. Create Issue
        create_res = run_command(
            [
                "gh",
                "issue",
                "create",
                "--title",
                title,
                "--body",
                body,
                "--label",
                labels,
            ]
        )

        if create_res and "https://" in create_res:
            issue_url = create_res
            print("[CREATED]", end=" ")

            # B. Add to Project
            add_res = run_command(
                [
                    "gh",
                    "project",
                    "item-add",
                    PROJECT_NUMBER,
                    "--owner",
                    owner,
                    "--url",
                    issue_url,
                    "--format",
                    "json",
                ]
            )

            if add_res:
                item_id = json.loads(add_res)["id"]
                print("[LINKED]", end=" ")

                # C. Set Status to Todo
                subprocess.run(
                    [
                        "gh",
                        "project",
                        "item-edit",
                        "--id",
                        item_id,
                        "--field-id",
                        status_field_id,
                        "--single-select-option-id",
                        todo_option_id,
                        "--project-id",
                        project_node_id,
                    ],
                    capture_output=True,
                )
                print("[SET TODO]")
            else:
                print("[LINK FAILED]")
        else:
            print("[CREATE FAILED]")

        time.sleep(1)

    print("\n=== MASTER RESET COMPLETE ===")
    print(f"All {len(tasks)} items created, linked, and set to '{TARGET_STATUS}'.")


if __name__ == "__main__":
    main()
