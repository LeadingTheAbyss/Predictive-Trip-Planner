from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
import math

from sqlalchemy.orm import Session
from database import SessionLocal, TripLog

app = FastAPI(title = "When-To-Go API")

app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"], 
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

class TripRequest(BaseModel):
    origin: str
    destination: str

def generate_time_slots(hours_ahead=4, interval_mins=30):
    slots = []
    now = datetime.now()
    discard_minutes = now.minute % interval_mins
    next_slot = now + timedelta(minutes=(interval_mins - discard_minutes))
    
    for i in range(math.ceil((hours_ahead * 60) / interval_mins)):
        target_time = next_slot + timedelta(minutes = interval_mins * i)
        slots.append({
            "readable_time": target_time.strftime("%I:%M %p"),
            "dt_object": target_time 
        })
    return slots

def get_mock_travel_time(origin: str, destination: str, dt_object: datetime):
    base_time = len(origin) + len(destination) + 15 
    hour = dt_object.hour
    if hour in [8, 9, 17, 18, 19]:
        return base_time + 25 
    return base_time

def get_heuristic_crowd_score(dt_object: datetime):
    score = 2 
    hour = dt_object.hour
    if dt_object.weekday() >= 5:
        score += 3
    if 18 <= hour <= 21: 
        score += 4
    elif 12 <= hour <= 17: 
        score += 2
    return min(score, 10) 

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/plan-trip")
def plan_trip(request: TripRequest, db: Session = Depends(get_db)): 
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
    
    best_slot = results[0]

    db_log = TripLog(
        origin = request.origin,
        destination = request.destination,
        recommended_time_slot = best_slot["time_slot"],
        predicted_travel_time = best_slot["estimated_travel_time_mins"],
        heuristic_crowd_score = best_slot["crowd_level"],
        penalty_score = best_slot["penalty_score"]
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log) 

    best_score = best_slot["penalty_score"]
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

    return {
        "trip_id": db_log.id, 
        "recommendations": results
    }