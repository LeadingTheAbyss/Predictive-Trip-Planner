from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import math

app = FastAPI(title="When-To-Go API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TripRequest(BaseModel):
    origin: str
    destination: str

def generate_time_slots(hours_ahead=4, interval_mins=30):
    """Generates future time slots as datetime objects."""
    slots = []
    now = datetime.now()
    discard_minutes = now.minute % interval_mins
    next_slot = now + timedelta(minutes=(interval_mins - discard_minutes))
    
    for i in range(math.ceil((hours_ahead * 60) / interval_mins)):
        target_time = next_slot + timedelta(minutes=interval_mins * i)
        slots.append({
            "readable_time": target_time.strftime("%I:%M %p"),
            "dt_object": target_time 
        })
    return slots

def get_mock_travel_time(origin: str, destination: str, dt_object: datetime):
    """Simulates travel time based on length of text and rush hours."""
    base_time = len(origin) + len(destination) + 15 
    
    hour = dt_object.hour
    # Rush hour penalty (8-10 AM, 5-7 PM)
    if hour in [8, 9, 17, 18, 19]:
        return base_time + 25 
    return base_time

def get_heuristic_crowd_score(dt_object: datetime):
    """Returns a simulated crowd score from 1 (empty) to 10 (packed)."""
    score = 2 
    hour = dt_object.hour
    
    # Weekend penalty
    if dt_object.weekday() >= 5:
        score += 3
        
    # Time of day penalty
    if 18 <= hour <= 21: 
        score += 4
    elif 12 <= hour <= 17: 
        score += 2
        
    return min(score, 10) 

@app.post("/plan-trip")
def plan_trip(request: TripRequest):
    slots = generate_time_slots(hours_ahead=4)
    results = []
    
    ALPHA = 3 

    for slot in slots:
        travel_time = get_mock_travel_time(request.origin, request.destination, slot["dt_object"])
        crowd_score = get_heuristic_crowd_score(slot["dt_object"])
        
        total_penalty_score = travel_time + (ALPHA * crowd_score)

        results.append({
            "time_slot": slot["readable_time"],
            "estimated_travel_time_mins": travel_time,
            "crowd_level": crowd_score,
            "penalty_score": total_penalty_score
        })

    results.sort(key=lambda x: x["penalty_score"])

    best_score = results[0]["penalty_score"]
    for res in results:
        if res["penalty_score"] <= best_score + 10: 
            res["status"] = "BEST"
            res["insight"] = "Optimal balance of low traffic and fewer crowds."
        elif res["penalty_score"] <= best_score + 25:
            res["status"] = "OK"
            res["insight"] = "Expect moderate delays or heavier foot traffic."
        else:
            res["status"] = "AVOID"
            res["insight"] = "Peak congestion. Leaving now is highly inefficient."

    return {"recommendations": results}