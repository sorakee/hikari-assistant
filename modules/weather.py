import os
import asyncio
import python_weather
from dotenv import load_dotenv

load_dotenv()

LOCATION = os.getenv("LOCATION")

 
async def get_weather():
    async with python_weather.Client() as client:
        weather = await client.get(LOCATION)
        temp = f"{weather.temperature}°C"
        desc = weather.description
        print(desc)

        for daily in weather.daily_forecasts:
            print(daily)

            for hourly in daily.hourly_forecasts:
                print(hourly)


if __name__ == "__main__":
    asyncio.run(get_weather())