import streamlit as st
from st_aggrid import AgGrid

import pandas as pd
import os

# Load data and cache
@st.cache()  # use Streamlit cache decorator to cache this operation so data doesn't have to be read in everytime script is re-run
def get_data(path):
    print('cache miss')
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "Practice_Code": "GP Practice code",
            "GP_Practice_Name": "GP Practice name",
            "Practice_Postcode": "GP Practice postcode",
            "CCG21": "CCG code",
            "Former CCG": "CCG name",
            "PCN_Code": "PCN code",
            "PCN_Name": "PCN name",
            "LOC22": "Location code",
            "LOC22name": "Location name",
            "ICS22": "ICB code",
            "ICS22name": "ICB name",
            "R22": "Region code",
            "Region22": "Region name",
            "LAD21": "LA District code",
            "LTLA21": "LA District name",
            "LA21": "LA code",
            "UTLA21": "LA name",
            "Patients": "Registered Patients",
            "pop 2022/23": "GP pop",
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
    df = df.fillna(1).replace(0, 1)
    df["practice_display"] = df["GP Practice code"] + ": " + df["GP Practice name"]
    return df


# Store defined places in a list to access them later for place based calculations
@st.cache(allow_output_mutation=True)
def store_data():
    return []


# Sidebar dropdown list
@st.cache
def get_sidebar(data):
    icb = data["ICB name"].unique().tolist()
    icb.sort()
    return icb


def write_table(data):
    return AgGrid(data)


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

# aggregate on a query and set of aggregations
#Name is the name of the place in the session state, 'aggregations' tells it how to sum each column, 'on' is what to group it by. Not sure what the not in bit is doing. 
#Query filters to make sure that GP Display (which is the gp name and code joined together by utils) is in the session state place list
# Function outputs filtered data and grouped, filtered data separately
def aggregate(df, name, on, aggregations):
    # This df has already been queried.
    if on not in df.columns:
        df.insert(loc=0, column=on, value=name)
    df_group = df.groupby(on).agg(aggregations)
    df_group = df_group.round(0).astype(int)
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
        large_df = large_df.round(decimals=3)
        dataset_dict[filename] = large_df

    return dataset_dict

