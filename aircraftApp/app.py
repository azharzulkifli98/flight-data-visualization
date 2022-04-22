import sqlite3
import streamlit as st
import pandas as pd
import plotly.express as px


# Database functions
conn = sqlite3.connect('mydata.db', check_same_thread=False)
c = conn.cursor()

def create_table():
    c.execute("CREATE TABLE IF NOT EXISTS flighttable(TailNumber TEXT, FlightDate DATE, FlightNumber INTEGER, LandingStatus INTEGER, FaultCode TEXT, Duration REAL)")

def clear_table():
    c.execute("DELETE FROM flighttable")

def add_from_csv(filename):
    df = pd.read_csv(filename)
    df.to_sql('flighttable', conn, if_exists='append', index=True)

def get_conditional_data(condition):
    c.execute("SELECT * FROM flighttable WHERE {}".format(condition))
    data = c.fetchall()
    return data

def get_all_data():
    c.execute("SELECT * FROM flighttable")
    data = c.fetchall()
    return data



# Graph and Chart functions
def get_timeline_graphs(mydata, attributes):
    st.header("Flights By Timeline")
    sorted_data = mydata.sort_values( by=['FlightDate', 'FlightNumber'] )
    sorted_attributes = ['FlightDate', 'FlightNumber', 'TailNumber', 'Duration', 'LandingStatus', 'FaultCode']
    sorted_data = sorted_data[sorted_attributes]


    st.subheader("Duration and Quantity vs Date")
    flights_per_day = sorted_data.groupby(['FlightDate']).max()['FlightNumber'].reset_index()
    duration_per_day = sorted_data.groupby(['FlightDate']).sum()['Duration'].reset_index()
    combined_data = flights_per_day.set_index('FlightDate').join(duration_per_day.set_index('FlightDate'))
    st.bar_chart(combined_data)
    st.write(combined_data)


    st.subheader("Flight Landing Statuses Per Day")
    status_per_day = px.bar(sorted_data, x=sorted_data['FlightDate'], color=sorted_data['LandingStatus'], title="Landing Status Timeline")
    st.plotly_chart(status_per_day)


    st.subheader("Flight Landing Statuses Chronologically")
    def color_arrange(s):
        color = { '0': 'gray', '1': 'white', '2': 'yellow', '3': 'red' }
        return f'background-color: {color[s]}'
    st.dataframe(sorted_data.style.applymap(color_arrange, subset=['LandingStatus']))


    st.subheader("Breakdown by Landing Status and Fault Code")

    status_code_breakdown = sorted_data['LandingStatus'].value_counts()
    p1 = px.pie(status_code_breakdown, names=['status 0', 'status 1', 'status 2', 'status 3'], values='LandingStatus')
    st.plotly_chart(p1, use_container_width=True)
    st.text(" 0 - no takeoff \n 1 - no issues \n 2 - minor issues during flight \n 3 - major issues during flight")

    fault_code_breakdown = sorted_data['FaultCode'].value_counts()
    fault_names = sorted_data['FaultCode'].unique()
    p2 = px.pie(fault_code_breakdown, names=fault_names, values='FaultCode')
    st.plotly_chart(p2, use_container_width=True)




def get_individual_graphs(mydata, attributes):
    st.header("Individual Aircraft Data")

    number_flights_by_plane = mydata['TailNumber'].value_counts()
    status_codes_per_day = mydata.groupby(['TailNumber']).sum()['Duration']
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Number of flights each aircarft has flown")
        st.bar_chart(number_flights_by_plane)
        st.write(number_flights_by_plane)
    with col2:
        st.subheader("Total duration flown by aircraft")
        st.bar_chart(status_codes_per_day)
        st.write(status_codes_per_day)

    st.subheader("Fault Codes Experienced By Aircraft Tail Number")
    plot = px.scatter(data_frame=mydata, x=mydata['FaultCode'], y=mydata['TailNumber'])
    st.plotly_chart(plot)
    st.subheader("Fault codes including duplicates")
    st.write(mydata[['TailNumber', 'FaultCode', 'FlightDate']].sort_values(by=['TailNumber']))


    st.subheader("Breakdown per Aircraft")
    choice = st.selectbox("TailNumber", mydata['TailNumber'].unique())
    tail_data = pd.DataFrame(get_conditional_data("tailNumber = '{}'".format(choice)), columns=attributes)
    tail_data['FaultCode'] = tail_data['FaultCode'].fillna("None")
    tail_data['FlightDate'] = pd.to_datetime(tail_data['FlightDate'])
    tail_data['LandingStatus'] = tail_data['LandingStatus'].astype(str)
    

    st.subheader("Percentage of landing statuses experienced")
    status_by_tailnumber = tail_data['LandingStatus'].value_counts()
    stats = px.pie(status_by_tailnumber, names=tail_data['LandingStatus'].unique(), values='LandingStatus')
    st.plotly_chart(stats, use_container_width=True)
    
    st.subheader("Percentage of fault codes experienced")
    code_by_tailnumber = tail_data['FaultCode'].value_counts()
    codes = px.pie(code_by_tailnumber, names=tail_data['FaultCode'].unique(), values='FaultCode')
    st.plotly_chart(codes, use_container_width=True)
    
    st.subheader("Flight Statuses Experienced Per Day")
    tail_status_per_day = px.bar(tail_data, x=tail_data['FlightDate'], color=tail_data['LandingStatus'], title="Landing Status Timeline")
    st.plotly_chart(tail_status_per_day)



# Initialization functions
def get_upload_data(attributes):
    st.subheader("Select a csv file from your local machine:")
    uploaded_data = st.file_uploader("Get Flight data", type='csv')

    # performs data checking to ensure it fits the db
    if uploaded_data is not None:
        new_data = pd.read_csv(uploaded_data)
        if set(attributes).issubset(new_data.columns):
            clear_table()
            new_data.to_sql('flighttable', conn, if_exists='replace', index=False)
            st.subheader("Data successfully added!")
        else:
            st.subheader("Incorrect format, please select a different file")


def main():
    create_table()
    attributes = ['TailNumber', 'FlightDate', 'FlightNumber', 'LandingStatus', 'FaultCode', 'Duration']
    mydata = pd.DataFrame(get_all_data(), columns=attributes)
    mydata['FlightDate'] = pd.to_datetime(mydata['FlightDate'])
    mydata['LandingStatus'] = mydata['LandingStatus'].astype(str)
    mydata['FaultCode'] = mydata['FaultCode'].fillna("None")

    st.title("Flight Data Visualizer")
    st.subheader("View graphs and tables about current aircraft flights")
    choice = st.selectbox("Topic", ['timelines', 'individual', 'upload'])

    if choice == 'timelines':
        get_timeline_graphs(mydata, attributes)
    
    elif choice == 'individual':
        get_individual_graphs(mydata, attributes)
    
    else:
        get_upload_data(attributes)
    
    if st.checkbox("View raw data"):
        st.write(mydata)
    
    c.close()
    conn.close()


if __name__ == '__main__':
    main()