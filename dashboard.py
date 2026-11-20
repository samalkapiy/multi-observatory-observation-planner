import requests
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import timedelta, datetime

# --------------------------------------------------
# Page configuration
# --------------------------------------------------

st.set_page_config(
    page_title="Astronomical Observation Planner",
    page_icon="🔭",
    layout="wide",
)

st.title("🔭 Multi-Observatory Astronomical Observation Planner")
st.write(
    "Explore target visibility across multiple ground-based observatories."
)

# Your FastAPI application must be running.
#API_URL = st.sidebar.text_input(
#    "FastAPI address",
#    value="http://127.0.0.1:8000",
#)
#Note: The above was commented out because we are using a two terminal setup due to incompatibility between Streamlit and FastAPI. The FastAPI backend must be running in a separate terminal, and the Streamlit frontend must be running in another terminal. The API_URL is hardcoded to "http://127.0.0.1:8000"

# --------------------------------------------------
# FastAPI backend connection
# --------------------------------------------------

API_URL = "http://127.0.0.1:8000"

st.sidebar.header("Backend connection")

try:
    response = requests.get(
        f"{API_URL}/health",
        timeout=5,
    )

    response.raise_for_status()

    st.sidebar.success("FastAPI connected")

except requests.exceptions.RequestException:
    st.sidebar.error("FastAPI is offline. Start the backend.")


# --------------------------------------------------
# Input form
# --------------------------------------------------

st.header("Observation parameters")

with st.form("observation_form"):

    col1, col2 = st.columns(2)

    with col1:
        event_name = st.text_input(
            "Event name",
            value="Example transient",
        )

        ra_deg = st.number_input(
            "Right Ascension (degrees)",
            min_value=0.0,
            max_value=359.999,
            value=83.63,
        )

        dec_deg = st.number_input(
            "Declination (degrees)",
            min_value=-90.0,
            max_value=90.0,
            value=22.01,
        )

        start_time = st.text_input(
            "Start time (UTC)",
            value="2026-11-05T00:00:00",
        )

    with col2:
        duration_hours = st.number_input(
            "Observation duration (hours)",
            min_value=1.0,
            max_value=72.0,
            value=12.0,
        )

        cadence_minutes = st.number_input(
            "Sampling cadence (minutes)",
            min_value=1,
            max_value=60,
            value=10,
        )

        min_altitude_deg = st.slider(
            "Minimum target altitude (degrees)",
            min_value=0,
            max_value=90,
            value=25,
        )

        require_darkness = st.checkbox(
            "Require astronomical darkness",
            value=True,
        )

    submitted = st.form_submit_button(
        "Generate observation plan",
        type="primary",
    )

# --------------------------------------------------
# Submit request to FastAPI and obtain an observation from FASTAPI
# --------------------------------------------------

if submitted:                                                               #returns a boolean variable, True or False. 
                                                                            #once the user hits submit, the data is added onto a dictionary called 'request_data'. This dictionary is then sent to the FastAPI backend for processing. The backend will return a JSON response containing the observation plan, which is then displayed in the Streamlit frontend.
    request_data = {
        "event_name": event_name,
        "ra_deg": ra_deg,
        "dec_deg": dec_deg,
        "start_time": start_time,
        "duration_hours": duration_hours,
        "cadence_minutes": cadence_minutes,
        "min_altitude_deg": min_altitude_deg,
        "require_astronomical_darkness": require_darkness,
    }

    try:                                                                    #try block allows python to execute a block of code that might fail. Failing can happen due to many reasons. eg: FASTAPI not running, API received invalid input, etc.
        with st.spinner("Calculating observatory visibility..."):           #so rather than allowing the application to crash, we use exception handling to display a meaningful error message. 

            response = requests.post(                                       #The requests library allows Python applications to communicate with web servers using HTTP requests.Two methods are GET(retreieve information from a server), POST(send information to a server for processing)
                f"{API_URL}/plan",                                          #specifies the API endpoint. eg: http://127.0.0.1:8000/plan
                json=request_data,                                          #converts python dictionary to a JSON format. 
                timeout=60,                                                 #Streamlit will wait up to 60 seconds for the request to complete.
            )

            response.raise_for_status()                                     #Check whether the API request was successful. HTTP status: 200-successful request,400-	Bad request, 404-Endpoint not found, 422-	Input validation error, 500-Internal server error
            plan = response.json()                                          #Convert the JSON response into a Python dictionary

        st.session_state["plan"] = plan                                     #allows Streamlit to preserve information between application reruns.Streamlit reruns your Python script when users interact with widgets.Without session state, the returned observation plan could be lost during a subsequent reruns

    except requests.exceptions.ConnectionError:
        st.error(
            "Could not connect to FastAPI. "
            "Make sure your API server is running."
        )

    except requests.exceptions.HTTPError:
        st.error(f"API error: {response.text}")

    except requests.exceptions.RequestException as error:
        st.error(f"Request failed: {error}")

