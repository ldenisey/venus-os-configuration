# Get and filter Victron Energy product lists

```python
import requests
import os
import json

# Fields to keep in the filtered JSON output file
fields_to_keep = ['id', 'short_name', 'category']
products_file = 'productids_full.json'
filtered_file = 'productids.json'

if not os.path.exists(products_file):
    # Download the product ID list from Victron Energy's API
    # This is a one-time operation to fetch the latest product IDs
    print("Downloading product ID list...")
    url = 'https://www.victronenergy.com/api/v1/products/?format=json'
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(products_file, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)

# Load the downloaded JSON file
with open(products_file, 'r', encoding='utf-8') as f:
    json_list = json.load(f)

# Filter and order by id
filtered_json = [{k: device.get(k) for k in fields_to_keep} for device in json_list]
filtered_json = sorted(filtered_json, key=lambda device: device.get('id', 0))

# Save the filtered list to a new file
with open(filtered_file, 'w', encoding='utf-8') as f:
    json.dump(filtered_json, f, indent=2)
```
