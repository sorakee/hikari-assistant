import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
from gcsa.google_calendar import GoogleCalendar
from pathlib import Path

load_dotenv()

root_dir = Path(__file__).resolve().parent.parent
filename = root_dir / "credentials.json"

EMAIL = os.getenv("EMAIL")
gc = GoogleCalendar(EMAIL, credentials_path=filename)


def get_event(date: str):
    if "today" in date.lower() or "now" in date.lower():
        date = datetime.now()
    else:
        date = datetime.strptime(date, "%d %B %Y")

    events = gc.get_events(date, date + timedelta(1), order_by="startTime", single_events=True)

    if not events:
        return None
    
    events_info = []
    for e in events:
        summary = e.summary
        location = e.location
        start_time = e.start.strftime("%d %B %Y, %I:%M %p")
        end_time = e.end.strftime("%d %B %Y, %I:%M %p")
        events_info.append(f"- {summary} at {location} from {start_time} until {end_time}")
    
    if not events_info:
        return f"No events on {datetime.strftime(date, "%d %B %Y")}."

    return events_info


if __name__ == "__main__":
    print(get_event("29 August 2024"))