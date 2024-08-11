import numpy as np 
import pandas as pd
from scipy.optimize import curve_fit 
import statsmodels.api as sm


from .markers import Oxcap_Markers 

from settings import REG_THRESHOLD, OUTLIER_THRESHOLD     

def regression(df_raw, based_on, type_analysis, padding):      
    regression_container = {
        'time':[],
        'B1':[],
        'B0': [],
        'R2':[],
        'type':[]
    }
    
    markers_failed = list()
    
    markers = Oxcap_Markers(df_raw)
    
    
    
    start_markers = list(markers.filter_markers(['A', 'S']).keys())
    end_markers = list(markers.filter_markers(['E', 'B']).keys())
    time = 0
    prev_time = start_markers[0]
    for i, (start_i, end_i) in enumerate(zip(start_markers, end_markers)):
        df = df_raw.loc[start_i+padding:end_i-padding]
        Y = df[based_on]
        X = sm.add_constant(df['time'])
        try:
            if i >0:
                time += (start_i - prev_time)
                
            model = sm.OLS(Y,X)
            results = model.fit()
            regression_container['B1'].append(results.params.iloc[1])
            regression_container['B0'].append(results.params.iloc[0])
            regression_container['R2'].append(results.rsquared)
            regression_container['time'].append(time/10)
            regression_container['type'].append(type_analysis)
                
            
            prev_time = start_i
            
        except:
            markers_failed.append((start_i, end_i))
      
    return regression_container, markers_failed


def model(time, y_end, a, tau):
    return y_end - a * np.exp(-time / tau)

def non_linear_fit(regression_container):
    outliers = None
    if isinstance(regression_container, dict):
        df = pd.DataFrame(regression_container)
    else:
        df = regression_container.copy()
    
    bounds = ([-np.inf, 0, 10], [0,np.inf,np.inf])
    popt, pcov = curve_fit(model, df['time'], df['B1'], bounds=bounds,method='trf')
    perr = np.sqrt(np.diag(pcov))
    
    
    df['residuals'] = df['B1'] - model(df['time'], *popt)
    ss_res = np.sum(df['residuals']**2)
    ss_tot = np.sum((df['B1'] - df['B1'].mean())**2)
    R2 = 1 - (ss_res / ss_tot)
    
    df['Z-scores'] = ((df['residuals'] - df['residuals'].mean()) / df['residuals'].std()).abs()
    if df['Z-scores'].max() >OUTLIER_THRESHOLD:
        outliers = df[df['Z-scores'] >OUTLIER_THRESHOLD]
        popt, perr, R2, new_outliers, df = non_linear_fit(df[df['Z-scores']<OUTLIER_THRESHOLD])
        outliers = pd.concat([outliers, new_outliers])

        
    return popt, perr, R2, outliers, df

def create_graph(popt, x):
    y = model(x, popt[0], popt[1], popt[2])
    return x,y
    
        