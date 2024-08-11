from typing import Any
from settings import SAMPLING_FREQUENCY

class Markers:
    def __init__(self, df, types_of_markers) -> None:
        self._markers = {}
        self.types_of_markers = types_of_markers
        self.compute_markers(df)
        
        
            
    def compute_markers(self, df):
        for marker in self.types_of_markers:
            idxs = df[df['(Event)'].str.startswith(marker, na=False)].index 
            counter = 1
            for i in idxs:
                self._markers[i] = marker + str(counter)
                counter += 1
    @property
    def markers(self):
        return dict(sorted(self._markers.items()))
    
    
    def filter_markers(self, value:str|list):
        if isinstance(value, str):
            if value not in self.types_of_markers:
                raise KeyError('Value not in markers')
            return dict(sorted({k:v for k, v in self.markers.items() if v.startswith(value)}.items()))
        
        if isinstance(value, list):
            result = {}
            for v in value:
                result.update(self.filter_markers(v))
            return dict(sorted(result.items()))
    
    
    
    @markers.setter
    def markers(self, markers: dict|list):
        if isinstance(markers, dict):
            self._markers.update(markers)
            self._sort_markers()
        elif isinstance(markers, list):
            for marker in markers:
                self.markers = marker
        else:
            raise TypeError(f'expexted dict or list but {type(markers)} was given')
        
    def _sort_markers(self):
        for marker in self.types_of_markers:
            counter = 1
            for i, marker_to_change in self.markers.items():
                if marker != marker_to_change[0]:
                    continue
                self._markers[i] = marker + str(counter)
                counter +=1
                
    def find_idx(self, value):
        for k, v in self.markers.items():
            if v == value:
                return k
                
    def delete_marker(self, idx, based_on_marker=False):
        if based_on_marker:
            idx = self.find_idx(idx)
        del self._markers[idx]
        self._sort_markers()
    
    
    def __getitem__(self, index):
        if isinstance(index, list):
            return [self._markers[i] for i in index]
        else:
            return self._markers[index]
    
    
    
class Oxcap_Markers(Markers):
    def __init__(self, df) -> None:
        types_of_markers = ['A', 'B', 'E', 'K', 'S']
        super().__init__(df, types_of_markers)
            
    def errors(self):
        error = ""
        number_of_critical_errors = 0
        
        def add_str(string:str):
            nonlocal error
            error = error + '- ' + string + '\n'
        
        number_of_start_mark = len(self.filter_markers('S'))
        number_of_end_mark = len(self.filter_markers('E'))
        
        if number_of_start_mark  == 0:
            add_str('No Starting Markers found')
            number_of_critical_errors += 1
        elif number_of_end_mark == 0:
            add_str('No ending Markers found')
            number_of_critical_errors += 1  
        elif number_of_start_mark != number_of_end_mark:
            k = number_of_start_mark - number_of_end_mark
            if k < 0:
                add_str(f'{abs(k)} starting markers missing')
                number_of_critical_errors += 1
            else:
                add_str(f'{abs(k)} ending markers missing')
                number_of_critical_errors += 1
        
        prev_v = 'Z'
        prev_k = 0
        list_of_missing=[]  
        for k, v in self.markers.items():
            if v[0] == 'S':
                prev_v = v[0]
                prev_k = k
                continue
            elif v[0] == prev_v[0]:
                    list_of_missing.append(v)
                    number_of_critical_errors += 1
                    
            elif v[0] == 'A' and prev_v[0] == 'S':
                time = k - prev_k
                if time < SAMPLING_FREQUENCY* 3.5:
                    add_str(f'Distance between {v} and {prev_v} marker to small')
                elif time > SAMPLING_FREQUENCY* 6:
                    add_str(f'Distance between {v} and {prev_v} marker to Big')
                    
            elif v[0] == 'A' and prev_v[0] == 'B':
                time = k - prev_k
                if time < SAMPLING_FREQUENCY* 8.5:
                    add_str(f'Distance between {v} and {prev_v} to small')
                elif time > SAMPLING_FREQUENCY* 11.5:
                    add_str(f'Distance between {v} and {prev_v} to Big')
                    
            
            elif v[0] == 'B' and prev_v[0] == 'A':
                time = k - prev_k
                if time < SAMPLING_FREQUENCY* 3.5:
                    add_str(f'Distance between {v} and  {prev_v} to small')
                elif time > SAMPLING_FREQUENCY* 6.5:
                    add_str(f'Distance between {v} and  {prev_v} to Big')
                    
            elif v[0] == 'B' and prev_v[0] == 'E':
                time = k - prev_k
                if time < SAMPLING_FREQUENCY* 8.5:
                    add_str(f'Distance between {v} and {prev_v} to small')
                elif time > SAMPLING_FREQUENCY* 11.5:
                    add_str(f'Distance between {v} and {prev_v} to Big')
                   
            prev_v = v
            prev_k = k
            
        if len(list_of_missing) >0:
            add_str(f'following markers are missing {list_of_missing}')
            number_of_critical_errors += 1
        
        return error, number_of_critical_errors
            

class VOT_markers(Markers):
    def __init__(self, df) -> None:
        types_of_markers = ['B', 'E', 'O', 'R']
        super().__init__(df, types_of_markers)
        
            
    def errors(self):
        error = ""
        number_of_errors = 0
        def add_str(string:str):
            nonlocal error
            error = error + '- ' + string + '\n'
        
        for marker in self.types_of_markers:    
            number_of_markers = len(self.filter_markers(marker))
            if number_of_markers == 0:
                add_str(f'{marker} is missing')
                number_of_errors +=1
                
            if number_of_markers >1:
                add_str(f'To many {marker} markers')
                number_of_errors +=1
            
        return error, number_of_errors