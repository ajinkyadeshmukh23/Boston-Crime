'''
CS 602 Summer 2020 Program 5

@author:  Ajinkya Deshmukh
'''
import pandas as pd
import numpy as np
import streamlit as st
import pydeck as pdk
import mapbox as mb
import datetime
import altair as alt
import matplotlib.pyplot as plt
plt.style.use('ggplot')

MAPKEY = "pk.eyJ1IjoiY2hlY2ttYXJrIiwiYSI6ImNrOTI0NzU3YTA0azYzZ21rZHRtM2tuYTcifQ.6aQ9nlBpGbomhySWPF98DApk.eyJ1IjoiY2hlY2ttYXJrIiwiYSI6ImNrOTI0NzU3YTA0azYzZ21rZHRtM2tuYTcifQ.6aQ9nlBpGbomhySWPF98DA"

def read_data():   #Read data from csv file and store it as pandas DataFrame/Dictionary
    datafile = "BostonCrime2020Sample.csv"                      #Primary dataset file 
    df = pd.read_csv(datafile)
    df = df.rename(columns={'Lat': 'lat', 'Long': 'lon'})       #columns renamed to Map defaults
    df['OCCURRED_ON_DATE'] = pd.to_datetime(df['OCCURRED_ON_DATE'])         #column type changed to datetime format
    df['SHOOTING'] = df['SHOOTING'].apply(str)
    d = {'1' : "Yes", '0' :'No'}                                
    df['SHOOTING'] = df['SHOOTING'].map(d).fillna(df['SHOOTING'])           #Binary values changed to Yes/No strings
    datafile2 = "BostonDistricts.csv"                                       #Secondary datafile read for district names
    dfdist = pd.read_csv(datafile2)
    dfdist['DISTRICT_NAME'] = dfdist['DISTRICT_NAME'].str.upper()           #district names changed to uppercase (for keyword search)
    distdic = pd.Series(dfdist.DISTRICT_NAME.values,index=dfdist.DISTRICT_NUMBER).to_dict()     
    df['DISTRICT'] = df['DISTRICT'].map(distdic).fillna(df['DISTRICT'])
    dm = {1: '1. January', 2: '2. February', 3: '3. March', 4: '4. April', 5: '5. May',
                6: '6. June', 7: '7. July'}
    df['MONTH'] = df['MONTH'].map(dm).fillna(df['MONTH'])                   #datafile 2 converted to dictionary and values mapped with the ones in datafle 1
    return df, distdic




def mapper(df):                                 #function to create a map based on dataframe

    view_state = pdk.ViewState(                 #setting the initial view of the map using mean of coordinates and setting zoom for the same
        latitude=df["lat"].mean(),
        longitude=df["lon"].mean(),
        zoom=11,
        pitch=0)

    layer1 = pdk.Layer('ScatterplotLayer',                  #plotting all the coordinates from the lat, lon columns
                      data=df,
                      get_position='[lon, lat]',
                      get_radius=100,
                      get_color=[0, 128, 200],
                      pickable=True
                      )
    
    tool_tip = {"html": "Incident No.:<br/> <b>{INCIDENT_NUMBER}</b> ",         #layer that appears on hovering over the coordinates
                "style": { "backgroundColor": "grey",
                            "color": "white"}
              }
    
    map = pdk.Deck(                                                             #combining elements together on a single deck
        map_style='mapbox://styles/mapbox/light-v9',
        initial_view_state=view_state,
        mapbox_key=MAPKEY,
        layers=[layer1],
        tooltip= tool_tip
    )
    st.pydeck_chart(map)                                                        #creating a map based on all the elements

