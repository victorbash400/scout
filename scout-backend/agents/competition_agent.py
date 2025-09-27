import os
import requests
import logging
from typing import List, Dict
from dotenv import load_dotenv

from strands import Agent, tool
from config.settings import settings
from strands_tools import file_write

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Tool 1: Find Competing Businesses ---
@tool
def find_competitors(business_type: str, area: str) -> str:
    """
    Finds competing businesses in a specified area using the Google Places API v1.
    It returns a summary of the top 5 competitors found.

    Args:
        business_type: The type of business to search for (e.g., "bakery", "gym").
        area: The geographic location to search within (e.g., "Juja, Kiambu County").

    Returns:
        A string summarizing the number of competitors found and details of the top 5.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return "Error: GOOGLE_PLACES_API_KEY is not configured."

    url = "https://places.googleapis.com/v1/places:searchText"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress"
    }
    data = {"textQuery": f"{business_type} in {area}"}

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()  # Raise an exception for bad status codes
        places_data = response.json()

        competitors = places_data.get("places", [])
        if not competitors:
            return f"No direct competitors found for '{business_type}' in '{area}'."

        summary = f"Found {len(competitors)} direct competitors. Here are the top {min(5, len(competitors))}:\n"
        for i, place in enumerate(competitors[:5]):
            name = place.get('displayName', {}).get('text', 'N/A')
            address = place.get('formattedAddress', 'N/A')
            summary += f"{i+1}. Name: {name}, Address: {address}\n"
        
        return summary.strip()

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed in find_competitors: {e}")
        return f"Error: Failed to communicate with the Google Places API. {e}"

# --- Tool 2: Get Location Images ---
@tool
def get_location_images(area: str, count: int = 2) -> str:
    """
    Finds notable landmarks or places in an area and returns direct URLs to their photos.
    This uses a two-step process: first find places with photos, then get their image URIs.

    Args:
        area: The geographic location to find images for (e.g., "downtown Juja").
        count: The number of image URLs to return. Defaults to 2.

    Returns:
        A string listing the direct URLs of the found images.
    """
    api_key = os.getenv("GOOGLE_PLACES_API_KEY")
    if not api_key:
        return "Error: GOOGLE_PLACES_API_KEY is not configured."

    # Step 1: Search for places with photos
    search_url = "https://places.googleapis.com/v1/places:searchText"
    search_headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.photos"
    }
    search_data = {"textQuery": f"notable landmark in {area}"}

    try:
        search_response = requests.post(search_url, headers=search_headers, json=search_data)
        search_response.raise_for_status()
        places_data = search_response.json()
        
        photo_names = []
        places = places_data.get("places", [])
        for place in places:
            if "photos" in place and place["photos"]:
                photo_names.append(place["photos"][0]["name"])
            if len(photo_names) >= count:
                break
        
        if not photo_names:
            return f"Could not find any images for landmarks in '{area}'."

        # Step 2: Get the photoUri for each photo name
        image_urls = []
        for photo_name in photo_names:
            photo_url = f"https://places.googleapis.com/v1/{photo_name}/media?key={api_key}&maxHeightPx=800&maxWidthPx=800&skipHttpRedirect=true"
            photo_resp = requests.get(photo_url)
            if photo_resp.status_code == 200:
                photo_json = photo_resp.json()
                if "photoUri" in photo_json:
                    image_urls.append(photo_json["photoUri"])

        if not image_urls:
            return "Found places with photos, but could not retrieve the final image URLs."

        return f"Found {len(image_urls)} images for '{area}':\n" + "\n".join(image_urls)

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed in get_location_images: {e}")
        return f"Error: Failed to communicate with the Google Places API. {e}"


# --- CompetitionAgent Class ---
class CompetitionAgent:
    def __init__(self):
        if not os.getenv("GOOGLE_PLACES_API_KEY"):
            raise ValueError("GOOGLE_PLACES_API_KEY environment variable not set.")

        # AWS credentials for Bedrock
        # Load AWS credentials (optional, but needed for Bedrock)
        if settings.aws_access_key_id:
            os.environ['AWS_ACCESS_KEY_ID'] = settings.aws_access_key_id
        if settings.aws_secret_access_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = settings.aws_secret_access_key
        if settings.aws_region:
            os.environ['AWS_DEFAULT_REGION'] = settings.aws_region
        self.agent = Agent(
            name="Competition Agent",
            model=settings.bedrock_model_id,
            system_prompt="""You are a meticulous Competition Analyst. Your mission is to generate a competition report for a new business in a specific location. You must use the provided tools in a logical sequence.

            **Your process must be:**
            1.  **State your plan.** First, analyze the user's request and state that you will begin by searching for competitors.
            2.  **Call `find_competitors`:** Use this tool to get a list of competing businesses.
            3.  **State the next step.** After getting the competitor list, state that you will now find images of the area to provide visual context.
            4.  **Call `get_location_images`:** Use this tool to get 2-3 images of the specified area.
            5.  **Synthesize the Final Report:** Combine the information from the tools into a single, comprehensive final answer. The report should include the number of competitors, details on the top 5, a summary of the competition level (e.g., high, medium, low), and the image URLs.
            6.  **Save the report:** Use the `file_write` tool to save the final report to a file named `competition_report.md` in the `reports/` directory.
            """,
            tools=[
                find_competitors,
                get_location_images,
                file_write
            ]
        )
        logger.info("✅ Competition Agent initialized correctly.")

    def run(self, business_type: str, area: str) -> str:
        """
        Runs the agent to generate a full competition analysis.
        """
        prompt = (
            f"Generate a full competition report for a new '{business_type}' in '{area}'. "
            "Follow your instructions precisely to find competitors and location images, "
            "then combine everything into a final summary and save it to a file."
        )
        
        response = self.agent(prompt)
        return str(response.message)

# --- Entry Point for Orchestrator ---

# Create a single, global instance of the agent
competition_agent_instance = CompetitionAgent()

def run_competition_agent(tasks: List[str]) -> str:
    """
    This function is the entry point for the Competition Agent, called by the Orchestrator.
    It expects the 'tasks' list to contain two items: [business_type, area].
    """
    if len(tasks) != 2:
        return "Error: The Competition Agent requires exactly two tasks: a business type and an area."
    
    business_type, area = tasks
    logger.info(f"🕵️‍♂️ Competition Agent received tasks: Analyze '{business_type}' in '{area}'.")
    
    return competition_agent_instance.run(business_type, area)

# --- Example Usage (for direct testing) ---
if __name__ == "__main__":
    # This block allows you to test the agent directly without the orchestrator
    test_tasks = ["specialty coffee shop", "Juja, Kiambu County"]
    
    analysis_result = run_competition_agent(test_tasks)
    
    print("\n--- AGENT'S FINAL REPORT ---")
    print(analysis_result)
    print("----------------------------\n")
