# -------------------------------------------------------------------------
# Copyright (c) 2021 NHS England and NHS Improvement. All rights reserved.
# Licensed under the MIT License and the Open Government License v3. See
# license.txt in the project root for license information.
# -------------------------------------------------------------------------

"""
FILE:           ICB_Place_Based_Tool.py
DESCRIPTION:    Streamlit weighted capitation tool
CONTRIBUTORS:   Craig Shenton, Jonathan Pearson, Mattia Ficarelli, Samuel Leat, Jennifer Struthers
CONTACT:        england.revenue-allocations@nhs.net
CREATED:        2021-12-14
VERSION:        0.0.1
"""

# Libraries
# -------------------------------------------------------------------------
# python
import json
import time
import base64
import io
import zipfile
import regex as re
from datetime import datetime
import os
from pathlib import Path

# local
import utils

# 3rd party:
import streamlit as st
import pandas as pd
from streamlit_folium import folium_static
import folium
import toml

#Config file setup
config = toml.load('config.toml')

st.set_page_config(
    page_title="ICB Place Based Allocation Tool",
    page_icon="https://www.england.nhs.uk/wp-content/themes/nhsengland/static/img/favicon.ico",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        "Get Help": "https://www.england.nhs.uk/allocations/",
        "Report a bug": "https://github.com/nhsengland/AIF_Allocation_Tool",
        "About": "This tool is designed to support allocation at places by allowing places to be defined by aggregating GP Practices within an ICB. Please refer to the User Guide for instructions. For more information on the latest allocations, including contact details, please refer to: [https://www.england.nhs.uk/allocations/](https://www.england.nhs.uk/allocations/)",
    },
)
padding = 1
st.markdown(
    f""" <style>
    .reportview-container .main .block-container{{
        padding-top: {padding}rem;
    }} </style> """,
    unsafe_allow_html=True,
)

# Set default place in session
# -------------------------------------------------------------------------
if len(st.session_state) < 1:
    st.session_state["Default Place"] = {
        "gps": [
            "B85005: SHEPLEY PRIMARY CARE LIMITED",
            "B85022: HONLEY SURGERY",
            "B85061: SKELMANTHORPE FAMILY DOCTORS",
            "B85026: KIRKBURTON HEALTH CENTRE",
        ],
        "icb": "NHS West Yorkshire ICB"
    }
if "places" not in st.session_state:
    st.session_state.places = ["Default Place"]

# Functions & Calls
# -------------------------------------------------------------------------


# render svg image
def render_svg(svg):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)


# Download functionality
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode("utf-8")

#Metric calcs. 
def metric_calcs(group_need_indices, metric_index):
    # Convert the value to float and round it using excel_round to 2 decimal places
    place_metric = utils.excel_round(group_need_indices[metric_index][0].astype(float), 0.01)
    # Subtract 1 and then round again using excel_round to 2 decimal places
    icb_metric = utils.excel_round(place_metric - 1, 0.01)
    return place_metric, icb_metric


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

# Markdown
# -------------------------------------------------------------------------
# NHS Logo
svg = """
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 16">
            <path d="M0 0h40v16H0z" fill="#005EB8"></path>
            <path d="M3.9 1.5h4.4l2.6 9h.1l1.8-9h3.3l-2.8 13H9l-2.7-9h-.1l-1.8 9H1.1M17.3 1.5h3.6l-1 4.9h4L25 1.5h3.5l-2.7 13h-3.5l1.1-5.6h-4.1l-1.2 5.6h-3.4M37.7 4.4c-.7-.3-1.6-.6-2.9-.6-1.4 0-2.5.2-2.5 1.3 0 1.8 5.1 1.2 5.1 5.1 0 3.6-3.3 4.5-6.4 4.5-1.3 0-2.9-.3-4-.7l.8-2.7c.7.4 2.1.7 3.2.7s2.8-.2 2.8-1.5c0-2.1-5.1-1.3-5.1-5 0-3.4 2.9-4.4 5.8-4.4 1.6 0 3.1.2 4 .6" fill="white"></path>
          </svg>
"""
render_svg(svg)

st.title("ICB Place Based Allocation Tool " + config['allocations_year'])

