import pandas as pd
import numpy as np
import re
from abc import ABC, abstractmethod

import statsmodels.api as sm

from .markers import Oxcap_Markers, VOT_markers
from .utils import regression, non_linear_fit
from .Models import OxcapModel, VOTModel


from settings import SAMPLING_FREQUENCY


class Data_handler(ABC):
    def __init__(self, file, name) -> None:
        self.df_raw = self.__file_reader(file)
        self._analysis_based_on = self._analysis_based_on = 'Rx1-Tx1,Tx2,Tx3 TSI% '
        
        #for jupyter notebooks
        if name == None:
            self.name = file.name.split('.')[0]
        else:
            self.name = name
    
    
    def df_to_analyse(self, start_idx, end_idx):
        df = pd.DataFrame()
        df[self.analysis_based_on] = self.df_raw[self.analysis_based_on].iloc[start_idx:end_idx+1]
        df['time'] = np.linspace(0, len(df) / SAMPLING_FREQUENCY, len(df))
        df_marker = pd.DataFrame.from_dict(self.markers.markers, orient='index').rename(columns={0: '(Event)'})
        result_df = df.join(df_marker, how='left')  
        return result_df
                
    @property 
    def analysis_based_on(self):
        return self._analysis_based_on
      
    @analysis_based_on.setter
    def analysis_based_on(self, name):
        if name not in self.df_raw.columns:
            raise KeyError('Column selected for the analysis does not exist')
        self._analysis_based_on = name
        
    def __file_reader(self, file):
        column_names = pd.read_excel(file, skiprows=34, usecols='A:B')[:16]
        column_names_dict = dict()
        for _, row in column_names.iterrows():
            if row['Trace (Measurement)'] not in ['(Sample number)', '(Event)']:
                pattern = r'\([^()]*\)'
                column_name = re.sub(pattern, '', row['Trace (Measurement)'])
            else:
                column_name = row['Trace (Measurement)']
                
            column_names_dict[row['Column']] = column_name
            
        df_raw = pd.read_excel(file, skiprows=52)
        df_raw = df_raw.rename(columns = column_names_dict,)
        return df_raw
       
    
    @abstractmethod
    def fit(self):
        return self.data
    
    def upload(self):
        if self.data:
            try:
                self.model.create_analysis(self.data)
                return 'Success'
            except Exception as e:
                return f'uploaded failed something wrong with the database {e}'
        return 'no data to upload'
    
    def min(self):
        return self.df_raw['(Sample number)'].min()
    
    def max(self):
        return self.df_raw['(Sample number)'].max()
    
    
    
    
class Oxcap_handler(Data_handler):
    def __init__(self, file, name=None) -> None:
        super().__init__(file, name)
        self.markers = Oxcap_Markers(self.df_raw)
        self.model = OxcapModel()
    
    def fit(self, data_selector, padding=10):
        start_markers = self.markers.filter_markers('S')
        end_markers = self.markers.filter_markers('E')
        _, critical_errors = self.markers.errors()
        
        if critical_errors >0:
            return None
        
        
        df_list = []
        if data_selector == 'ALL':
            for k, v in start_markers.items():
                 for k2,v2 in end_markers.items():
                     if v[1]==v2[1]:
                        df_list.append((self.df_to_analyse(k, k2),v))               
        else:
            for k, v in start_markers.items():
                if v == data_selector:
                    for k2,v2 in end_markers.items():
                        if v[1]==v2[1]:
                            df_list.append(((self.df_to_analyse(k, k2)),v))
            
        result = list()
        for df, v in df_list:
            reg_results, _  = regression(df, self.analysis_based_on, v, padding)
            result.append(pd.DataFrame(reg_results))   
            
                
        df = pd.concat(result)
        if len(df) == 0:
            return None

        #this need to be changed in the future
        popt, perr, R2, self.outliers, self.df_analysis = non_linear_fit(df)
        
    
        self.data = {
            'id':self.name,
            'Project':self.name.split('_')[0],
            'pp':self.name.split('_')[1],
            'type': '_'.join(self.name.split('_')[2:]),
            'Y_end': popt[0],
            'Y_end_std': perr[0],
            'A':popt[1],
            'A_std':perr[1],
            'Tau':popt[2],
            'Tau_std':perr[2],
            'R²':R2,
            'Analysis_on':data_selector,
            'Full_data':self.df_analysis.to_dict(orient='list'),
        }
        return self.data
            

    
    
class VOT_handler(Data_handler):
    def __init__(self, file, name=None) -> None:
        super().__init__(file, name)
        self.markers = VOT_markers(self.df_raw)
        self.model = VOTModel()
        
    def fit(self, slope_delay=10):
        _, critical_errors = self.markers.errors()
        
        if critical_errors >0:
            return None
        
        #30-s average before occlusion
        oclusion_mark = list(self.markers.filter_markers('O').keys())[0]
        base_line_stO2 = self.df_to_analyse(oclusion_mark-300, oclusion_mark)[self.analysis_based_on].mean()
        
        #downslope of the ST02 singal over a 300-s period immediately after cuff inflation
        df_occ = self.df_to_analyse(oclusion_mark, oclusion_mark+3000)
        min_value_occ = df_occ[self.analysis_based_on].min()
        Y = df_occ[self.analysis_based_on]
        x = sm.add_constant(df_occ['time'])
        slope_occlusion = sm.OLS(Y, x).fit().params.iloc[1]
        
        #Microvascular responsiveness
        #slope of 10s after cuff release 
        releasse_mark = list(self.markers.filter_markers('R').keys())[0]
        df_slope_release = self.df_to_analyse(releasse_mark, releasse_mark+100)
        Y = df_slope_release[self.analysis_based_on]
        x = sm.add_constant(df_slope_release['time'])
        slope_release = sm.OLS(Y,x).fit().params.iloc[1]
        
        #all values after release
        df_release = self.df_to_analyse(releasse_mark+slope_delay, releasse_mark+1200)
        max_st02 = df_release[self.analysis_based_on].max()
        i = df_release[self.analysis_based_on].idxmax()
        time_till_max = df_release.loc[i, 'time']
        
        #AUC
        df_release[self.analysis_based_on] -= base_line_stO2
        positive_values = df_release[df_release[self.analysis_based_on] > 0][self.analysis_based_on]
        auc = positive_values.sum()
        
    
        self.data = {
            'id':self.name,
            'Project':self.name.split('_')[0],
            'pp':self.name.split('_')[1],
            'type': '_'.join(self.name.split('_')[2:]),
            'Base_line_StO2': base_line_stO2,
            'slope_occlusion': slope_occlusion,
            'slope_release':slope_release,
            'Max_stO2':max_st02,
            'min_stO2': min_value_occ,
            'time_to_max':time_till_max,
            'stO2_amp':max_st02-min_value_occ,
            'AUC': auc,
        }
        return self.data
     
 