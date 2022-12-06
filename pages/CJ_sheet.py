import streamlit as st 

from datetime import date, timedelta

today = date.today()

# Get the year, week number, and day of the week
year, week_number, day_of_week = today.isocalendar()

# Calculate the starting date of the week (Monday)
starting_date = today - timedelta(days=day_of_week-1)

# Calculate the ending date of the week (Sunday)
ending_date = starting_date + timedelta(days=6)

st.write(f"Week starting: {starting_date.strftime('%B %d, %Y')}")
st.write(f"Week ending: {ending_date.strftime('%B %d, %Y')}")