#Code below uses the date of last modification for the file to create a last updated date.
script_path = Path(__file__)
last_modified_time = script_path.stat().st_mtime
last_modified_date = time.localtime(last_modified_time)
formatted_date = time.strftime('%d %B %Y', last_modified_date)
st.write(f"Last updated: {formatted_date}")

# SIDEBAR Prologue (have to run before loading data)
# -------------------------------------------------------------------------
# Call the function to set sidebar width
utils.set_sidebar_width(min_width=500, max_width=500)

datasets = os.listdir('data/')

selected_dataset = st.sidebar.selectbox("Time Period:", options = datasets, help="Select a time period", format_func=lambda x : x.replace('.csv','').replace('_','/'))
selected_year = selected_dataset.replace('.csv', '')

st.sidebar.write("-" * 34)  # horizontal separator line.


# Import Data
# -------------------------------------------------------------------------

dataset_dict = {}

# Loads in all datasets, regardless of how many there are
for dataset in datasets:
    year = dataset.replace('.csv', '')
    dataset_dict[year] = utils.get_data('data/' + dataset)

icb = utils.get_sidebar(dataset_dict[selected_year])


# SIDEBAR Main
# -------------------------------------------------------------------------
st.sidebar.subheader("Create New Place")

# ICB Selection
with st.sidebar.expander("Select an ICB", expanded=True):
    icb_choice = st.selectbox("Select an ICB from the drop-down", icb, help="Select an ICB", label_visibility="hidden")

    # Generate the list of LADs based on ICB selection
    lad = dataset_dict[selected_year]["LA District name"].loc[
        dataset_dict[selected_year]["ICB name"] == icb_choice
    ].unique().tolist()

    # Create a DataFrame for the LADs with a 'tick' column
    lad_list_to_select = pd.DataFrame(lad, columns=['Local Authority District'])
    lad_list_to_select['tick'] = False

    # Use st.expander to maintain state for LAD filter
    with st.sidebar.expander('Select Local Authority District(s)', expanded=False):
        lad_choice = st.data_editor(
            lad_list_to_select,
            column_config={
                "tick": st.column_config.CheckboxColumn("Select", default=False)
            },
            hide_index=True
        )

        selected_lads = lad_choice[lad_choice['tick']]["Local Authority District"].tolist()

    # Filter practices based on selected ICB and LADs
    if not selected_lads:
        filtered_practices = dataset_dict[selected_year]["practice_display"].loc[
            dataset_dict[selected_year]["ICB name"] == icb_choice
        ].unique().tolist()
    else:
        filtered_practices = dataset_dict[selected_year]["practice_display"].loc[
            (dataset_dict[selected_year]["LA District name"].isin(selected_lads)) &
            (dataset_dict[selected_year]["ICB name"] == icb_choice)
        ].unique().tolist()

    # Create DataFrame for GP practices with a 'tick' column
    practice_list_to_select = pd.DataFrame(filtered_practices, columns=['GP Practice'])
    practice_list_to_select['tick'] = False

    # Sidebar for GP Practice filter
    with st.sidebar.expander("Select GP Practice(s)", expanded=False):
        # Create three columns for the buttons with reduced width
        col1, col2, col3 = st.columns([1.1, 1.3, 2.2])

        # Place buttons in separate columns
        with col1:
            if st.button("Select all"):
                practice_list_to_select['tick'] = True
                st.session_state.practice_list = practice_list_to_select.copy() #Store in session state

        with col2:
            if st.button("Deselect all"):
                practice_list_to_select['tick'] = False
                st.session_state.practice_list = practice_list_to_select.copy() #Store in session state

        if 'practice_list' not in st.session_state or st.session_state.get('last_icb_choice') != icb_choice or st.session_state.get('last_selected_lads') != selected_lads:
            st.session_state.practice_list = practice_list_to_select.copy()
            st.session_state['last_icb_choice'] = icb_choice
            st.session_state['last_selected_lads'] = selected_lads

        # Practice choice table
        practice_choice = st.data_editor(
            st.session_state.practice_list,
            column_config={
                "tick": st.column_config.CheckboxColumn("Select", default=False)
            },
            hide_index=True
        )

    # Get selected practices
    selected_practices = practice_choice[practice_choice['tick']]["GP Practice"].tolist()

