import json
from utils.helpers import extract_names

text = """
# Travel Plan
This is a trip to Goa.
## Destinations
Baga Beach, Fort Aguada.
## Hotel
Taj Hotel in Panaji.
## Food & Dining Guide
You must try the local Goan Fish Curry and Bebinca. Also, have some Pork Vindaloo.
"""

print(json.dumps(extract_names(text), indent=2))
