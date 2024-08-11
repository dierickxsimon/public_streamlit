import pandas as pd
from pymongo import MongoClient
import streamlit as st


password = st.secrets['MONGO_DB_PWD']
database_name = st.secrets['MONGO_DB_NAME']
mongo_uri = st.secrets['MONGO_URI']

class Model:
    def __init__(self):
        self.client = MongoClient(mongo_uri)
        self.db = self.client[database_name]
        
    @property    
    def df(self):
        df = pd.DataFrame(list(self.collection.find()))
        df = df.drop('_id', axis=1)
        return df
        
    def delete_analysis(self, analysis_id):
        result = self.collection.delete_one({"id": analysis_id})
        return result.deleted_count > 0
    
    def get_analysis(self, analysis_id):
        return self.collection.find_one({"id": analysis_id})
    
    def create_analysis(self, analysis_data):
        if self.collection.find_one({'id': analysis_data['id']}) and not self.collection.count_documents({}) == 0:
            raise ValueError('file id already exists')
        result = self.collection.insert_one(analysis_data)
        return result.inserted_id
    
    def get_excact_analysis(self, analysis_id):
        data = self.get_analysis(analysis_id)
        return pd.DataFrame(data['Full_data'])
        
class OxcapModel(Model):
    def __init__(self):
        super().__init__()
        self.collection = self.db['Oxcap']

    
class VOTModel(Model):
    def __init__(self):
        super().__init__()
        self.collection = self.db['VOT']


    




