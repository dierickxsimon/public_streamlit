import streamlit as st
from streamlit_option_menu import option_menu

import pandas as pd
import time

from data_handler import data_handlers as oh
from front_end_components.plot import plot_with_vertical_lines

st.set_page_config(layout="wide")
    
st.title('VOT analysis')
placeholder = st.empty()

if 'VOT_obj' not in st.session_state:
    file = placeholder.file_uploader('VOT_file', type=['xlsx', 'xls'])
    
if "Analysis" not in st.session_state:
    st.session_state["Analysis"] = False
    


if 'VOT_obj' in st.session_state or file is not None:
    placeholder.empty()
    with st.spinner('loading data'):
        if 'VOT_obj' not in st.session_state:
            st.session_state['VOT_obj'] = oh.VOT_handler(file)
            
    
    col1, col2 = st.columns(2)

    with col1:
        st.write(f'**File used:** {st.session_state.VOT_obj.name}')

    with col2:
        if st.button('&#10060;'):
            st.session_state.pop('VOT_obj', None)
            st.session_state.pop('Analysis', None)
            st.rerun()
    
    if st.session_state.VOT_obj.markers.errors()[0] != '':
        st.warning(st.session_state.VOT_obj.markers.errors()[0])
    
    selected = option_menu(
        menu_title=None,
        options=['Add', 'Delete'],
        icons=['plus','trash'],
        orientation='horizontal'
    )
 
    vertical_line_position = 0
 
    if selected == 'Add':
        type_marker = st.selectbox('Type of marker', st.session_state.VOT_obj.markers.types_of_markers)
        vertical_line_position = st.number_input('Vertical Line Position', min_value=st.session_state.VOT_obj.min(), max_value=st.session_state.VOT_obj.max(), value=0, step=5)
        if st.button("Add Marker", key="add_line"):
            st.session_state.VOT_obj.markers.markers = {vertical_line_position: type_marker}
            st.session_state['Analysis'] = False
       
    if selected == 'Delete': 
        marker_to_delete = st.selectbox('marker to delete', st.session_state.VOT_obj.markers.markers.values())
        if st.button('DELETE MARKER', key='delete_marker'):
            st.session_state.VOT_obj.markers.delete_marker(marker_to_delete, based_on_marker=True)
            st.session_state['Analysis'] = False
        
    
    fig = plot_with_vertical_lines(vertical_line_position, st.session_state.VOT_obj)
    st.plotly_chart(fig, use_container_width=True ,width=10000)
    delay = st.number_input("delay after R for the slope calulculation", min_value=0, max_value=100, value=10, step=10)
   
    if st.button('Analyse'):
        st.session_state['Analysis'] = True
        
    if st.session_state['Analysis']:
        if st.session_state.VOT_obj.markers.errors()[1] !=0:
                st.error('please solve the errors')
        else:
            result = st.session_state.VOT_obj.fit(slope_delay=delay) 
            st.write(pd.DataFrame(result, index=[0]).drop(columns=['type', 'id', 'Project', 'pp']))
    
            if st.button('Upload', key='upload_button'):
                mesg = st.session_state.VOT_obj.upload()
                if mesg == 'Success':
                    st.success(f'Upload was successful! Reloading in 3s...')
                    st.session_state.pop('VOT_obj', None)
                    st.session_state.pop('Analysis', None)
                    time.sleep(2.0) 
                    st.rerun()
                else:
                    st.error(f'Something went wrong with uploading: {mesg}')
                

            
    
    
    
    