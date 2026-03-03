import sys, os
# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.spider_weather import fetch_weather_data as fetch_city_weather

def test_fetch():
    city = '北京'
    code = '101010100'
    data = fetch_city_weather(city, code)
    if data is None:
        raise AssertionError('Failed to fetch weather data')
    print('Fetched data keys:', list(data.keys()))
    # Print a sample day if present
    if data.get('daily'):
        print('First day forecast:', data['daily'][0])

if __name__ == '__main__':
    test_fetch()
