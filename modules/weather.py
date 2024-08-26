import asyncio
import python_weather

 
async def get_weather():
    async with python_weather.Client() as client:
        weather = await client.get("Pasir Gudang")
        temp = f"{weather.temperature}°C"
        desc = weather.description
        print(desc)

        for daily in weather.daily_forecasts:
            print(daily)

            for hourly in daily.hourly_forecasts:
                print(hourly)


if __name__ == "__main__":
    asyncio.run(get_weather())