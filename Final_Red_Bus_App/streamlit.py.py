import streamlit as st
import mysql.connector
import pandas as pd
from datetime import time

# Connect to MySQL database
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="bus_details"
    )

# Fetch unique states
def fetch_states(connection):
    query = "SELECT DISTINCT State FROM bus_info ORDER BY State"
    cursor = connection.cursor()
    cursor.execute(query)
    states = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return states

# Fetch routes based on selected state
def fetch_routes(connection, state):
    query = "SELECT DISTINCT Route_Name FROM bus_info WHERE State = %s ORDER BY Route_Name"
    cursor = connection.cursor()
    cursor.execute(query, (state,))
    routes = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return routes

# Fetch available bus types based on state and route
def fetch_bus_types(connection, route_name, state):
    query = "SELECT DISTINCT Bus_Type FROM bus_info WHERE Route_Name = %s AND State = %s ORDER BY Bus_Type"
    cursor = connection.cursor()
    cursor.execute(query, (route_name, state))
    bus_types = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return bus_types

# Fetch available departing times based on state and route
def fetch_departure_times(connection, route_name, state):
    query = "SELECT DISTINCT Departing_Time FROM bus_info WHERE Route_Name = %s AND State = %s ORDER BY Departing_Time"
    cursor = connection.cursor()
    cursor.execute(query, (route_name, state))
    departure_times = [row[0] for row in cursor.fetchall()]
    cursor.close()
    return departure_times

# Fetch bus details based on filters
def fetch_data(connection, route_name, state, price_sort_order, min_price, max_price, departing_time, min_star_rating, bus_types):
    price_sort_order_sql = "ASC" if price_sort_order == "Low to High" else "DESC"
    
    query = """
        SELECT * FROM bus_info 
        WHERE Route_Name = %s 
        AND State = %s 
        AND Price BETWEEN %s AND %s 
        AND Departing_Time >= %s 
        AND Star_Rating >= %s 
        AND Bus_Type IN ({})
        ORDER BY Star_Rating DESC, Price {}
    """.format(', '.join(['%s'] * len(bus_types)), price_sort_order_sql)

    params = [route_name, state, min_price, max_price, departing_time, min_star_rating] + bus_types
    df = pd.read_sql(query, connection, params=params)
    
    return df

# Main Streamlit app
def main():
    st.title('🚌 Easy and Secure Online Bus Ticket Booking')

    # Connect to MySQL
    connection = get_connection()
    try:
        # Fetch states
        states = fetch_states(connection)
        state = st.sidebar.selectbox('🌍 Select State', states)

        # Fetch routes based on selected state
        routes = fetch_routes(connection, state)
        route_name = st.sidebar.selectbox('📍 Select Route', routes)

        # Fetch available bus types for the selected state & route
        available_bus_types = fetch_bus_types(connection, route_name, state)

        # Fetch available departing times for the selected state & route
        available_departure_times = fetch_departure_times(connection, route_name, state)

        # Sidebar - Departure Time (Only show available times)
        if available_departure_times:
            departing_time = st.sidebar.selectbox('⏰ Select Departing Time', available_departure_times)
        else:
            departing_time = "00:00"

        # Sidebar - Price Sorting
        price_sort_order = st.sidebar.selectbox('💲 Sort by Price', ['Low to High', 'High to Low'])

        # Sidebar - Price Range
        min_price, max_price = st.sidebar.slider('💵 Select Price Range', 0, 5000, (500, 3000))

        # Sidebar - Star Rating
        min_star_rating = st.sidebar.selectbox('⭐ Minimum Star Rating', options=[1, 2, 3, 4, 5], index=0)

        # Sidebar - Bus Type Filter (Only show available bus types)
        if available_bus_types:
            bus_types = st.sidebar.multiselect('🚌 Filter by Bus Type', available_bus_types, default=available_bus_types)
        else:
            bus_types = []

        # Fetch data based on filters
        if bus_types:
            data = fetch_data(connection, route_name, state, price_sort_order, min_price, max_price, departing_time, min_star_rating, bus_types)

            if not data.empty:
                st.subheader("🎯 Bus Details")
                st.dataframe(data)
            else:
                st.warning("No buses match the selected filters.")
        else:
            st.warning("No available bus types for this route.")
    finally:
        connection.close()

if __name__ == '__main__':
    main()
