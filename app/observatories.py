"""Ground-based observatory registry for the Multi mission obsevation planner.

These are illustrative site coordinates, not mission scheduling interfaces.
Space observatories require orbit/attitude/visibility constraints and are not
modeled by this ground-based AltAz implementation.
"""
from astropy.coordinates import EarthLocation
import astropy.units as u

#observatory information is saved as key-value pairs in a dictionary. eg: Kitt Peak is the key. location and description are the values. 
# Dictionary containing all the observatory information. 
OBSERVATORIES = {
    "Kitt Peak": {
        "location": EarthLocation.from_geodetic(
            lon=-111.6003 * u.deg, lat=31.9583 * u.deg, height=2096 * u.m
        ),
        "description": "Ground-based observatory site in Arizona, USA",
    },
    "Cerro Tololo": {
        "location": EarthLocation.from_geodetic(
            lon=-70.8065 * u.deg, lat=-30.1690 * u.deg, height=2200 * u.m
        ),
        "description": "Ground-based observatory site in Chile",
    },
    "Roque de los Muchachos": {
        "location": EarthLocation.from_geodetic(
            lon=-17.8890 * u.deg, lat=28.7606 * u.deg, height=2326 * u.m
        ),
        "description": "Ground-based observatory site on La Palma, Spain",
    },
}


def list_observatories():
    return [
        {"name": name, "description": info["description"]}
        for name, info in OBSERVATORIES.items()
    ]

#OBSERVATORIES.items returns the key and value together. In the for loop we call the key 'name' and the value 'info'. The value is also a dictionary,
# so we can access the description using info["description"]. The function returns a list of dictionaries, each containing the name and description
# of an observatory.

#eg: [
#    {
#        "name": "Kitt Peak",
#        "description": "Ground-based observatory site in Arizona, USA"
#    },
#    {
#        "name": "Cerro Tololo",
#        "description": "Ground-based observatory site in Chile"
#    },
#    {
#        "name": "Roque de los Muchachos",
#        "description": "Ground-based observatory site on La Palma, Spain"
#    }
#]