def filter():                                               #Function for using different filters to get desired results
    
    df, distd = read_data()                                 #retrieving data from read_data function
    distdic = [*distd.values()]
    st.sidebar.text('')
    if st.sidebar.checkbox('Select date range'):            #Date range filter
        st.sidebar.text('^Uncheck for all results')
        from_date = st.sidebar.date_input("From", datetime.date(2020,1,1))
        to_date = st.sidebar.date_input("To", datetime.date(2020,4,1))
        df = df.loc[(df['OCCURRED_ON_DATE'] >= from_date) & (df['OCCURRED_ON_DATE'] <= to_date)]
    district = distdic
    if st.sidebar.checkbox('Shooting involved'):                    #Shooting involved filter
        status = st.sidebar.radio("^Uncheck for all results",("Yes","No"))
        if status == "Yes":
            df = df.loc[df['SHOOTING'] == 'Yes']
        else:
            df = df.loc[df['SHOOTING'] == 'No'] 
        
    if st.sidebar.checkbox("Select District(s)"):                   #district Filter
        st.sidebar.text('^Uncheck for all results')
        district = st.sidebar.multiselect("Select District", (distdic), default = ['ROXBURY'])
    df = df.loc[df['DISTRICT'].isin(district)]
    df = df.reset_index()
    df = df.drop(['Unnamed: 0','index', 'Location', 'HOUR', 'MONTH', 'YEAR', 'DAY_OF_WEEK','REPORTING_AREA'], axis =1 )     #dropping the columns not required to show in the dataframe
    rowcount = len(df.index)
    st.text(f'{rowcount} results fetched')
    if rowcount == 0:                                                           #Showing results based on the filtered data
        st.error("Please select at least 1 District from the Sidebar")
    else:
        if st.checkbox("Show results in DataFrame"):
            st.dataframe(df)
            if st.checkbox("View incident Info"):
                inci = st.text_input("Enter Incident Number")
                infor(inci)
        if st.checkbox("Show results on map"):
            st.text('MAP')
            mapper(df)

def keyw(key):                                              #Function to get results based on a keyword search
    df , distd = read_data()
    distdic = [*distd.values()]
    df = df[df['OFFENSE_DESCRIPTION'].str.contains(key) | df['STREET'].str.contains(key) | df['DISTRICT'].str.contains(key)]        #selecting columns for keyword search and obtaining rows in df if the columns contains the keyword
    if st.sidebar.checkbox("Add Filter"):                                                           #further adding filters to narrow the search
        if st.sidebar.checkbox('Select Date Range'):                                    #Date Range filter
            st.sidebar.text('Uncheck for all results')
            from_date = st.sidebar.date_input("From", datetime.date(2020,1,1))
            to_date = st.sidebar.date_input("To", datetime.date(2020,4,1))
            df = df.loc[(df['OCCURRED_ON_DATE'] >= from_date) & (df['OCCURRED_ON_DATE'] <= to_date)]
        district = distdic
        if st.sidebar.checkbox('Shooting Involved'):                                    #shooting involved Filter
            status = st.sidebar.radio("Uncheck for all results",("Yes","No"))
            if status == "Yes":
                df = df.loc[df['SHOOTING'] == 'Yes']
            else:
                df = df.loc[df['SHOOTING'] == 'No'] 
            
        if st.sidebar.checkbox("Select District(s)"):                                   #District filter
            district = st.sidebar.multiselect("Select District", (distdic), default = ['ROXBURY'])
        df = df.loc[df['DISTRICT'].isin(district)]
    df = df.reset_index()
    df = df.drop(['Unnamed: 0','OFFENSE_CODE', 'index', 'Location', 'HOUR', 'MONTH', 'YEAR', 'DAY_OF_WEEK','REPORTING_AREA'], axis =1 )
    rowcount = len(df.index)
    if 1 <= rowcount < 5355:
        st.info(f'{rowcount} results fetched')                      #Showing results based on the keyword and optional filtered data
        if st.checkbox("Show results in DataFrame"):
            st.dataframe(df)
            if st.checkbox("View incident Info"):
                inci = st.text_input("Enter Incident Number")
                infor(inci)
        if st.checkbox("Show results on map"):
            st.text('MAP')
            mapper(df)
    elif rowcount == 0:
        st.error("Please select at least 1 District from the Sidebar")
             
    