place_name = st.sidebar.text_input(
    "Name your Place",
    "",
    help="Give your defined place a name to identify it",
)

if st.sidebar.button("Save Place", help="Save place to session data"):
    if selected_practices == [] or place_name == "Default Place":
        if selected_practices == []:
            st.sidebar.error("Please select one or more GP practices")
        if place_name == "Default Place":
            st.sidebar.error(
                "Please rename your place to something other than 'Default Place'"
            )
    if place_name == "":
        st.sidebar.error("Please give your place a name")
    else:
        if selected_practices == [] or place_name == "Default Place":
            print("")
        else:
            if (
                len(st.session_state.places) <= 1
                and st.session_state.places[0] == "Default Place"
            ):
                del [st.session_state["Default Place"]]
                del [st.session_state.places[0]]
                if [place_name] not in st.session_state:
                    st.session_state[place_name] = {
                        "gps": selected_practices,
                        "icb": icb_choice
                    }
                if "places" not in st.session_state:
                    st.session_state.places = [place_name]
                if place_name not in st.session_state.places:
                    st.session_state.places = st.session_state.places + [place_name]
            else:
                if [place_name] not in st.session_state:
                    st.session_state[place_name] = {
                        "gps": selected_practices,
                        "icb": icb_choice
                    }
                if "places" not in st.session_state:
                    st.session_state.places = [place_name]
                if place_name not in st.session_state.places:
                    st.session_state.places = st.session_state.places + [place_name]

st.sidebar.write("-" * 34)  # horizontal separator line.

session_state_dict = dict.fromkeys(st.session_state.places, [])
for key, value in session_state_dict.items():
    session_state_dict[key] = st.session_state[key]
session_state_dict["places"] = st.session_state.places

session_state_dump = json.dumps(session_state_dict, indent=4, sort_keys=False)

# Use file uploaded to read in groups of practices
advanced_options = st.sidebar.checkbox("Advanced Options")
if advanced_options:
    # downloads
    st.sidebar.download_button(
        label="Download session data as JSON",
        data=session_state_dump,
        file_name="session.json",
        mime="text/json",
    )
    # uploads
    form = st.sidebar.form(key="my-form")
    group_file = form.file_uploader(
        "Upload previous session data as JSON", type=["json"]
    )
    submit = form.form_submit_button("Submit")
    if submit:
        if group_file is not None:
            d = json.load(group_file)
            st.session_state.places = d["places"]
            for place in d["places"]:
                st.session_state[place] = d[place]
            my_bar = st.sidebar.progress(0)
            for percent_complete in range(100):
                time.sleep(0.01)
                my_bar.progress(percent_complete + 1)
            my_bar.empty()

see_session_data = st.sidebar.checkbox("Show Session Data")

# BODY
# -------------------------------------------------------------------------

select_index = len(st.session_state.places) - 1  # find n-1 index
placeholder = st.empty()
option = placeholder.selectbox(
    "Select Place", (st.session_state.places), index=select_index, key="before"
)

# DELETE PLACE
# -------------------------------------------------------------------------
if "after" not in st.session_state:
    st.session_state.after = st.session_state.before

label = "Delete Current Selection"
delete_place = st.button(label, help=label)
my_bar_delete = st.empty()
if delete_place:
    if len(st.session_state.places) <= 1:
        del [st.session_state[st.session_state.after]]
        if "Default Group" not in st.session_state:
            st.session_state["Default Place"] = {
                "gps": [
                    "B85005: SHEPLEY PRIMARY CARE LIMITED",
                    "B85022: HONLEY SURGERY",
                    "B85061: SKELMANTHORPE FAMILY DOCTORS",
                    "B85026: KIRKBURTON HEALTH CENTRE",
                ],
                "icb": "NHS West Yorkshire ICB"
            }
        if "places" not in st.session_state:
            st.session_state.places = ["Default Place"]
        else:
            st.session_state["Default Place"] = {
                "gps": [
                    "B85005: SHEPLEY PRIMARY CARE LIMITED",
                    "B85022: HONLEY SURGERY",
                    "B85061: SKELMANTHORPE FAMILY DOCTORS",
                    "B85026: KIRKBURTON HEALTH CENTRE",
                ],
                "icb": "NHS West Yorkshire ICB"
            }
        st.session_state.places = ["Default Place"]
        st.session_state.after = "Default Place"
        st.warning(
            "All places deleted. 'Default Place' reset to default. Please create a new place."
        )
        my_bar_delete.progress(0)
        for percent_complete in range(100):
            time.sleep(0.01)
            my_bar_delete.progress(percent_complete + 1)
        my_bar_delete.empty()
    else:
        del [st.session_state[st.session_state.after]]
        del [
            st.session_state.places[
                st.session_state.places.index(st.session_state.after)
            ]
        ]
        my_bar_delete.progress(0)
        for percent_complete in range(100):
            time.sleep(0.01)
            my_bar_delete.progress(percent_complete + 1)
        my_bar_delete.empty()

