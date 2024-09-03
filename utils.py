import streamlit as st
from st_aggrid import AgGrid

import pandas as pd

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



def aggregate(df, query, name, on, aggregations):
    
    if on not in df.columns:
        df.insert(loc=0, column=on, value=name)
    df_group = df.groupby(on).agg(aggregations)
    df_group = df_group.round(0).astype(int)
    return df, df_group

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

import os
def get_data_for_other_year(selected_dataset, session_state):
    aggregations = {
    "GP pop": "sum",
    "Weighted G&A pop": "sum",
    "Weighted Community pop": "sum",
    "Weighted Mental Health pop": "sum",
    "Weighted Maternity pop": "sum",
    "Weighted Prescribing pop": "sum",
    "Overall Weighted pop": "sum",
    "Weighted Primary Care": "sum",
    "Weighted Primary Medical Care Need": "sum",
    "Weighted Health Inequalities pop": "sum",
}
    index_numerator = [
    "Weighted G&A pop",
    "Weighted Community pop",
    "Weighted Mental Health pop",
    "Weighted Maternity pop",
    "Weighted Prescribing pop",
    "Overall Weighted pop",
    "Weighted Primary Care",
    "Weighted Primary Medical Care Need",
    "Weighted Health Inequalities pop",
]

    index_names = [
    "G&A Index",
    "Community Index",
    "Mental Health Index",
    "Maternity Index",
    "Prescribing Index",
    "Overall Core Index",
    "Primary Medical Care Index",
    "Primary Medical Care Need Index",
    "Health Inequalities Index",
    
]

    gp_query = "practice_display == @place_state"
    icb_query = "`ICB name` == @icb_state"  # escape column names with backticks https://stackoverflow.com/a/56157729

    # this returns list of all other datasets filenames that are NOT the selected one
    datasets = os.listdir('data/')
    other_datasets = [f for f in datasets if f != selected_dataset]

    data_dict = {}

    for filename in other_datasets:
        # Construct the full path to the file
        file_path = os.path.join('data/', filename)
        
        # Load the data from the file
        data_loaded = get_data(file_path)
        
        # Optionally copy or process the data
        data_dict[filename] = data_loaded.copy()

    #now data dict has dict of all data
    for filename, data in data_dict.items():
        # dict to store all dfs sorted by ICB
        dict_obj = {}
        df_list = []

        #FOR EACH PLACE in the SESSION STATE aggregate the data at the ICB and Place level, calculate indices 
        #adds them to a dictionary object
        print("hello")
        print(session_state)
        print(session_state['Default Place']['gps'])
        for place in session_state.places:
            place_state = session_state[place]["gps"]
            icb_state = session_state[place]["icb"]
                # get place aggregations
            df = data.query(gp_query)
            place_data, place_groupby = aggregate(
                df, gp_query, place, "Place Name", aggregations
            )
            print("aaaaaa")
            # get ICB aggregations
            df = data.query(icb_query)
            icb_data, icb_groupby = aggregate(
                df, icb_query, icb_state, "ICB name", aggregations
            )
            print("bbbbb")


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
    data_dict[filename] = large_df

    return data_dict

