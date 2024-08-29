import os
import asyncio
import python_weather
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

LOCATION = os.getenv("LOCATION")

 
async def get_weather(date: str) -> str:
    async with python_weather.Client() as client:
        weather = await client.get(LOCATION)
    
    if "today" or "now" in date.lower():
        date = datetime.now().strftime("%d %B %Y, %I:%M %p")
    
    curr_temp = f"{weather.temperature}°C"
    curr_desc = weather.description

    response = f"Current temperature and weather is {curr_temp}, {curr_desc}\n"
        
    matching_forecast = None

    # Weather Forecast for 3 Days **ONLY** 
    for daily_forecast in weather.daily_forecasts:
        forecast_date = daily_forecast.date
        if forecast_date == datetime.strptime(date, "%d %B %Y").date():
            matching_forecast = daily_forecast

    if matching_forecast:
        response += f"Weather on {date}:\n"
        for hourly in matching_forecast.hourly_forecasts:
            time = hourly.time.strftime("%I:%M %p")
            temp = hourly.temperature
            desc = hourly.description
            response += f"- {time}: {temp}°C, {desc}\n"
        return response
    else:
        return f"No weather forecast available for {date}."
        

if __name__ == "__main__":
    result = asyncio.run(get_weather("28 August 2024"))
    print(result)