select_index = len(st.session_state.places) - 1  # find n-1 index
option = placeholder.selectbox(
    "Select Place", (st.session_state.places), index=select_index, key="after"
)
icb_name = st.session_state[st.session_state.after]["icb"]
group_gp_list = st.session_state[st.session_state.after]["gps"]

# MAP
# -------------------------------------------------------------------------

map = folium.Map(location=[52, 0], zoom_start=10, tiles="openstreetmap")
lat = []
long = []

for gp in group_gp_list:
    escaped_gp = re.escape(gp)
    if ~dataset_dict[selected_year]["practice_display"].str.contains(escaped_gp).any():
        st.write(f"{gp} is not available in this time period")
        continue
    latitude = dataset_dict[selected_year]["Latitude"].loc[dataset_dict[selected_year]["practice_display"] == gp].item()
    longitude = dataset_dict[selected_year]["Longitude"].loc[dataset_dict[selected_year]["practice_display"] == gp].item()
    lat.append(latitude)
    long.append(longitude)
    folium.Marker(
        [latitude, longitude],
        popup=str(gp),
        icon=folium.Icon(color="darkblue", icon="fa-user-md", prefix="fa"),
    ).add_to(map)


if not lat:
    st.write("No GP Practices in this Place are available in this time period")
    st.stop()

# bounds method https://stackoverflow.com/a/58185815
map.fit_bounds(
    [[min(lat) - 0.02, min(long)], [max(lat) + 0.02, max(long)]]
)  # add buffer to north
# call to render Folium map in Streamlit
folium_static(map, width=700, height=300)

# Group GP practice display
list_of_gps = re.sub(
    "\w+:",
    "",
    str(group_gp_list).replace("'", "").replace("[", "").replace("]", ""),
)
st.info(f"This information pertains to the **{selected_year.replace("_","/")}** time period")
st.info("**Selected GP Practices:**" + list_of_gps)


gp_query = "practice_display == @place_state"
icb_query = "`ICB name` == @icb_state"  # escape column names with backticks https://stackoverflow.com/a/56157729

# "Weighted G&A pop",
# "Weighted Community pop",
# "Weighted Mental Health pop",
# "Weighted Maternity pop",
# "Weighted Health Inequalities pop",
# "Weighted Prescribing pop",
# "Overall Weighted pop",

# order = [
#     0,
#     -9,
#     -8,
#     -7,
#     -6,
#     -5,
#     -4,
#     -2,
#     -3,
#     -1,
#     1,
#     2,
#     3,
#     4,
#     5,
#     6,
#     7,
#     8,
#     9,
#     10,
# ]  # setting column's order
# large_df = large_df[[large_df.columns[i] for i in order]]

# All metrics - didn't work well, but might be useful
# for option in dict_obj:
#     st.write("**", option, "**")
#     for count, df in enumerate(dict_obj[option][1:]):  # skip first (ICB) metric
#         # Group GP practice display
#         group_name = dict_obj[option][count + 1]["Group / ICB"].item()
#         group_gps = (
#             "**"
#             + group_name
#             + " : **"
#             + re.sub(
#                 "\w+:",
#                 "",
#                 str(st.session_state[group_name]["gps"])
#                 .replace("'", "")
#                 .replace("[", "")
#                 .replace("]", ""),
#             )
#         )
#         st.info(group_gps)
#         cols = st.columns(len(metric_cols))
#         for metric, name in zip(metric_cols, metric_names):
#             place_metric, icb_metric = metric_calcs(dict_obj[option][count], metric,)
#             cols[metric_cols.index(metric)].metric(
#                 name, place_metric,  # icb_metric, delta_color="inverse"
#             )