def plotops():                                              #function to show options for plotting different charts
    st.header("**Plot Graphs :chart_with_upwards_trend:**")
    st.info("<<== Check Sidebar on the left for options")
    df, distd = read_data()
    distdic = [*distd.values()]
    plott = st.sidebar.radio("Select option", ("Bar Chart", "Line Chart", "Stacked/Grouped Bar Chart"))             #options shown in radio buttons
    if plott == "Bar Chart":
        barch(df)
    elif plott == "Line Chart":
        linech(df)
            
    else:
        bartype = st.radio("", ('Stacked Bar Chart', 'Grouped Bar Chart'))                      #secondary options shown in radio buttons
        if bartype == 'Stacked Bar Chart':                                                      #Creating Stacked bar chart using matplotlib
            df.groupby(['DISTRICT','MONTH']).size().unstack().plot(kind='bar',stacked=True)
            plt.legend(loc=0, fontsize = 'x-small')
            plt.title('Number of crimes in each District/Month')
            plt.xlabel('District')
            plt.ylabel('Number of Crimes')
            plot = plt.show()
            st.pyplot(plot)
        else:                                                                   #Creating grouped bar chart using matplotlib
            if st.checkbox("Select District(s)"):         
                district = st.multiselect("Select District(s)", (distdic), default = ['ROXBURY'])               #selecting different diferent districts for the chart
                df = df.loc[df['DISTRICT'].isin(district)]            
            rowcount = len(df.index)
            if rowcount == 0:
                st.text(f'Please select at least 1 District')
            else:
                df.groupby(['MONTH','DISTRICT']).size().unstack().plot.bar(rot = 0)
                plt.legend(loc=0, fontsize = 'x-small')
                plt.title('Number of crimes in each District/Month')
                plt.xticks(rotation = 35)
                plt.xlabel('Month')
                plt.ylabel('Number of Crimes')
                plot = plt.show()
                st.pyplot(plot)
        
def barch(df):                                  #Funtion to create different barcharts
    df = df[['DISTRICT', 'OCCURRED_ON_DATE']]
    df2 = pd.DataFrame(df.DISTRICT.value_counts().reset_index().values, columns=["DISTRICTS", "Crime_Count"])
    st.text('This Bar-Chart shows the number of crimes in each district for a selected date range. \nSelect a date range in the sidebar')
    if st.sidebar.checkbox("Select Date Range"):
        from_date = st.sidebar.date_input("From", datetime.date(2020,1,1))                      #setting default settings for date input 
        to_date = st.sidebar.date_input("To", datetime.date(2020,4,1))
        df = df.loc[(df['OCCURRED_ON_DATE'] >= from_date) & (df['OCCURRED_ON_DATE'] <= to_date)]        #Croping the dataframe based on the applied filters
        st.markdown(f'Number of Crimes from **{from_date}** to **{to_date}**')
        df = df[['DISTRICT', 'OCCURRED_ON_DATE']]
        df2 = pd.DataFrame(df.DISTRICT.value_counts().reset_index().values, columns=["DISTRICTS", "Crime_Count"])

    base = alt.Chart(df2).mark_bar().encode(
    x='DISTRICTS',
    y='Crime_Count'
    ).properties(
        width=600,
        height=500
    )
    text = base.mark_text(
        align='center',
        baseline='bottom',
    ).encode(
        text='Crime_Count:Q'
    )
    
    st.write((base + text).properties(height=900))
        
