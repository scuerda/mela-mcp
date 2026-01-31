"""AppleScript-based calendar integration for meal scheduling."""

import subprocess
from datetime import datetime, timedelta


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


def get_scheduled_meals(calendar_name: str, days: int = 7, past_days: int = 0) -> list[dict]:
    """Get meals scheduled in a date range relative to today.

    Args:
        calendar_name: Name of the calendar to query
        days: Number of days to look ahead (default 7)
        past_days: Number of days to look back (default 0)

    Returns:
        List of scheduled meals with title, date, time
    """
    start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=days)

    script = f'''
    set startDate to current date
    set time of startDate to 0
    set startDate to startDate - ({past_days} * days)
    set endDate to startDate + ({past_days + days} * days)

    set output to ""
    tell application "Calendar"
        set targetCalendar to first calendar whose name is "{calendar_name}"
        set eventList to (every event of targetCalendar whose start date >= startDate and start date < endDate)
        repeat with evt in eventList
            set evtTitle to summary of evt
            set evtStart to start date of evt
            set dateStr to (year of evtStart as string) & "-" & text -2 thru -1 of ("0" & ((month of evtStart as number) as string)) & "-" & text -2 thru -1 of ("0" & (day of evtStart as string))
            set timeStr to text -2 thru -1 of ("0" & (hours of evtStart as string)) & ":" & text -2 thru -1 of ("0" & (minutes of evtStart as string))
            set output to output & evtTitle & "|||" & dateStr & "|||" & timeStr & "\\n"
        end repeat
    end tell
    return output
    '''

    try:
        output = run_applescript(script)
    except RuntimeError:
        return []

    meals = []
    if output:
        for line in output.strip().split("\n"):
            if line and "|||" in line:
                parts = line.split("|||")
                if len(parts) >= 3:
                    meals.append({
                        "title": parts[0],
                        "date": parts[1],
                        "time": parts[2]
                    })

    return meals


def schedule_meal(calendar_name: str, title: str, date: str, time: str = "18:00") -> dict:
    """Schedule a meal on the calendar.

    Args:
        calendar_name: Name of the calendar to add the event to
        title: Name of the meal/recipe
        date: Date in YYYY-MM-DD format
        time: Time in HH:MM 24-hour format (default 18:00)

    Returns:
        Dict with success status and event details
    """
    year, month, day = date.split("-")
    hour, minute = time.split(":")

    script = f'''
    tell application "Calendar"
        set targetCalendar to first calendar whose name is "{calendar_name}"

        set eventDate to current date
        set year of eventDate to {year}
        set month of eventDate to {month}
        set day of eventDate to {day}
        set hours of eventDate to {hour}
        set minutes of eventDate to {minute}
        set seconds of eventDate to 0

        set endDate to eventDate + (1 * hours)

        set newEvent to make new event at end of events of targetCalendar with properties {{summary:"{title}", start date:eventDate, end date:endDate}}

        return "success"
    end tell
    '''

    try:
        result = run_applescript(script)
        return {
            "success": True,
            "title": title,
            "date": date,
            "time": time,
            "calendar": calendar_name
        }
    except RuntimeError as e:
        return {
            "success": False,
            "error": str(e)
        }
