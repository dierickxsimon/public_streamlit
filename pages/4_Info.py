import streamlit as st
import pandas as pd
import datetime

def predict_traffic(junction, dataset):
    return junction


with st.expander("Upload CSV with DateTime Column"):
    st.write("IMPORT DATA")
    st.write(
        "Import the time series CSV file. It should have one column labelled as 'DateTime'"
    )
    data = st.file_uploader("Upload here", type="csv")
    st.session_state.counter = 0
    if data is not None:
        dataset = pd.read_csv(data)
        

        junction = st.number_input(
            "Which Junction:", min_value=1, max_value=4, value=1, step=1, format="%d"
        )

        results = predict_traffic(junction, 'lol')
        st.write("Upload Sucessful")
        st.session_state.counter += 1
        if st.button("Predict Dataset"):
            result = results
            st.success("Successful!!!")
            st.write("Predicting for Junction", 1)
            st.write(result)

            def convert_df(df):
                # IMPORTANT: Cache the conversion to prevent computation on every rerun
                return df.to_csv().encode("utf-8")

            csv = convert_df(dataset)

            st.download_button(
                label="Download Traffic Predictions as CSV",
                data=csv,
                file_name="Traffic Predictions.csv",
                mime="text/csv",
            )
            st.session_state.counter += 1