def linech(df):                #Function to create different line charts using matplotlib and altair
    df['OCCURRED_ON_DATE'] = [datetime.date() for datetime in df['OCCURRED_ON_DATE']]
    type = st.radio("choose", ('Number of Crimes : Daily', 'Number of Crimes : Monthly', 'Month-District Multiline'))
    if type == 'Number of Crimes : Daily':                                  #Line Chart for total number of crimes Daily
        df2 = pd.DataFrame(df.OCCURRED_ON_DATE.value_counts().reset_index().values, columns=["OCCURRED_ON_DATE", "Crime_Count"])
        Total = df2['Crime_Count'].sum()
        brush = alt.selection(type='interval', encodings=['x'])

        base = alt.Chart(df2).mark_line(point=False).encode(
            x = 'OCCURRED_ON_DATE:T',
            y = 'Crime_Count:Q'
        ).properties(
            width=600,
            height=400
        )
        
        upper = base.encode(
            alt.X('OCCURRED_ON_DATE:T', scale=alt.Scale(domain=brush))
        )
        st.write(base)        
    if type == 'Number of Crimes : Monthly':
        df2 = pd.DataFrame(df.MONTH.value_counts().reset_index().values, columns=["MONTH", "Crime_Count"])
       
        Total = df2['Crime_Count'].sum()
        base = alt.Chart(df2).mark_line(point=True).encode(
            x='MONTH:O',
            y='Crime_Count:Q'
        ).properties(
            width=600,
            height=400
        )
        text = base.mark_text(
            align='center',
            baseline='bottom',
        ).encode(
            text='Crime_Count:Q'
        )
        st.write(base+text)
    if type == 'Month-District Multiline':
        df.groupby(['MONTH','DISTRICT']).size().unstack().plot(kind='line', ylim = (0,300))
        plt.legend(loc=0, fontsize = 'x-small')
        plt.xticks(rotation = 35)
        plt.xlabel('Month')
        plt.ylabel('Number of Crimes')
        plot = plt.show()
        st.pyplot(plot)

def table():                                                                #Function to create interactive pivot table
    st.header("**Pivot Table :control_knobs:**")
    df , distd = read_data()
    collist =df.columns.tolist()
    funclist = ['sum', 'count', 'mean']
    func = st.selectbox("Select function", (funclist), index = 1)
    col = st.multiselect(f"Select column", (collist))
    ind = st.multiselect("Select index", (collist),default = ['DISTRICT', 'MONTH'])
    coln = st.multiselect("Select other columns in table", (collist), default = ['INCIDENT_NUMBER'])
    df.drop(df.columns.difference(col + ind + coln), 1, inplace=True)
    if not col:
        table2 = pd.pivot_table(df, index= ind,  aggfunc= func )
    else:    
        table2 = pd.pivot_table(df, index= ind, columns = col,  aggfunc= func )
    st.table(table2)

def infor(inci):                                            #Function to retrieve information about a particular incident on inserting incident number
    df , dic = read_data()
    y = df.loc[df['INCIDENT_NUMBER'] == inci]    
    for row in y.itertuples():
        st.info(f'''Incident No.: \t\t{row.INCIDENT_NUMBER}
        \nDate & Time : \t\t{row.OCCURRED_ON_DATE} ({row.DAY_OF_WEEK})
        \nOffense Code : \t\t{row.OFFENSE_CODE}
        \nOffense Description :   {row.OFFENSE_DESCRIPTION}
        \nShooting Involved : \t{row.SHOOTING}
        \nStreet : \t\t{row.STREET}
        \nDistrict : \t\t{row.DISTRICT}
        \nLatitude & Logitude :   {row.lat:.6f}, {row.lon:.6f}''')
        st.text('Location of entered incident')
        mapper(y)


def main():
    st.title("Python Project - Boston Crime :cop: :police_car:")                        #Title of the Web-App
    first = st.radio("Select your choice", ("Search Crime Data", "Graphs & Tables"))    
    st.title("------------------------------------------------")
    if first == "Search Crime Data":                                    #Options to choose between searching and search and graphs/table
        st.sidebar.title("Search Crime Data")
        st.header("Search Crime Data :mag:")
        st.info("<<== Check Sidebar on the left for options")
        status = st.sidebar.radio('Search Using', ("Filters", "Keyword"))                
    
        if status == "Filters":
            filter()
        
        else:
            kw = st.sidebar.text_input("Enter a keyword (e.g. - Assault, Boston)")
            kw = kw.upper()
            keyw(kw)
        
    else:
        second = st.sidebar.radio("Select your Choice", ('Graphs','Pivot Table'))
        if second == 'Graphs':
            plotops()
        else:
            table()


main()
    
