import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder

import pandas as pd
from decimal import Decimal, ROUND_HALF_UP
import os

# Load data and cache
@st.cache_data()  # use Streamlit cache decorator to cache this operation so data doesn't have to be read in everytime script is re-run
def get_data(path):
    print('cache miss')
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "Practice_Code": "GP Practice code",
            "GP_Practice_Name": "GP Practice name",
            "Practice_Postcode": "GP Practice postcode",
            "CCG": "CCG code",
            "Former CCG": "CCG name",
            "PCN_Code": "PCN code",
            "PCN_Name": "PCN name",
            "LOC": "Location code",
            "LOCname": "Location name",
            "ICB": "ICB code",
            "ICBname": "ICB name",
            "RCode": "Region code",
            "Region": "Region name",
            "LAD": "LA District code",
            "LTLA": "LA District name",
            "LA": "LA code",
            "UTLA": "LA name",
            "Patients": "Registered Patients",
            "Population": "GP pop",
            "G&A WP": "Weighted G&A pop",
            "CS WP": "Weighted Community pop",
            "MH WP": "Weighted Mental Health pop",
            "Mat WP": "Weighted Maternity pop",
            "Health Ineq WP": "Weighted Health Inequalities pop",
            "Prescr WP": "Weighted Prescribing pop",
            "Final WP": "Overall Weighted pop",
            "Primary Medical Care WP": "Weighted Primary Medical Care Need",
            "Final PMC WP": "Weighted Primary Care",
            

        }
    )
    df = df.fillna(0)
    df["practice_display"] = df["GP Practice code"] + ": " + df["GP Practice name"]
    return df


# Store defined places in a list to access them later for place based calculations
def store_data():
    if 'data_list' not in st.session_state:
        st.session_state.data_list = []
    return st.session_state.data_list


# Sidebar dropdown list
@st.cache_data
def get_sidebar(data):
    icb = data["ICB name"].unique().tolist()
    icb.sort()
    return icb

# Example utility function to render a table with the first column frozen and no bottom bar
def write_table(data):
    # Create grid options to pin the first column
    gb = GridOptionsBuilder.from_dataframe(data)

    # Freeze the first column (index 0)
    gb.configure_column(list(data.columns)[0], pinned='left')
    
    # Build the gridOptions dictionary
    gridOptions = gb.build()
    
    # Display the table with AgGrid
    return AgGrid(data, gridOptions=gridOptions)


def write_headers(sheet, *csv_headers):
    """
    Function takes an unlimited amount of headers and writes them to the top of an excel sheet

    Parameters:
    sheet (str): name of the sheet
    *csv_headers (str): individual strings with the header information

    Returns:
    The integer number of the row where the data should be placed (leaving a space after the headers)
    """
    # Loop through the csv_headers and write each header to the sheet
    for index, header in enumerate(csv_headers):
        sheet.write(index, 0, header)
    
    header_row_count = len(csv_headers)
    
    return header_row_count + 1  # Return the starting row for data

# Aggregates a dataframe; how data is grouped and which aggregations are performed depends on given inputs.
# Used exclusively in the get_data_all_years function; when used there inputs are as below:
## df is the already filtered (using a query string) data from the dataset_dict, meaning the data will only contain a single place or ICB before aggregate is run.
## name is the place taken from the session_state.places list, used to populate the "on" field if it's not already in the data.
## on is either the string "Place Name" or "ICB name", telling the function what to group on.
## aggregations is the library of column names and aggregation functions, defined in the main tool page.
# This function also checks that the df includes the specified "on" column and, if not, creates it and populates it with the name value, before aggregating.
# The outputs are the same df initially loaded into the function (df) and the aggregated and grouped df (df_group)
def aggregate(df, name, on, aggregations):
    if on not in df.columns:
        df.insert(loc=0, column=on, value=name)

    df_group = df.groupby(on).agg(aggregations)

    return df, df_group

#Calculate index of weighted populations. Take the groupby output fromn the aggregator and divides it by the population number. Do it by icb and place. 
#get_index(place_groupby, icb_groupby, index_names, index_numerator)
#place index is divided by icb index to get a relative number
#overall index is final_wp / gp pop
def get_index(place_indices, icb_indices, index_names, index_numerator):
    icb_indices[index_names] = icb_indices[index_numerator].div(
        icb_indices["GP pop"].values, axis=0
    )
    place_indices[index_names] = (
        place_indices[index_numerator]
        .div(place_indices["GP pop"].values, axis=0)
        .div(icb_indices[index_names].values, axis=0)
    )
    return place_indices, icb_indices


