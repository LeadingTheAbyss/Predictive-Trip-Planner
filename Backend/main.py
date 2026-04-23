from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import requests
import os
import math

app = FastAPI(title = "When-To-Go API")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"], 
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "YOUR_API_KEY_HERE")
class TripRequest(BaseModel):
    origin: str
    destination: str
    
def generate_time_slots(hours_ahead = 4, interval_mins = 30):
    """Generates future time slots as Unix timestamps."""
    slots = []
    now = datetime.now()
    discard_minutes = now.minute % interval_mins
    next_slot = now + timedelta(minutes=(interval_mins - discard_minutes))
    
    for i in range(math.ceil((hours_ahead * 60) / interval_mins)):
        target_time = next_slot + timedelta(minutes=interval_mins * i)
        slots.append({
            "readable_time": target_time.strftime("%I:%M %p"),
            "timestamp": int(target_time.timestamp())
        })
    return slots

def get_travel_time(origin: str, destination: str, departure_time: int):
    """Calls Google Maps Distance Matrix API."""
    url = "https://maps.googleapis.com/maps/api/distancematrix/json"
    params = {
        "origins": origin,
        "destinations": destination,
        "departure_time": departure_time, 
        "key": API_KEY,
        "mode": "driving"
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if data['status'] == 'OK' and data['rows'][0]['elements'][0]['status'] == 'OK':
        element = data['rows'][0]['elements'][0]
        travel_time_seconds = element.get('duration_in_traffic', element['duration'])['value']
        return travel_time_seconds // 60 
    else:
        return None

@app.post("/plan-trip")
def plan_trip(request: TripRequest):
    if API_KEY == "YOUR_API_KEY_HERE":
        raise HTTPException(status_code=500, detail="Google Maps API key not configured.")

    slots = generate_time_slots(hours_ahead=4)
    results = []

    for slot in slots:
        duration = get_travel_time(request.origin, request.destination, slot["timestamp"])
        if duration is not None:
            results.append({
                "time_slot": slot["readable_time"],
                "estimated_travel_time_mins": duration,
            })
            
    if not results:
        raise HTTPException(status_code=400, detail="Could not fetch route data. Check locations.")

    results.sort(key=lambda x: x["estimated_travel_time_mins"])

    best_time = results[0]["estimated_travel_time_mins"]
    for res in results:
        if res["estimated_travel_time_mins"] <= best_time + 5: 
            res["status"] = "BEST"
        elif res["estimated_travel_time_mins"] <= best_time + 15:
            res["status"] = "OK"
        else:
            res["status"] = "AVOID"

    return {"recommendations": results}