# Metrics
# -------------------------------------------------------------------------
data_all_years = utils.get_data_for_all_years(dataset_dict, st.session_state, aggregations, index_numerator, index_names, gp_query, icb_query) #this is getting the other data
df = data_all_years[selected_year].loc[data_all_years[selected_year]["Place / ICB"] == st.session_state.after]
df = df.reset_index(drop=True)

#Core Index
metric_cols = [
    "G&A Index",
    "Community Index",
    "Mental Health Index",
    "Maternity Index",
]

metric_names = [
    "Gen & Acute",
    "Community*",
    "Mental Health",
    "Maternity",
]

metric_cols2 = [
    "Prescribing Index",
    "Primary Medical Care Need Index",
    "Health Inequalities Index",
]

metric_names2 = [
    "Prescribing",
    "Primary Medical in Core**",
    "Health Inequals",
]

place_metric, icb_metric = metric_calcs(df, "Overall Core Index")
place_metric = "{:.2f}".format(place_metric)
st.header("Core Index: " + str(place_metric))

with st.expander("Core Sub Indices", expanded  = True):

    cols = st.columns(len(metric_cols))
    for metric, name in zip(metric_cols, metric_names):
        place_metric, icb_metric = metric_calcs(
            df,
            metric,
        )
        place_metric = "{:.2f}".format(place_metric)
        cols[metric_cols.index(metric)].metric(
            name,
            place_metric,  # icb_metric, delta_color="inverse"
        )

    cols = st.columns(len(metric_cols2)+1)
    for metric, name in zip(metric_cols2, metric_names2):
        place_metric, icb_metric = metric_calcs(
            df,
            metric,
        )
        place_metric = "{:.2f}".format(place_metric)
        cols[metric_cols2.index(metric)].metric(
            name,
            place_metric,  # icb_metric, delta_color="inverse"
        )

#Component Relative Weighting
with st.expander("Relative Weighting of Components"):
    st.markdown(
        """The relative weighting applied to each of these components are provided in Workbook J.  These weightings are based on modelled estimated expenditure in 2025/26.
        \n\nThese relative weightings are based on national modelled expenditure, and do not take into consideration variation of weights at the local level.  It is not appropriate to apply these weights to place-level indices that are relative to the ICB, not England.
        """)

#Primary Care Index
#Core Index
metric_cols = [
    "Primary Medical Care Need Index",
    "Health Inequalities Index",
]

metric_names = [
    "Primary Medical Care Need****",
    "Health Inequals",
]
place_metric, icb_metric = metric_calcs(df, "Primary Medical Care Index")
place_metric = "{:.2f}".format(place_metric)
st.header("Primary Medical Care Index: " + str(place_metric))
st.caption("Based on weighted populations from the formula for ICB allocations, not the global sum weighted populations***")

with st.expander("Primary Medical Care Sub Indices", expanded  = True):

    cols = st.columns(3)
    for metric, name in zip(metric_cols, metric_names):
        place_metric, icb_metric = metric_calcs(
            df,
            metric,
        )
        place_metric = "{:.2f}".format(place_metric)
        cols[metric_cols.index(metric)].metric(
            name,
            place_metric,  # icb_metric, delta_color="inverse"
        )

# Downloads
# -------------------------------------------------------------------------
current_date = datetime.now().strftime("%Y-%m-%d")

st.subheader("Download Data")

print_table = st.checkbox("Preview data download", value=True)
if print_table:
    with st.container():
        utils.write_table(data_all_years[selected_year])

# csv_header = b'WARNING: this is a warning message'
# CSV Header content
csv_header1 = "PLEASE READ: Below you can find the results for the places you created, and for the ICB they belong to, for the year you selected."
csv_header2 = "Note that the need indices for the places are relative to the ICB (where the ICBs need index = 1.00), while the need index for the ICB is relative to national need (where the national need index = 1.00)."
csv_header3 = "This means that the need indices of the individual places cannot be compared to the need index of the ICB. For more information, see the FAQ tab available in the tool."
csv_header4 = ""