def get_data_for_all_years(dataset_dict, session_state, aggregations, index_numerator, index_names, gp_query, icb_query):
    """
    Processes and aggregates data for all datasets across multiple years.

    This function iterates over all datasets in the given `dataset_dict`, aggregates data for each place
    and Integrated Care Board (ICB) specified in the `session_state`, and calculates indices based on the 
    provided aggregation functions and queries. The aggregated and indexed data is then stored back in 
    the `dataset_dict` for each dataset.

    Parameters:
    ----------
    dataset_dict : dict
        A dictionary where the keys are filenames and the values are corresponding datasets (DataFrames).
        
    session_state : object
        An object that contains the session state, including a list of places and corresponding 
        geographical and ICB information for each place.
        
    aggregations : dict
        A dictionary specifying the aggregation functions to apply to the data. The keys are column names
        and the values are aggregation functions (e.g., 'sum', 'mean').

    index_numerator : str
        The column name to use as the numerator for index calculations.

    index_names : list
        A list of column names to use as the denominator for index calculations.

    gp_query : str
        A query string to filter the data for place-level aggregations.

    icb_query : str
        A query string to filter the data for ICB-level aggregations.

    Returns:
    -------
    dict
        The updated `dataset_dict` where each dataset (DataFrame) has been aggregated, indexed, and rounded 
        to three decimal places. Each dataset is a DataFrame with data aggregated at the ICB and place level.

    """

    # Loop through all datasets
    # This has potential to take time but I think with the size of data it's neglible.
    for filename, data in dataset_dict.items():
        # dict to store all dfs sorted by ICB
        dict_obj = {}
        df_list = []

        #FOR EACH PLACE in the SESSION STATE aggregate the data at the ICB and Place level, calculate indices 
        #adds them to a dictionary object
        for place in session_state.places:
            place_state = session_state[place]["gps"]
            icb_state = session_state[place]["icb"]

            # get place aggregations
            df = data.query(gp_query)
            place_data, place_groupby = aggregate(
                df, place, "Place Name", aggregations
            )

            # get ICB aggregations
            df = data.query(icb_query)
            icb_data, icb_groupby = aggregate(
                df, icb_state, "ICB name", aggregations
            )

            # index calcs
            place_indices, icb_indices = get_index(
                place_groupby, icb_groupby, index_names, index_numerator
            )

            icb_indices.insert(loc=0, column="Place / ICB", value=icb_state)
            place_indices.insert(loc=0, column="Place / ICB", value=place)

            if icb_state not in dict_obj:
                dict_obj[icb_state] = [icb_indices, place_indices]
            else:
                dict_obj[icb_state].append(place_indices)

        # add dict values to list
        for obj in dict_obj:
            df_list.append(dict_obj[obj])

        # flaten list for concatination
        flat_list = [item for sublist in df_list for item in sublist]
        large_df = pd.concat(flat_list, ignore_index=True)

        # Rounding the data here, after calculations are done to maintain accuracy - numerators and indices are rounded differently
        large_df[index_numerator + ["GP pop"]] = large_df[index_numerator + ["GP pop"]].map(lambda x: excel_round(x, 1))
        large_df[index_names] = large_df[index_names].map(lambda x: excel_round(x, 0.001))

        dataset_dict[filename] = large_df

    return dataset_dict



def excel_round(number, precision=0.01) -> float:
    """
    Rounds a number to a specified precision using the "round half up" method, similar to Excel.

    Parameters:
    number (float/int): The number to be rounded.
    precision (float/int): The precision to round to (e.g., 0.1, 0.01, 100, etc.).

    Returns:
    float: The rounded number, or the original value if it's not numeric.
    """
    try:
        if isinstance(number, (int, float)):  # Ensure the number is numeric
            if precision > 1:  # For rounding to nearest ten, hundreds, etc.
                rounded_num = round(number / precision) * precision
            else:  # For decimal precision
                number = Decimal(str(number))
                precision = Decimal(str(precision))
                rounded_num = number.quantize(precision, rounding=ROUND_HALF_UP)
            return float(rounded_num)
        else:
            return number  # Return the value unchanged if it's not numeric
    except (ValueError, InvalidOperation):
        return number  # Return the value unchanged if there's an error during conversion

# Helper function to inject CSS for sidebar width
def set_sidebar_width(min_width=300, max_width=300):
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] {{
            min-width: {min_width}px;
            max-width: {max_width}px;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )