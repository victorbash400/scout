import os
import requests
from dotenv import load_dotenv

# Load .env file
load_dotenv()

API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")
if not API_KEY:
    raise Exception("GOOGLE_PLACES_API_KEY not found in .env")

url = "https://places.googleapis.com/v1/places:searchText"
headers = {
    "Content-Type": "application/json",
    "X-Goog-Api-Key": API_KEY,
    "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.priceLevel,places.photos"
}
data = {
    "textQuery": "Spicy Vegetarian Food in Sydney, Australia"
}


# Step 1: Search for places and get photo resource name
response = requests.post(url, headers=headers, json=data)
print("Status code:", response.status_code)
places_data = response.json()
print("Places response:")
print(places_data)

# Try to get the first photo resource name
photo_name = None
if "places" in places_data and places_data["places"]:
    first_place = places_data["places"][0]
    photos = first_place.get("photos")
    if photos and isinstance(photos, list) and len(photos) > 0:
        photo_name = photos[0].get("name")

if photo_name:
    # Step 2: Get the photoUri using skipHttpRedirect=true
    photo_url = f"https://places.googleapis.com/v1/{photo_name}/media?key={API_KEY}&maxHeightPx=400&maxWidthPx=400&skipHttpRedirect=true"
    photo_resp = requests.get(photo_url)
    print("Photo endpoint status:", photo_resp.status_code)
    try:
        photo_json = photo_resp.json()
        print("Photo endpoint response:")
        print(photo_json)
        if "photoUri" in photo_json:
            print("Image URL:", photo_json["photoUri"])
        else:
            print("No photoUri found in photo endpoint response.")
    except Exception as e:
        print("Could not parse photo endpoint response as JSON.", e)
else:
    print("No photo resource name found in the first place result.")
