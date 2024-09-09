import streamlit as st
import base64
from pathlib import Path
import time
import toml

config = toml.load('config.toml')

st.set_page_config(
    page_title="ICB Place Based Allocation Tool FAQs",
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

def render_svg(svg):
    """Renders the given svg string."""
    b64 = base64.b64encode(svg.encode("utf-8")).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s"/>' % b64
    st.write(html, unsafe_allow_html=True)

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

st.title("ICB Place Based Allocation Tool " + config['allocations_year'] + " FAQs")

#Code below uses the date of last modification for the file to create a last updated date.
script_path = Path(__file__)
last_modified_time = script_path.stat().st_mtime
last_modified_date = time.localtime(last_modified_time)
formatted_date = time.strftime('%d %B %Y', last_modified_date)
st.write(f"Last updated: {formatted_date}")

with st.expander("What does the tool do?"):
    st.markdown("""This tool was built to provide Integrated Care Boards (ICBs) insight into the local-level data underlying their ICB-level resource allocation. It uses recently 
    produced GP registered practice populations as well as the weighted populations calculated from the allocation model for each of its components. More information on the 
    allocations process, as well as useful documentation can be found at https://www.england.nhs.uk/allocations/. \n\nThe data used to allocate resources consists of GP-practice 
    level data for the following model components and their sub-components. With exception of health inequalities<sup>1</sup>), the data for these components reflect modelled need based 
    on historic and projected service use:""", unsafe_allow_html=True)
    st.markdown("""
    - Core Services:
        - General and Acute
        - Community services
        - Mental health services
        - Maternity
        - Prescribing
    - Primary Medical Care:
        - Primary Medicare Care need
    - Cross-components:
        - Health inequalities
    """)
    st.markdown("""
    The tool allows users to build up self-defined places by selecting GP practices and assigning them to a place. It then returns the need indices for the above components 
    as well as an overall need index for the defined place, relative to the ICB in which the place is located.
    \n\nThe need indices for these places are relative to their ICB, meaning that a value of 1.00 means that need for that component in the defined place equals the level of 
    need of the ICB. If a place displays a value below 1.00, this means there is a lower level of need in that place compared to the ICB. A value above 1.00 means there is a 
    higher need in that place compared to the ICB.
    \n\nThe intention of the tool is that these results may help inform ICB-level allocations and contribute to evidence-based resource decisions.""")
    st.caption("""(1)The measure used to calculate the health inequalities need index is Avoidable mortality. This avoidable 
    mortality need index is used to implement the Health inequalities and unmet need adjustment, but we use 
    Health inequalities, or HI, as a shorthand. Avoidable mortality only includes deaths that could have been avoided 
    through public health measures and timely and effective health care intervention. Furthermore, the definition of 
    the measure of avoidable mortality used here generally includes these avoidable deaths for people aged under 
    75, except for some specific causes of death where it includes deaths of people of all ages, where these causes 
    are deemed to be avoidable at all ages.""")

with st.expander("How do I create a place?"):
    col1, col2 = st.columns(2)

    with col1:
        st.image("images/PBTFAQ1.png", caption="Figure 1: DESCRIPTION NEEDED", width=292)

    with col2:
        st.markdown("""
            To create a place, input is required on the left-hand side of the tool. Please note that the Default place that is shown when first accessing the site, is for illustration only, it will not be included in the download under Step 3 in Section 4. If you do want to keep this place in the download, please rename it.
            \n\n**1a:** Unlike the previous version of this tool, this version covers two years (2023/24 and 2024/25). Please select which year you would like to tool to show by selecting this in the dropdown indicated in page element 1a). Please note that the download function (steps 3a-3c) will only download the selected year.
            \n\n**1b:** Select the ICB of interest. You can select only one ICB at a time. This will filter the options available to you in the two drop-down menus below (Local Authority District Filter and Select GP Practice).
            \n\n**1c:** If you want to select GP practices from one or more specific Local Authority District(s), select these in this dropdown. You can select multiple Local Authority Districts at once.
            """)
    st.markdown("""**1d:** You can then either select all GP practices for those Local Authority Districts selected under step 1c) by ticking “Select all” under this step. Alternatively, select the individual GP practices you want to include in your defined place. The dropdown under this filter will only show GP practices that are both in the ICBs and Local Authority Districts you selected from the previous drop-down menus. It does not, for example, include GP practices that are in a selected Local Authority but are not part of the selected ICB.
        \n\nYou can select multiple GP practices at once, either by individually selecting the GP practices from the dropdown list, or by typing part of the practice code or name in the GP practices box: this will then suggest the closest matched GP practice which you can click on to add it to the list.
        \n\n**1e:** Give your place a name by typing the name into the text box.
        \n\n**1f** Clicking the “Save Place” button will then add each selected GP practice to the place you named and displayed visually on the dashboard.
        \n\nPlease note that:
        """)
    st.markdown("""
        - If you want to make changes to a place you already defined you can add more GP practices in 1d and press “Save Place” again to update.
        - Once you have saved a place, you can then create a new place in the same way. You will not overwrite the place you created previously as long as you have saved it under a new name.
        - If you want to delete a place and start again, please refer to Step 2 under Section 3.
        - You can select the same GP practice to be in different places (e.g. if you create place A and B, both can include GP practice X).
        """)
    st.markdown("""
        **Warning:** Refreshing the web page will reset all your inputs including your saved places. Only refresh the page if you do not want to keep your saved places. Alternatively, download your work first (under Section 4 / Step 3) which will download a save file for the tool from which you can return to your saved places.
        """)

with st.expander("How do I view my saved places?"):
    st.markdown("""
        To view the places you created and their relative need indices, some user input is required in the main body of the tool, on the right-hand side. This functionality allows you to check the places you created, change them, and view their relative need indices.
        \n\nNote that you can only view one place at a time in the part of the tool displayed in Figure 2.
        """)
    st.image("images/PBTFAQ2.png", caption="Figure 2: DESCRIPTION NEEDED")
    st.markdown("""
        **2a)** Once you have created a new place, the place name will become available in the main page dropdown menu. If you create multiple places, you can switch between them here. The place you select in this dropdown is the active place, and while it is active (i.e. you have it selected) the page elements 2b, 2c, 2d, and 2e will all refer to the active place.
        \n\n**2b)** If you want to remove the active place completely, click the button “Delete current selection”. If you delete all of your saved places, the app will return to the default place shown in Figure 1.
        \n\n**2c)** The map feature provides a helpful check on the geography and relative locations of the selected GP practices. This is useful to check that you included those GP practices in your defined place that you intended.
        \n\n**2d)** This box lists the GP practices that make up the active year and place you selected in steps 1a and 2a. This information is here to also help you check whether you have the desired GP practices in your defined place.
        \n\n**2e)** The dashboard provides the relative need indices for the active year and place you selected under steps 1a and 2a. These are the combined need indices for the GP practices that make up the active place selected. These need indices are always relative to the ICB (i) and defined place (p) given by the formula:
        """)
    st.latex(r'''
        {WP_{p}/GP_{p} \over WP_{i}/GP_{i}}
        ''')
    st.markdown("""
        Where *WP* is the weighted population for a given need and *GP* is the GP practice population. These weighted populations are based on estimated need for 2023/24 and 2024/25 by utilising weighted populations projected from the November 2021 to October 2022 GP Registered practice populations.
        """)

with st.expander("How do I download my saved places data?"):
    st.markdown("""
    You can download the results for the places you created. This requires some user input in the main body of the tool, on the right-hand side.
    """)
    st.image("images/PBTFAQ3.png", caption="Figure 3: DESCRIPTION NEEDED")
    st.markdown("""
    **3a)** Scroll down below the “Relative Need Index” to “Download Data”. Here you can preview the data download by ensuring the box “Preview data download” is ticked (this is ticked by default).
    \n\n**3b)** A preview of the data downloads as a table showing the need indices for all components and the overall need index (columns). It will also give an overview of all the created places and ICBs you created places for (rows). This overview also gives you the ability to compare need indices across your defined places.
    \n\n***Please Note:** The ICB need indices shown here are not comparable with the need indices of the created places. The former is relative to the national need, whereas the place need indices are calculated relative to the ICB need.*
    \n\n**3c)** To download the data, click “Download ZIP”. A time-stamped ZIP file will then be downloaded into your default download folder and contains the following items:
    """)
    st.markdown("""
    - 'ICB allocation calculations.csv': The data you previewed under step 3b in a Comma Separated Value (.csv) file which can be opened as a table in Microsoft Excel.
    - 'ICB allocation tool configuration file.json': A JavaScript Object Notation (JSON) file which can be used to re-upload your saved places into the tool at another time and return to the session you just downloaded. This is useful if you have defined many different places and want to come back to these places without having to redefine them. More information on this can be found in Step 4 in Section 5 of this guide.
    - 'ICB allocation tool documentation.txt': A plain text file with reference information on the AIF Place Based Tool, including a link to NHS England’s GitHub<sup>1</sup> repository from which the tool runs on the Streamlit<sup>2</sup> app. The GitHub repository provides further technical information on the tool.
    """, unsafe_allow_html=True)
    st.markdown("""
    ***Please Note:** The download function can only download the results (weighted populations and need indices) for the active year. Two separate downloads are needed to download both years. All that needs to be done to download the second time period is to select this year in the dropdown as explained in step 1a.*
    """)
    st.caption("""
    (1) For more information on GitHub, please refer to https://github.com/security
    \n\n(2) For more information on how Streamlit works, including information about security, please refer to https://docs.streamlit.io/streamlit-cloud/trust-and-security
    """)

with st.expander("How do I save and return to my session?"):
    st.markdown("""
    To be able to return to your session you will need the .json file described under step 3c of the “How do I download my saved places data?” section above. Alternatively, you are also able to download the .json file without downloading the full .zip, as detailed in step 4b below.
    """)
    col1, col2 = st.columns(2)

    with col1:
        st.image("images/PBTFAQ4.png", caption="Figure 4: DESCRIPTION NEEDED", width=346)

    with col2:
        st.markdown("""
            You can return to a previous session for which you downloaded result using the .json file in the .zip you downloaded, as follows:
            \n\n**4a)** On the left-hand side of the tool, below the “Save Place” button, tick “Advanced Options”.
            \n\n**4b)** The new menu that appears and has a button called “Download session data as JSON”. Click this to download just the .json save file to return to later, if you don’t want to download the full .zip file.
            \n\n**4c)** From the menu that appears, click “Browse files” and use the new window to find the file location of the .json file from a previous session that you would like to reload in the tool. Alternatively, simply drag and drop the .json save file where the tool indicates “Drag and drop file here”.
            \n\nClick “Submit” to reload the session. You should now see the saved places in the selection box at the top of the page. You can now add or delete any of your saved places if you wish.
            \n\n**4d)** You can also see the current session data (that will be downloaded in step 4b by clicking the “Show Session Data” button under the Advanced Options. This session data will then be printed out at the bottom of the main page as long as this check box is ticked.
            """)

with st.expander("Further information"):
    st.markdown("""
    Further information in support of the tool can be found in the NHS England GitHub repository docs folder: 
    \n\n REPOSITORY LINK HERE
    \n\nThis includes this user guide and a readme file with other useful information regarding this tool 
    \n\nREADME LINK HERE
    """)