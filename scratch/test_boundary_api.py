import urllib.request
import json

for loc in ['Puttur', 'Mumbai', 'Kundapura', 'Delhi', 'London']:
    try:
        url = f"http://127.0.0.1:5000/api/nowcast?location={loc}"
        req = urllib.request.Request(url, headers={'User-Agent': 'AeroCast/2.0'})
        resp = urllib.request.urlopen(req, timeout=12)
        data = json.loads(resp.read().decode())
        is_ka = data.get("is_karnataka")
        lat = data.get("latitude")
        lon = data.get("longitude")
        warning = data.get("warning")
        print(f"[{loc}] -> is_karnataka: {is_ka} | lat: {lat}, lon: {lon}")
        if warning:
            print(f"   WARNING: {warning}")
    except Exception as e:
        print(f"[{loc}] -> Error: {e}")
