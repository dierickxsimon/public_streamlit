import streamlit as st
from streamlit_option_menu import option_menu
from data_handler import Models
from pandas.api.types import (
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
) 
import pandas as pd
import itertools


st.set_page_config(layout="wide")
st.title('Export')


selected = option_menu(
        menu_title=None,
        options=['Oxcap', 'VOT'],
        orientation='horizontal'
    )

counter = itertools.count()

# Define your function
def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # Generate a unique key for the checkbox
    checkbox_key = f"modify_checkbox_{next(counter)}"
    modify = st.checkbox("Add filters", key=checkbox_key)

    if not modify:
        return df

    df = df.copy()

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if isinstance(df[column].dtype, pd.CategoricalDtype) or df[column].nunique() < 5:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                    key=f"{column}_multiselect"
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                    key=f"{column}_slider"
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                    key=f"{column}_date_input"
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                    key=f"{column}_text_input"
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df




    

if selected == 'Oxcap':
    model = Models.OxcapModel()
    try:
        df = model.df.drop(columns=['Full_data'])
        st.dataframe(filter_dataframe(df))
    except:
        st.write('No data to show')
    
    
if selected == 'VOT':
    model = Models.VOTModel()
    try:
        st.dataframe(filter_dataframe(model.df))
    except:
        st.write('No data to show')


col1, col2 = st.columns([1,2])
with col1:
    try:
        analysis_to_delete = st.selectbox(
            label='analysis to delete',
            options=model.df['id'],
            key="analysis_to_delete",
        )
    except:
        st.write('No data to show')

with col2:
    #for astetic reasoans
    st.write('')
    st.write('')
    if st.button('Delete'):
        try:
            model.delete_analysis(analysis_to_delete)
        except Exception as e:
            st.error(f'Something went wrong {e}')
        

     
   
if selected == 'Oxcap':
    try:
        st.write('### Export Oxcap exact Analysis')
        model = Models.OxcapModel()
        data_to_show = st.selectbox(label='Analysis to show', options=model.df['id'], key="analysis_to_show")
    
        df = model.get_excact_analysis(data_to_show)
        st.dataframe(filter_dataframe(df))
    except:
        st.write('No data to show')


           
    