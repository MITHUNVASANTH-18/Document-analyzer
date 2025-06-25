import requests

# ✅ Replace this with your actual Google Maps API Key
GOOGLE_MAPS_API_KEY = ""

# 🔍 Full property address to geocode
address = """
V-686, Rishi Nagar, Shakur Basti,
SALEEMPUR MAZRA MADIPUR, Pitampura,
North Delhi, Delhi, 110034
"""

def get_lat_lon_from_address(address, api_key):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }

    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception("Failed to connect to Google Maps API.")

    data = response.json()

    if data["status"] == "OK":
        result = data["results"][0]
        print(result)
        location = result["geometry"]["location"]
        lat = location["lat"]
        lon = location["lng"]
        formatted_address = result["formatted_address"]
        return {
            "latitude": lat,
            "longitude": lon,
            "formatted_address": formatted_address,
            "source": "google_geocoded"
        }
    else:
        raise Exception(f"Geocoding failed: {data.get('status')} - {data.get('error_message')}")

# Run the geocoder
if __name__ == "__main__":
    try:
        result = get_lat_lon_from_address(address.strip(), GOOGLE_MAPS_API_KEY)
        print("📍 Geocoded Address:", result["formatted_address"])
        print("🌐 Latitude:", result["latitude"])
        print("🌐 Longitude:", result["longitude"])
    except Exception as e:
        print("❌ Error:", e)
