import requests

latitude = 26.7487
longitude = 83.3296

url = "https://api.open-meteo.com/v1/elevation"

params = {
    "latitude": latitude,
    "longitude": longitude,
}

response = requests.get(url, params=params, timeout=10)
response.raise_for_status()

data = response.json()

print("Latitude:", latitude)
print("Longitude:", longitude)
print("Elevation:", data["elevation"][0], "meters")