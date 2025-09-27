def test_price_agent():
    # Realistic scenario: Analyze pricing for a bakery in Manhattan, NY, for specific products
    business_type = "bakery"
    location = "Manhattan, New York, NY"
    products = "croissant, baguette, coffee"
    tasks = [business_type, location, products]
    print(f"Testing Price Agent with: {business_type} in {location} for products: {products}")
    from agents.price_agent import run_price_agent
    result = run_price_agent(tasks)
    print("\n--- AGENT'S FINAL PRICING RECOMMENDATION ---")
    print(result)
    print("----------------------------\n")

if __name__ == "__main__":
    test_price_agent()

    # ...existing code...