# --------------------------------------------------
# Display results
# --------------------------------------------------

if "plan" in st.session_state:                                                  #checking is the 'plan' exists in the session state

    plan = st.session_state["plan"]                                             #This retrieves the observation plan stored in session state and assigns it to a variable called plan.
    results = plan["results"]                                                   # you can retreive the information using, plan['target'], plan['search'], plan['results']. target, search and results are the 3 keys in the dictionary returned by the FastAPI backend.

    st.divider()                                                                #divider to separate the input form from the results section
    st.header(f"Results: {plan['target'].get('event_name', 'Target')}")

    # Target information
    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Right Ascension",
        f"{plan['target']['ra_deg']:.3f}°",
    )

    col2.metric(
        "Declination",
        f"{plan['target']['dec_deg']:.3f}°",
    )

    col3.metric(
        "Observation duration",
        f"{plan['search']['duration_hours']} hours",
    )

    # --------------------------------------------------
    # Observatory comparison
    # --------------------------------------------------

    st.subheader("Observatory comparison")
    st.write("Shows the maximum altitude the target will be based on the different observatory locations, how many 10 min sample slots will be visibile and which observatory will be able to observe the target.")

    comparison_data = []

    for result in results:                                                      # to get an idea about the keys in the 'result' dictionary, check planner.py code
        comparison_data.append({
            "Observatory": result["observatory"],
            "Maximum altitude (degrees)": result["max_altitude_deg"],
            "Visible samples": result["visible_sample_count"],
            "Observable": (
                "Yes" if result["observable"] else "No"
            ),
        })

    comparison_df = pd.DataFrame(comparison_data)                               #convert the list into a pandas dataframe

    col1, col2 = st.columns(2)

    with col1:
        st.dataframe(
            comparison_df,                                                      #shows the comparison dataframe in an interactive table format. 
            use_container_width=True,                                           #This tells Streamlit to expand the table to use the available width of its column
            hide_index=True,                                                    #hide the indices of the dataframe
        )

    with col2:
        altitude_fig = px.bar(                                                  #creates a bar plot
            comparison_df,
            x="Observatory",                                                    #slects the x-axis values from the "Observatory" column of the dataframe
            y="Maximum altitude (degrees)",
            color="Observatory",  
            color_discrete_map={
                "Kitt Peak": "#8B008B",
                "Cerro Tololo": "#1E90FF",
                "Roque de los Muchachos": "#008B8B",
            },
            title="Maximum target altitude by observatory",
            labels={
                "Maximum altitude (degrees)": "Altitude (degrees)"
            },
        )

        altitude_fig.update_layout(
            yaxis_range=[0, 90],
            xaxis_title="Observatory",
            yaxis_title="Maximum altitude (degrees)",
        )

        st.plotly_chart(                                                        #displays the chart in the dashboard.
            altitude_fig,
            use_container_width=True,
        )

    # --------------------------------------------------
    # Visibility timeline
    # --------------------------------------------------

    st.subheader("Visibility windows")
    st.markdown("""
    Visibility windows are calculated by first validating the user-provided inputs, including the target's Right Ascension (RA), Declination (Dec),
    observation start time, duration, and sampling cadence. The backend then generates a time grid based on the requested observation period and cadence.
            
    For each observatory, the target's and the Sun's altitudes are calculated at every time sample to determine when and where the target is observable.
    
    When astronomical darkness is required, as is typically the case for optical observations, two conditions must be satisfied: 
    - The target's altitude must be above the specified minimum altitude.
    - The Sun must be below -18 degrees. 
        
    The backend uses these conditions to identify visibility windows and calculate the number of visible samples for each observatory. 
    Finally, the results are returned through the FastAPI backend and displayed in the Streamlit dashboard.
            """)
    
    start_time = datetime.fromisoformat(start_time)
    end_time = start_time + timedelta(hours=duration_hours) #newline. calculating the end time based on the user start time and duration hours
    window_data = []

    for result in results:

        for window in result["visibility_windows"]:                         #visibility_windows dictionary has the following keys: start_utc, end_utc, sample_count.

            window_data.append({                                            #appending the start_utc, emd_etc, sample count onto the window_data list
                "Observatory": result["observatory"],
                "Start": pd.to_datetime(
                    window["start_utc"]
                ),
                "End": pd.to_datetime(
                    window["end_utc"]
                ),
                "Samples": window["sample_count"],
            })

    if window_data:                                                         #is window_data=True

        windows_df = pd.DataFrame(window_data)                              #convert the list into a dataframe

        timeline_fig = px.timeline(                                         #creates a timeline chart
            windows_df,
            x_start="Start",                                                #start at the "Start"
            x_end="End",                                                    #end at the "End"
            y="Observatory",                                                #Display each observatory on the y-axis
            color="Observatory",                                            #assigns different colors to each observaotry
            color_discrete_map={
                "Kitt Peak": "#8B008B",
                "Cerro Tololo": "#1E90FF",
                "Roque de los Muchachos": "#008B8B",
    },
            
            hover_data=["Samples"],                                         #when the cursor hovers over the plot, plotly shows the number of samples in that window
            title="Target visibility timeline (UTC)",
        )

        timeline_fig.update_yaxes(                                          #changing the vertical(y) axis ordering. 
            autorange="reversed"
        )
            
        # Set the x-axis range                                              #newline. Added a new x axes range. start= user defined start time. end = user defined end time (start time+observation_duraiton)
        timeline_fig.update_xaxes(
            range=[start_time, end_time]
        )

        # Vertical line showing user-defined observation start time            #newline
        timeline_fig.add_vline(
            x=start_time,
            line_dash="dash",
            line_color="green",
            line_width=2,
            annotation_text="Requested start time",
            annotation_position="top"
            )

        # Vertical line showing user-defined observation end time              #newline
        timeline_fig.add_vline(
            x=end_time,
            line_dash="dash",
            line_color="red",
            line_width=2,
            annotation_text="Requested observation end time",
            annotation_position="top"
            )



        timeline_fig.update_layout(
            xaxis_title="Time (UTC)",
            yaxis_title="Observatory",
        )

        st.plotly_chart(                                                    #displays the timeline figure on the dashboard
            timeline_fig,
            use_container_width=True,                                       #use the full width of the layout
        )

        #st.caption(
        #    "Timeline boundaries are approximate because visibility "      #display a explanatory note
        #    "is evaluated at the selected sampling cadence."
        #)

        st.subheader("Detailed visibility windows")

        st.dataframe(
            windows_df,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.warning(
            "No visibility windows were found for the selected "
            "time range and constraints."
        )


    #
    # Altitude Plots: For target, Sun and Moon
    #

    st.subheader("Altitude Plots")
    st.markdown("""
    The altitude plots show how the altitudes of the Target, Sun and the Moon changes over the observation period at different Observatory locations. 
"""
    )

    observatory_colors = {
        "Kitt Peak": "#8B008B",
        "Cerro Tololo": "#1E90FF",
        "Roque de los Muchachos": "#008B8B",
    }

    for result in results:

        # Retrieve the observatory name
        observatory = result["observatory"]

        # Create a dataframe for the current observatory
        altitude_df = pd.DataFrame({
            "Times": pd.to_datetime(result["Times"]),
            "Sun's altitude": result["sun_altitude"],
            "Moon's altitude": result["moon_altitude"],
            "Target's altitude": result["target_altitude"],
        })

        # Create the altitude plot
        altitude_fig = px.line(
            altitude_df,
            x="Times",
            y=["Sun's altitude", "Target's altitude", "Moon's altitude"],
            title=f"Sun, Moon and the Target Altitudes - {observatory}",
            labels={
                "Times": "Time (UTC)",
                "value": "Altitude (degrees)",
                "variable": "Object",
            },
            color_discrete_map={
                "Sun's altitude": "#FFA500",
                "Target's altitude": observatory_colors.get(
                    observatory, "#8B008B"
                ),
            },
        )

    # Configure plot layout
        altitude_fig.update_layout(
            yaxis_range=[0, 90],
            xaxis_title="Time (UTC)",
            yaxis_title="Altitude (degrees)",
            legend_title="Object",
            hovermode="x unified",
        )

        # Display the plot
        st.plotly_chart(
            altitude_fig,
            use_container_width=True,
        )

    # --------------------------------------------------
    # Scientific limitations
    # --------------------------------------------------

    with st.expander("Model limitations"):
        for limitation in plan.get("limitations", []):
            st.write(f"- {limitation}")

    # --------------------------------------------------
    # Raw API response
    # --------------------------------------------------

    with st.expander("View raw API response (JSON)"):
        st.json(plan)