# Create a BytesIO buffer for the Excel file
excel_buffer = io.BytesIO()
# Create a Pandas Excel writer using the XlsxWriter engine
with pd.ExcelWriter(excel_buffer, engine='xlsxwriter') as writer:
    
    for year, df in data_all_years.items():
        worksheet_name = f"Allocations for {year}" #Got to be less than 32 characters
        worksheet = writer.book.add_worksheet(worksheet_name.replace("/", "_")) #Excel doesn't like the slashes
        start_row = utils.write_headers(worksheet, csv_header1, csv_header2, csv_header3, csv_header4)

        # Write the DataFrame column names
        worksheet.write_row(start_row, 0, df.columns)
        for r, row in enumerate(df.values, start=start_row+1):
            worksheet.write_row(r,0,row)
    # Save the Excel file
    writer.close()

# Move the pointer of the buffer to the beginning
excel_buffer.seek(0)




# Open the text documentation file
with open("docs/ICB allocation tool documentation.txt", "rb") as fh:
    readme_text = io.BytesIO(fh.read())

# Create JSON dump of the session state (example)
session_state_dict = dict.fromkeys(st.session_state.places, [])
for key, value in session_state_dict.items():
    session_state_dict[key] = st.session_state[key]
session_state_dict["places"] = st.session_state.places
session_state_dump = json.dumps(session_state_dict, indent=4, sort_keys=False)

# Create a ZIP file containing the Excel file, documentation, and configuration
zip_buffer = io.BytesIO()
with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
    zip_file.writestr(f"ICB allocation calculations.xlsx", excel_buffer.getvalue())
    zip_file.writestr("ICB allocation tool documentation.txt", readme_text.getvalue())
    zip_file.writestr("ICB allocation tool configuration file.json", session_state_dump)

# Ensure the ZIP file buffer's pointer is at the start
zip_buffer.seek(0)

# Streamlit download button
btn = st.download_button(
    label="Download ZIP",
    data=zip_buffer.getvalue(),
    file_name=f"ICB allocation tool {current_date}.zip",
    mime="application/zip",
)

with st.expander("Notes", expanded = True):
    st.markdown(
        "*The Community Services index relates to the half of Community Services that are similarly distributed to district nursing. The published Community Services target allocation is calculated using the Community Services model. This covers 50% of Community Services. The other 50% is distributed through the General & Acute model."
    )
    st.markdown("")
    st.markdown(
        "**The Primary Medical Care in Core element covers Other primary care services (not relating to pharmaceutical, ophthalmic, and dental services), NHS 111, and out of hours services."
        )
    st.markdown("")
    st.markdown(
        "***The global sum weighted populations are calculated using the Carr-Hill formula. The global sum weighted populations are a key component of payments to GP practices under the GMS contract. Funding GP practices is part of ICB’s commissioning responsibilities."
        )
    st.markdown("")
    st.markdown(
        "****The Primary Medical Care Need Indices will not include the dispensing doctors adjustment – this is applied at ICB level."
        )

with st.expander("About the ICB Place Based Tool", expanded = True):
    st.markdown(
        "This tool is designed to support allocation at places by allowing places to be defined by aggregating GP Practices within an ICB. Please refer to the User Guide for instructions."
    )
    st.markdown("The tool estimates the relative need for places within the ICB.")
    st.markdown(
        "The Relative Need Index for ICB (i) and Defined Place (p) is given by the formula:"
    )
    st.latex(r""" (WP_p/GP_p)\over (WP_i/GP_i)""")
    st.markdown(
        "Where *WP* is the weighted population for a given need and *GP* is the GP practice population."
    )
    st.markdown(
        f"This tool is based on estimated need for 2023/24 and 2024/25 by utilising weighted populations projected from the November 2021 to October 2022 GP Registered practice populations."
    )
    st.markdown(
        "More information on the latest allocations, including contact details, can be found [here](https://www.england.nhs.uk/allocations/)."
    )

st.info(
    "For support with using the AIF Allocation tool please email: [england.revenue-allocations@nhs.net](mailto:england.revenue-allocations@nhs.net)"
)

# Show Session Data
# -------------------------------------------------------------------------
if see_session_data:
    st.subheader("Session Data")
    st.session_state


