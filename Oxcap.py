import streamlit as st
import pandas as pd
from data_handler import data_handlers as oh
from streamlit_option_menu import option_menu
from settings import REG_THRESHOLD
import time

from front_end_components.plot import plot_with_vertical_lines, plot_oxcap_model

st.set_page_config(layout="wide")
    
st.title('Oxcap analysis')
placeholder = st.empty()

if 'oxcap_obj' not in st.session_state:
    file = placeholder.file_uploader('Oxcap_file', type=['xlsx', 'xls'])
    
if "Analysis_oxcap" not in st.session_state:
    st.session_state["Analysis_oxcap"] = False
    

if 'oxcap_obj' in st.session_state or file is not None:
    placeholder.empty()
    with st.spinner('loading data'):
        if 'oxcap_obj' not in st.session_state:
            st.session_state['oxcap_obj'] = oh.Oxcap_handler(file)
            
    
    col1, col2 = st.columns(2)

    with col1:
        st.write(f'**File used:** {st.session_state.oxcap_obj.name}')

    with col2:
        if st.button('&#10060;'):
            st.session_state.pop('oxcap_obj', None)
            st.session_state.pop('Analysis_oxcap', None)
            st.rerun()
    
    if st.session_state.oxcap_obj.markers.errors()[0] != '':
        st.warning(st.session_state.oxcap_obj.markers.errors()[0])
    
    selected = option_menu(
        menu_title=None,
        options=['Add', 'Delete'],
        icons=['plus','trash'],
        orientation='horizontal'
    )
 
    vertical_line_position = 0
 
    if selected == 'Add':
        type_marker = st.selectbox('Type of marker', st.session_state.oxcap_obj.markers.types_of_markers)
        vertical_line_position = st.number_input('Vertical Line Position', min_value=st.session_state.oxcap_obj.min(), max_value=st.session_state.oxcap_obj.max(), value=0, step=5)
        if st.button("Add Marker", key="add_line"):
            st.session_state.oxcap_obj.markers.markers = {vertical_line_position: type_marker}
            st.session_state['Analysis'] = False
            
    
    if selected == 'Delete': 
        marker_to_delete = st.selectbox('marker to delete', st.session_state.oxcap_obj.markers.markers.values())
        if st.button('DELETE MARKER', key='delete_marker'):
            st.session_state.oxcap_obj.markers.delete_marker(marker_to_delete, based_on_marker=True)
            st.session_state['Analysis'] = False
            
   
    def fig():    
        fig = plot_with_vertical_lines(vertical_line_position, st.session_state.oxcap_obj)
        st.plotly_chart(fig, use_container_width=True ,width=10000)
    
    placeholder_fig = st.empty()
    with placeholder_fig.container():
        fig()
    analysis_to_use = st.selectbox('Wich data to use for the analysis', ['ALL'] + [marker for marker in st.session_state.oxcap_obj.markers.markers.values() if marker.startswith('S')])
    padding = st.number_input("padding after A and before B for the slope calulculation", min_value=0, max_value=20, value=10, step=1)
    
    if st.button('Analyse'):
        st.session_state["Analysis_oxcap"] = True
        
    if st.session_state["Analysis_oxcap"]:
        if st.session_state.oxcap_obj.markers.errors()[1] !=0:
            st.error('Please solve the errors')
        
        else:
            data = st.session_state.oxcap_obj.fit(analysis_to_use, padding=padding)
            fig_model = plot_oxcap_model(st.session_state.oxcap_obj)  
               
            st.write(f"""
                - **$y_{{end}}$:** {data['Y_end']:.4f} &plusmn; {data['Y_end_std']:.4f}\n
                - **$A$:** {data['A']:.4f} &plusmn; {data['A_std']/2:.4f}\n
                - **$τ$:** {data['Tau']:.4f} &plusmn; {data['Tau_std']/2:.4f}\n
                - **$R²$:** {data['R²']:.4f}\n
                    """)
            st.plotly_chart(fig_model, use_container_width=True ,width=10000)

    
            if st.button('Upload', key='upload_button'):
                mesg = st.session_state.oxcap_obj.upload()
                if mesg == 'Success':
                    st.success(f'Upload was successful! Reloading in 3s...')
                    st.session_state.pop('oxcap_obj', None)
                    st.session_state.pop('Analysis_oxcap', None)
                    time.sleep(2.3) 
                    st.rerun()
                else:
                    st.error(f'Something went wrong with uploading: {mesg}')
            

            
    
    
    
    