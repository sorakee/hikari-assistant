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
    date = datetime.strptime(date, "%d %B %Y")
    events = gc.get_events(date, date + timedelta(7), order_by="startTime", single_events=True)
    events_info = []

    if not events:
        return None
    
    for e in events:
        summary = e.summary
        location = e.location
        start_time = e.start.strftime("%d %B %Y, %H:%M:%S")
        end_time = e.end.strftime("%d %B %Y, %H:%M:%S")
        events_info.append(f"- {summary} at {location} from {start_time} until {end_time}")
    
    return events_info


if __name__ == "__main__":
    print(get_event("26 August 2024"))