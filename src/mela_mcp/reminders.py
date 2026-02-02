"""AppleScript-based Apple Reminders integration for grocery lists."""

import subprocess


def run_applescript(script: str) -> str:
    """Execute an AppleScript and return the output."""
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"AppleScript error: {result.stderr}")
    return result.stdout.strip()


def add_reminders(items: list[str], list_name: str = "Grocery") -> dict:
    """Add items as reminders to a named list, creating the list if needed.

    Args:
        items: List of item names to add as reminders
        list_name: Name of the Reminders list (default "Grocery")

    Returns:
        Dict with success status and count of items added
    """
    escaped_list = list_name.replace('"', '\\"')

    reminder_lines = ""
    for item in items:
        escaped_item = item.replace('"', '\\"')
        reminder_lines += f'        make new reminder at end of reminders of targetList with properties {{name:"{escaped_item}"}}\n'

    script = f'''
    tell application "Reminders"
        try
            set targetList to list "{escaped_list}"
        on error
            set targetList to make new list with properties {{name:"{escaped_list}"}}
        end try
{reminder_lines}
    end tell
    return "success"
    '''

    try:
        run_applescript(script)
        return {"success": True, "count": len(items), "list": list_name}
    except RuntimeError as e:
        return {"success": False, "error": str(e)}


def clear_reminders(list_name: str = "Grocery") -> dict:
    """Delete all incomplete reminders from a list.

    Args:
        list_name: Name of the Reminders list (default "Grocery")

    Returns:
        Dict with success status and count of items removed
    """
    escaped_list = list_name.replace('"', '\\"')

    script = f'''
    tell application "Reminders"
        try
            set targetList to list "{escaped_list}"
        on error
            return "0"
        end try
        set incompleteItems to (every reminder of targetList whose completed is false)
        set itemCount to count of incompleteItems
        repeat with r in incompleteItems
            delete r
        end repeat
        return itemCount as string
    end tell
    '''

    try:
        result = run_applescript(script)
        count = int(result) if result else 0
        return {"success": True, "removed": count, "list": list_name}
    except RuntimeError as e:
        return {"success": False, "error": str(e)}


def get_reminders(list_name: str = "Grocery") -> dict:
    """Get names of all incomplete reminders from a list.

    Args:
        list_name: Name of the Reminders list (default "Grocery")

    Returns:
        Dict with success status and list of item names
    """
    escaped_list = list_name.replace('"', '\\"')

    script = f'''
    tell application "Reminders"
        try
            set targetList to list "{escaped_list}"
        on error
            return ""
        end try
        set output to ""
        set incompleteItems to (every reminder of targetList whose completed is false)
        repeat with r in incompleteItems
            set output to output & name of r & "|||"
        end repeat
        return output
    end tell
    '''

    try:
        result = run_applescript(script)
        items = []
        if result:
            items = [item for item in result.split("|||") if item]
        return {"success": True, "items": items, "list": list_name}
    except RuntimeError as e:
        return {"success": False, "error": str(e), "items": []}
