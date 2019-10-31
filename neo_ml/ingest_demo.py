'''
    Sample code to demonstrate the ingest of neo 'tracklet' data from sample data files
    Intended for machine learning class with C. Nugent @ Olin
    October 2019
    
    This is *not* intended to be a complete 'how-to' guide to a full analysis ...
    ... It is just a demo of some simple methods to read the data into some numpy/pandas data structures
    
'''

# ---------------------------------------
# Third-party imports
# ---------------------------------------
import os, sys
from collections import namedtuple
import re

# ---------------------------------------
# Local imports
# ---------------------------------------
import data

# ---------------------------------------
# Define some useful class(es)
# ---------------------------------------

class NEODATA():
    '''
        Convenience class used to demonstrate how to read, check & use the sample data 
        It is expected that this class would need to be extended in order to allow a full data analysis
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
    

    def _read_data_into_dict(self, filepath, fieldDefinitions , dataKey):
        '''
            Convenience function to ...
            (i) read data from a file
            (ii) check that the data type is as expected
            (iii) return the data in an dictionary key-ed on the supplied dataKey
        '''
        # Read the data from file
        dataArray = self._read_from_file(filepath)
        
        # Get the expected data structure
        assert fieldDefinitions in [data.detection_field_definitions, data.tracklet_field_definitions , data.object_field_definitions], 'fieldDefinitions not recognized: %r' % fieldDefinitions
        
        # Check the imported data has the expected structure
        # (if not, that implies that the person that made the data file did something wrong!)
        headerKeys, dataList  = self._check_imported_data_structure(fieldDefinitions , dataKey, dataArray )
        
        # Structure the data into an appropriatedly key-ed dictionary
        # While doing this, check for uniqueness
        dataDict = {}
        for n, item in enumerate(dataList):
            d = dict(zip(headerKeys, item))
            assert d[dataKey] not in dataDict, '%s already in dataDict (line %d reading from %s)' % (d[dataKey], n, filepath)
            dataDict[d[dataKey]] = d
        
        print('\n _read_data_into_dict successfuly imported data from %s' % filepath)
        
        return dataDict

    def read_detection_data_into_dict(self, filepath):
        ''' Convenience function to read detection-data into a dictionary: keyed on detID'''
        return self._read_data_into_dict(filepath , data.detection_field_definitions , 'detID')

    def read_tracklet_data_into_dict(self, filepath):
        '''Convenience function to read tracklet-data into a dictionary: keyed on trkID'''
        return self._read_data_into_dict(filepath , data.tracklet_field_definitions , 'trkID')

    def read_object_data_into_dict(self, filepath):
        '''Convenience function to read object-data into a dictionary: keyed on objectID'''
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
                headerKeys = [_.strip() for _ in line[1:].split(",") ]
                assert len(headerKeys) == len(dataDefinitions), ' differing lengths ... %r ,  %r' % (headerKeys , dataDefinitions)
                break
        assert headerKeys != "", 'could not find correct header line in ... \n \t %r ' % dataDefinitions

        # Check body
        # Populate a dictionary with the data from the body
        dataList = []
        for line in body:
            
            # split the line "intelligently":
            # - look for content inside "[ ... ]" as well as splitting on commas
            lineSplit = self._split_intelligently(line)
            
            # (i) check the number of fields is correct
            if dataKey != 'trkID':
                assert len(lineSplit) == len(dataDefinitions), 'dataKey'
        
            # (ii) insert additional checks of content
            # ...
            
            # (iii) append into list
            dataList.append( lineSplit )
            
        #print('\n _check_imported_data_structure executed successfully')
        return headerKeys, dataList

    def _split_intelligently(self, line):
        '''
            # - look for content inside "[ ... ]" as well as splitting on commas
        '''
        if "[" in line:
            
            # find positions of []
            left  = [m.start() for m in re.finditer('\[', line.strip())]
            right = [m.start() for m in re.finditer('\]', line)]
            
            # identify the different "portions" of the string, and label them as to whether they are within a bracket region "[ ... ]" or not
            # (i) starting region ...
            regions            = [ (0, left[0]) ]
            region_is_bracket  = [ False ]
            # (ii) bracket regions ...
            for l,r in zip( left, right ):
                regions.append( (l,r+1) )
                region_is_bracket.append( True )
            # (iii) gaps between the brackets
            for r,l in zip(right[:-1],left[1:]):
                regions.append( (r+1,l) )
                region_is_bracket.append( False )
        
            # Ensure the regions are sorted
            regions, region_is_bracket = zip(*sorted(zip(regions, region_is_bracket)))

            # split the regions on commas is they are a non-bracket region
            lineSplit = []
            for region, is_bracket in zip(regions, region_is_bracket):
                regionStr = line[region[0]:region[1]]
                if is_bracket:
                    lineSplit.append(regionStr)
                else:
                    # getting rid of any gap regions which contain ONLY commas/blank-spaces
                    tmp_ = [_.replace(' ','') for _ in regionStr.split(",") if _.replace(' ','') != '']
                    if len(tmp_):
                        lineSplit.extend(tmp_)
        else:
            # Just do a simple split based on commas
            lineSplit = [_.strip() for _ in line.split(",") ]
        return lineSplit

    def check_tracklet_correspondance(self, detDict, trkDict, objDict):
        '''
        Perform a test/check to see whether
        (a) all of the tracklet-IDs that are in the *detection* dict have corresponding entries in the *tracklet* dict (and vice-versa)
        (b) all of the tracklet-IDs that are in the *tracklet* dict have corresponding entries in the *object* dict (and vice-versa)
        '''

        # Check all of the tracklet-IDs that are in the *detection* dict have corresponding entries in the *tracklet* dict (and vice-versa)
        trkIDsFromDetectionDict = { det['trkID'] : True for det in detDict.values() }
        for trkID in trkIDsFromDetectionDict:
            assert trkID in trkDict, '%s not in trkDict' % trkID
        for trkID in trkDict:
            assert trkID in trkIDsFromDetectionDict, '%s not in trkIDsFromDetectionDict and hence not in detDict' % trkID

        # Check all of the object-IDs that are in the *tracklet* dict have corresponding entries in the *object* dict (and vice-versa)
        objectIDsFromTrackletDict = { trk['objectID'] : True for trk in trkDict.values() }
        cntNOT, cntIN = 0,0
        for objectID in objectIDsFromTrackletDict:
            #assert objectID in objDict, '%s (from TrackletDict) not in objDict' % objectID
            if objectID not in objDict:
                cntNOT +=1
                print( '%s (from TrackletDict) not in objDict' % objectID)
            else:
                cntIN += 1
                print(objectID , ' in as desired ...')
        print(cntNOT, cntIN)
        for objectID in objDict:
            assert objectID in objectIDsFromTrackletDict, '%s not in objectIDsFromTrackletDict and hence not in trkDict' % objectID

        print("\n check_tracklet_correspondance successfully executed")

    def _check_unique(self,  array ):
        '''convenience function to check/assert that a supplied array has only unique values'''
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

        print("\n generate_label_dictionaries successfully executed ")
        return trackletLabels, detectionLabels



# ---------------------------------------
# Implement some tests/examples of data-read
# ---------------------------------------

# Define a useful NEODATA-class object to use for the ingest of data
N = NEODATA()

# ----------- SELECT SOURCE FILE LENGTH ----
numberString = '1e6'

# (i) Read detection data into a dictionary
filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_%s_real_detections.csv' % numberString)
detDict = N.read_detection_data_into_dict(filepath)
print(' There are %d unique detections' % len(detDict))
d=detDict; key0 = list(d.keys())[0]; print("An example detection looks like ...\n", key0, d[key0])

# (ii) Read tracklet data into a dictionary
filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_%s_real_tracklets.csv' % numberString)
trkDict = N.read_tracklet_data_into_dict(filepath)
print(' There are %d unique tracklets' % len(trkDict))
d=trkDict; key0 = list(d.keys())[0]; print("An example tracklet looks like ...\n", key0, d[key0])

# (iii) Read object data into a dictionary
filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_%s_real_objects.csv' % numberString)
objDict = N.read_object_data_into_dict(filepath)
print(' There are %d unique objects' % len(objDict))
d=objDict; key0 = list(d.keys())[0]; print("An example object looks like ...\n", key0, d[key0])

# (iv) Perform a test/check to see whether
# - (a) all of the tracklet-IDs that are in the *detection* table have corresponding entries in the *tracklet* table (and vice-versa)
# - (b) all of the tracklet-IDs that are in the *tracklet* table have corresponding entries in the *object* table (and vice-versa)
N.check_tracklet_correspondance(detDict, trkDict, objDict)

# (v) Use the data in the object table to label the detections (and tracklets) with the NEO status
#  - i.e. as would presumably be required if one wants to use labelled data for 'training' in an ML routine
trackletLabels, detectionLabels = N.generate_label_dictionaries(detDict, trkDict, objDict)
print("len(detectionLabels)", len(detectionLabels))
print("len(trackletLabels) ", len(trackletLabels))
for trk in trkDict:
    print("trkID=%20s :\t isNEO = %6s " % (trk, trackletLabels[trk]) )

