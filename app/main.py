"""FastAPI application for the observation planner."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from fastapi.responses import RedirectResponse

from .observatories import list_observatories  # python is importing from the same package
from .planner import plan_observations

###
#Main application file that uses FastAPI to create a web API which allows a user to submit astronomical event coordinates (Right Ascension and Declination),
#specify an observation window, and receive a schedule showing when the target is observable from different observatories.
###

#creating an instance of the FastAPI application with metadata such as title, description, and version.
app = FastAPI(
    title="Multi-Observatory Astronomical Observation Planner",
    description=(
        "A portfolio MVP that estimates target visibility at several "
        "ground-based observatory sites."
    ),
    version="0.1.0",
)

# creates a class. This describes the information that a user need to provide when they want to create a plan for observing an astronomical event.
#BaseModel comes from Pydantic. By inheriting from BaseModel, your class automatically gets:
#1. Data validation.
#2. Type checking.
#3. Error reporting.
#4. Data conversion where appropriate.
class PlanningRequest(BaseModel):
    event_name: str = Field(default="Unspecified transient", max_length=120)
    ra_deg: float = Field(ge=0, lt=360, description="Right ascension in degrees")
    dec_deg: float = Field(ge=-90, le=90, description="Declination in degrees")
    start_time: str = Field(description="UTC ISO timestamp, e.g. 2026-11-05T00:00:00")
    duration_hours: float = Field(default=12, gt=0, le=72)
    cadence_minutes: int = Field(default=10, ge=1, le=60)  #This determines how frequently the planner evaluates the target's visibility.
    min_altitude_deg: float = Field(default=25, ge=0, le=90)
    require_astronomical_darkness: bool = True


# Creating API endpoints using FastAPI decorators. Each endpoint corresponds to a specific URL path and HTTP method (GET or POST). 
# The functions defined under these decorators handle incoming requests and return responses.
#@app.get("/")                                                                       #creates a GET endpoint at the root URL ("/"). When a user accesses this URL, the root() function is called, returning a JSON response with project information.
#def root():                                                                         # this is simply a welcome page in JSON format
#    return {
#        "project": "Multi-Observatory Astronomical Observation Planner",
#        "version": "0.1.0",
#        "docs": "/docs",
#    }

# I want to direct the webserver to the API documentation page diretly. 
@app.get("/")
def root():
    return RedirectResponse(url="/docs")

#checks whether the app is running and healthy. Imagine deploying your application to AWS. A monitoring system can periodically call /health 
# to check whether the application is responding.
@app.get("/health")
def health():
    return {"status": "ok"}

#lists the observatories available in the project
@app.get("/observatories")
def observatories():
    return {"observatories": list_observatories()}

#main functionality of the project. 
@app.post("/plan")
def create_plan(request: PlanningRequest):  # requires the submitted data to follow the structure we defined earlier. Takes in the request from the user through the PlanningRequest model. FastAPI automatically validates the incoming request against the PlanningRequest model.
    try:
        result = plan_observations(    # plan_observation is a function from planner.py that takes the user input and calculates when the target is observable from different observatories.
            ra_deg=request.ra_deg,
            dec_deg=request.dec_deg,
            start_time=request.start_time,
            duration_hours=request.duration_hours,
            cadence_minutes=request.cadence_minutes,
            min_altitude_deg=request.min_altitude_deg,
            require_astronomical_darkness=request.require_astronomical_darkness,
        )
        result["target"]["event_name"] = request.event_name     # adds the event name to the result dictionary before returning it to the user.
        return result                                           #FastAPI automatically converts Python dictionaries into JSON responses.
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
