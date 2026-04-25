from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

# format: postgresql://<username>:<password>@localhost:5432/<database_name>
# Change "yourpassword" to whatever you set when installing Postgres!
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Kartikey.singh62@localhost:5432/when_to_go_db"

# Notice the connect_args is GONE. Postgres handles its own threads!
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TripLog(Base):
    __tablename__ = "trip_logs"

    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    
    recommended_time_slot = Column(String)
    predicted_travel_time = Column(Integer)
    heuristic_crowd_score = Column(Integer)
    penalty_score = Column(Float)
    
    actual_crowd_level = Column(Integer, nullable=True) 

Base.metadata.create_all(bind=engine)