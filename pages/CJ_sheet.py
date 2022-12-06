import streamlit as st 

from datetime import date, timedelta

today = date.today()

# Get the day of the week (1-7, where 1 is Monday and 7 is Sunday)
day_of_week = today.isoweekday()

# Calculate the starting and ending dates of the week
start_of_week = today - timedelta(days=day_of_week - 1)
end_of_week = today + timedelta(days=7 - day_of_week)

# Print the starting and ending dates
this_week = "{}-{}".format(start_of_week.strftime("%b%d"), end_of_week.strftime("%b%d"))
st.write(this_week)

next_week = today + timedelta(days=7)

# Get the day of the week (1-7, where 1 is Monday and 7 is Sunday)
day_of_week = next_week.isoweekday()

# Calculate the starting and ending dates of the week
start_of_week = next_week - timedelta(days=day_of_week - 1)
end_of_week = next_week + timedelta(days=7 - day_of_week)

# Print the starting and ending dates
next_week = "{}-{}".format(start_of_week.strftime("%b%d"), end_of_week.strftime("%b%d"))
st.write(next_week)


