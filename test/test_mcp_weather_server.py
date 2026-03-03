import sys, os
# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from mcp_server.mcp_weather_server import app

client = TestClient(app)

def test_get_weather_no_params():
    """Call the endpoint without filters – should return all rows (or at least one)."""
    response = client.get("/weather")
    assert response.status_code == 200, f"Unexpected status: {response.status_code}"
    data = response.json()
    assert isinstance(data, list)
    # At least one record should exist because we populated earlier
    assert len(data) > 0
    # Verify required fields exist in the first record
    first = data[0]
    for key in ["city", "fx_date", "update_time"]:
        assert key in first

def test_get_weather_city_filter():
    """Filter by a known city – expect only that city in results."""
    response = client.get("/weather", params={"city": "北京"})
    assert response.status_code == 200
    data = response.json()
    assert all(item["city"] == "北京" for item in data)
