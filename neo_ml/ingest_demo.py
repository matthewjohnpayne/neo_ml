'''
    Sample code to demonstrate the ingest of neo 'tracklet' data from sample data files
    
    This is *not* intended to be a complete 'how-to' guide to a full analysis ...
    ... It is just a demo of some simple methods to read the data into some numpy/pandas data structures
    
'''

# ---------------------------------------
# Third-party imports
# ---------------------------------------
import os, sys

# ---------------------------------------
# Local imports
# ---------------------------------------
import data

# ---------------------------------------
# Define some useful class(es)
# ---------------------------------------

class NEODATA():
    '''
        ...
    '''

    def __init__(self, ):
        pass
    
    def _read_from_file(self, filepath):
        '''
            Convience function to read in data from a file (after checking that the file exists)
            Data is returned in a simple list
        '''
        assert os.path.isfile(filepath), 'filepath could not be found : %r ' % filepath
        try:
            with open(filepath, 'r') as fh:
                dataList = fh.readlines()
        except:
            sys.exit('file could not be read : %r' % filepath )
        return dataList
    

    def _read_data_into_dict(self, filepath, dataType , dataKey):
        '''
            Convenience function to ...
            (i) read data from a file
            (ii) check that the data type is as expected
            (iii) return the data in an dictionary key-ed on the supplied dataKey
        '''
        # Read the data from file
        dataArray = self._read_from_file(filepath)
        
        # Get the expected data structure
        assert dataType in [data.detection_field_definitions, data.tracklet_field_definitions , data.object_field_definitions], 'dataType not recognized: %r' % dataType
        dataDefinitions = data.dataType
        
        # Check the imported data has the expected structure
        # (if not, that implies that the person that made the data file did something wrong!)
        dataList  = self._check_imported_data_structure(dataDefinitions , dataArray )
        
        # Structure the data into an appropriatedly key-ed dictionary
        # While doing this, check for uniqueness
        dataDict
        for item in dataList:
            assert item[dataKey] not in dataDict, '%s alreadt in dataDict ' % item[dataKey]
            dataDict[item[dataKey]] = item
        
        return dataDict

    def read_detection_data_into_dict(self, filepath):
        '''
            Convenience function to read detection-data into a dictionary: keyed on detID
        '''
        return self._read_data_into_dict(filepath , data.detection_field_definitions , 'detID')

    def read_tracklet_data_into_dict(self, filepath):
        '''
            Convenience function to read tracklet-data into a dictionary: keyed on trkID
        '''
        return self._read_data_into_dict(filepath , data.tracklet_field_definitions , 'trkID')

    def read_object_data_into_dict(self, filepath):
        '''
            Convenience function to read object-data into a dictionary: keyed on objectID
        '''
        return self._read_data_into_dict(filepath , data.object_field_definitions , 'objectID')

    def _check_imported_data_structure(self, dataDefinitions , dataKey, dataArray ):
        '''
            Convenience function to check whether the data in the dataArray has the correct structure
            
            N.B. We have predefined the allowed data structures in some dictionaries in the data.py file
            - We import one of these into dataDefinitions
           
        '''
        # Split into "head" & "body"
        headArray = [line for line in dataArray if '#' == line.strip()[0]]
        body      = [line for line in dataArray if '#' != line.strip()[0]]
        
        # Check that all required fields are in one of the header lines
        headerKeys = ""
        for line in headArray:
            if len([key for key in dataDefinitions if key in line]) == len(dataDefinitions):
                headerKeys = line[1:].split(",")
                assert len(headerKeys) == len(dataDefinitions), ' differing lengths ... %r ,  %r' % (headerKeys , dataDefinitions)
                break
        assert headerKeys != "", 'could not find correct header line'


        # Check body
        # Populate a dictionary with the data from the body
        dataList = []
        for line in body:
            lineSplit = line.split(",")
            # (i) check the number of fields is correct
            assert len(lineSplit) == len(dataDefinitions)
        
            # (ii) insert additional checks of content
            # ...
            
            # (iii) turn each line/row into a namedTuple
            dataList.append()
            
        return dataList


    def check_tracklet_correspondance(detDict, trkDict, objDict):
        '''
        Perform a test/check to see whether
        (a) all of the tracklet-IDs that are in the *detection* dict have corresponding entries in the *tracklet* dict (and vice-versa)
        (b) all of the tracklet-IDs that are in the *tracklet* dict have corresponding entries in the *object* dict (and vice-versa)
        '''

        # Check all of the tracklet-IDs that are in the *detection* dict have corresponding entries in the *tracklet* dict (and vice-versa)
        trkIDsFromDetectionDict = { det['trkID'] : True for det in detDict.values() }
        for trkID in trkIDsFromDetectionDict:
            assert trkID in trkDict, '%s not in trkDict' % t
        for trkID in trkDict:
            assert trkID in trkIDsFromDetectionDict, '%s not in trkIDsFromDetectionDict and hence not in detDict' % t

        # Check all of the tracklet-IDs that are in the *tracklet* dict have corresponding entries in the *object* dict (and vice-versa)
        trkIDsFromObjectDict = { det['trkID'] : True for det in objDict.values() }
        for trkID in trkIDsFromObjectDict:
            assert trkID in trkDict, '%s not in trkDict' % t
        for trkID in trkDict:
            assert trkID in trkIDsFromDetectionDict, '%s not in trkIDsFromDetectionDict  and hence not in objDict' % t


    def _check_unique(self,  array ):
        '''
            convenience function to check/assert that a supplied array has only unique values
        '''
        assert np.all(array == np.unique(array)), ' inequality implies not all entries in array are unique'
        return True


    def generate_label_dictionaries(self, detDict, trkDict, objDict):
        '''
            convenience function to use the data in the object table to label the detections (and tracklets) with the NEO status
            - i.e. as would presumably be required if one wants to use labelled data for 'training' in an ML routine
        '''
        
        # Use the objectID label in each tracklet in trkDict to query the objDict and hence attach an 'isNEO' label to the tracklet data
        trackletLabels  = { trkID : objDict[trk['objectID']]['isNEO'] for trkID, trk in trkDict.items() }

        # Use the trkID label in each detection in detDict to query the trackletLabels and hence attach an 'isNEO' label to the detection data
        detectionLabels = { detID : trackletLabels[det['trkID']]      for detID, det in detDict.items() }

        return



# ---------------------------------------
# Implement some tests/examples of data-read
# ---------------------------------------

# Define a useful NEODATA-class object to use for the ingest of data
N = NEODATA()

# (i) Read detection data into a dictionary
filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_real_observations.txt')
detDict = N.read_detection_data_into_dict(filepath)

# (ii) Read tracklet data into a dictionary
filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_real_tracklets.txt')
trkDict = N.read_tracklet_data_into_dict(filepath)

# (iii) Read object data into a dictionary
filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_real_objects.txt')
objDict = N.read_object_data_into_dict(filepath)

# (iv) Perform a test/check to see whether
# - (a) all of the tracklet-IDs that are in the *detection* table have corresponding entries in the *tracklet* table (and vice-versa)
# - (b) all of the tracklet-IDs that are in the *tracklet* table have corresponding entries in the *object* table (and vice-versa)
N.check_tracklet_correspondance(detDict, trkDict, objDict)

# (v) Use the data in the object table to label the detections (and tracklets) with the NEO status
#  - i.e. as would presumably be required if one wants to use labelled data for 'training' in an ML routine
detectionLabels , trackletLabels = N.generate_label_dictionaries()


