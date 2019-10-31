'''
    October 2019
    
    This code is/was used by M.Payne to help create the sample data in neo_ml/neo_ml/sample_data
     - This mainly involves the reformatting of data from standard formats used at the MPC to formats likely to be of more use in an ML investigation
    
    The main value of this script will be as a record of the steps involved in the necessary data-wrangling
     
    It is not expected that this will be used as part of the central machine-learning investigation
     - And some functionality may be dependent on internal MPC data-sources / code that is not supplied within this neo_ml repo
     - As such, it should be assumed that 'sample_data_creation.py' will not work for external users
'''

# ----------------------------------------
# Third-party imports
# ----------------------------------------
import os, sys
import numpy as np
from collections import namedtuple

# ----------------------------------------
# Local imports
# ----------------------------------------
import data
from obs80 import obs80 as o
import MPC_library as MPCL
import phys_const as PHYS

# ----------------------------------------
# Define some useful class(es)/function(s)
# ----------------------------------------

# Consider the following few designations selected from mpcweb2:
#>>> head /share/tracklets/products/neo2017
#>>> 2K17A13G 100 100
#>>> 2K17B03M 100 100
#>>> head /share/tracklets/products/nonneo2017
#>>> 0K17A01J 7 7
#>>> 0K17A00Z 7 7


# May need to convert to GW's idiotic version of designation
#>>> mpc_convert.convert_packed_prov_desig('K17A13G')
#'K17A00013G'
#>>> mpc_convert.convert_packed_prov_desig('K17B03M')
#'K17B00003M'
#>>> mpc_convert.convert_packed_prov_desig('K17A01J')
#'K17A00001J'
#>>> mpc_convert.convert_packed_prov_desig('K17A00Z')
#'K17A00000Z'


# Look in psql at the observations
#vmsops=# \copy (select provid_pkd,obsID,trkID,obs80 from obs where provid_pkd in ('K17A00013G','K17B00003M','K17A00001J','K17A00000Z') order by provid_pkd) to '/home/mpayne/sample_obs.csv' csv header;


# Look in psql at the orbits
# vmsops=# \copy ( select desig_pkd, peri_dist, eccentricity, incl, arg_peri, asc_node, peri_time from orbits where desig_pkd in ('K17A00013G','K17B00003M','K17A00001J','K17A00000Z') order by desig_pkd) to '/home/mpayne/sample_orbit.csv' csv header;

# Set up a function to process the selected input data ...
def _read_from_file(filepath):
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

def angle_unitvectors(uv1,uv2):
    '''
        Calculate the angle between two unit vectors
        Returns angle in radians
        '''
    # Check the format is as required
    assert (uv1.shape == (3,) or uv1.shape == (1,3)), 'The behavior of this routine has only been tested when uv1 is a single unit vector'
    assert (uv2.shape == (3,) or uv2.shape[1] ==3 )
    
    # Do the dot-products to get the angle
    uv1.flatten()
    uv2 = np.atleast_2d(uv2)
    dot = np.dot( uv1,uv2.T )
    
    # Return results in radians
    return np.arccos( dot )

def radec_to_unitvector_equatorial(RA_deg, DEC_deg):
    return np.transpose(np.array([  np.cos(np.radians(RA_deg))*np.cos(np.radians(DEC_deg)),
                                  np.sin(np.radians(RA_deg))*np.cos(np.radians(DEC_deg)),
                                  np.sin(np.radians(DEC_deg))]))

def unitvector_equatorial_to_unitvector_ecliptic(unitvector_equatorial):
    return np.dot(np.transpose(PHYS.rot_mat), unitvector_equatorial )

# Useful functions related to position of the observatory at the time the pointing was taken ...
# ... this is EQUATORIAL
def calc_heliocentric_position_of_observatory_in_equatorial_coords(obsCode, JDutc):
    helio_eq_posn = MPCL.Observatory().getObservatoryPosition(obsCode, JDutc)
    return helio_eq_posn

def calc_heliocentric_position_of_observatory_in_ecliptic_coords(helio_eq_posn):
    helio_ec_posn = np.dot(np.transpose(PHYS.rot_mat), helio_eq_posn )
    return helio_ec_posn


def _process_detections(dataList, numberString, dict_of_Strings_keyed_on_orbitID):
    '''
        We are reading data that was created from a query of the mpc obs-table in the postgres database ...
        
        The contents of dataList look like ...
        provid_pkd,obsid,trkid,obs80
        K17A00000Z,L1UJng000000Crte0100001m7,00000VF-fh,     K17A00Z 5C2014 04 28.98950 13 24 42.05 -19 38 29.3                L~2ClrW84
        
        
        dict_of_Strings_keyed_on_orbitID was created by _process_orbits
    '''
    
    # data containers
    detDict = {}
    trkDict = {}
    orbitID_Dict = {}
    outputListOfStringsForDetections,outputListOfStringsForTracklets, outputListOfStringsForTrackletsHeader  = [], [], []
    
    # create the header line & append it to the output container
    detectionKeys = sorted(data.detection_field_definitions.keys())
    outputListOfStringsForDetections.append("# " + " , ".join( detectionKeys ))
    print(outputListOfStringsForDetections)

    trackletKeys = sorted(data.tracklet_field_definitions.keys())
    outputListOfStringsForTrackletsHeader.append("# " + " , ".join( trackletKeys ))
    print(outputListOfStringsForTrackletsHeader)
    countTrkIDs = 0
    
    prev_trkID = ''
    for l,line in enumerate(dataList):
        totLen=len(dataList)
        if len(line) < 150 :
            
            # immediately try to split the line & parse the obs80 part and use this as a guage of success
            try:
                orbitID, detID, trkID, obs80 = line.split(',')
                obs80 = o.parseOpt(obs80)
                detDict['detID'] = detID
                detDict['trkID'] = trkID
              
                PROCEED = True
            except:
                PROCEED = False
            
            
            if PROCEED :
                
                
                # At this point we know the orbitID, so we will only both to proceed if the orbitID is contained in ...
                # ... the dict_of_Strings_keyed_on_orbitID created by _process_orbits
                if orbitID in dict_of_Strings_keyed_on_orbitID:


                    # --- TRACKLET-LEVEL QUANTITIES ------------------
                    # look for new trkIDs so that we know when it is a good time to periodically write
                    if trkID != prev_trkID:
                        countTrkIDs +=1
                        
                        # arbitrarily choose to write-out every 1000 tracklets
                        critCount = 100
                        if countTrkIDs % critCount == 0 :
                            print(" ... l=%15d, countTrkIDs=%10d" % (l , countTrkIDs) , flush=True)
                            # do_tracklet_calculations_on_accumulated_contents_of_tracklet_dictionary
                            outputListOfStringsForTracklets = do_tracklet_calculations_on_contents_of_tracklet_dictionary(trkDict, trackletKeys)
                            
                            # write the detection & tracklet strings to file
                            if countTrkIDs == critCount :
                                temp_string_list = outputListOfStringsForTracklets
                                outputListOfStringsForTracklets = outputListOfStringsForTrackletsHeader
                                outputListOfStringsForTracklets.extend(temp_string_list)
                            append_strings_to_files(outputListOfStringsForDetections , outputListOfStringsForTracklets, numberString)
                            
                            # reset the strings to ""
                            outputListOfStringsForDetections,outputListOfStringsForTracklets  = [], []
                            
                            # reset the trkDict to zero
                            trkDict = {}
                            trkDict[trkID] = { 'timeUTC' : [] , 'UV': [] }

            
                    # --- DETECTION-LEVEL QUANTITIES ------------------
                    # Try to parse each detection
                    # - But if anything goes wrong with any of the detections, flag the entire tracklet as something to be ignored
                    try:
                        
                        # parse the obs80 line
                        detDict['timeUTC'] = obs80.jdutc
                        detDict['Vmag']    = obs80.mag
                        detDict['obsCode'] = obs80.cod
                        
                        RA,Dec = obs80.ra * 15. , obs80.dec
                        
                        # convert RA, Dec to unit vector (ecliptic coords)
                        UV = unitvector_equatorial_to_unitvector_ecliptic( radec_to_unitvector_equatorial(RA,Dec) ) # [None,None,None]
                        detDict['UV_X'] = UV[0]
                        detDict['UV_Y'] = UV[1]
                        detDict['UV_Z'] = UV[2]
                        
                        # generate_observatory_position_Heliocentric_Ecliptic_Coordinates
                        obsPosn = calc_heliocentric_position_of_observatory_in_ecliptic_coords(calc_heliocentric_position_of_observatory_in_equatorial_coords(obs80.cod, obs80.jdutc))
                        detDict['Obs_X'] = obsPosn[0]
                        detDict['Obs_Y'] = obsPosn[1]
                        detDict['Obs_Z'] = obsPosn[2]

                        # calculate_ecliptic_latitude() : [RADIANS]
                        detDict['eclipticLat'] = np.arctan( detDict['UV_Z'] / ( detDict['UV_X']**2 +detDict['UV_Y']**2 )**0.5 )

                        # calculate_solar_elongation [RADIANS] :
                        UobsPosn = obsPosn / ( obsPosn[0]**2 + obsPosn[1]**2 + obsPosn[2]**2 )**0.5
                        detDict['solarElong'] = np.pi - angle_unitvectors(UV,UobsPosn)[0]
                        
                        # save the data line as a string
                        outputstr =  " , ".join( [ str(detDict[key]) for key in detectionKeys ] )
                        outputListOfStringsForDetections.append(outputstr)
                    
                    
                        # -------- Now store tracklet quantities --------------------
                        if trkID not in trkDict:
                            trkDict[trkID] = { 'timeUTC' : [] , 'UV': [] }
                        trkDict[trkID]['timeUTC'].append(detDict['timeUTC'])
                        trkDict[trkID]['UV'].append( UV )
                        trkDict[trkID]['objectID']=orbitID

                        # reset the prev_trkID variable
                        prev_trkID = trkID
        
                        # save the orbitID (because it may be useful later on ... )
                        orbitID_Dict[orbitID] = True
                        
                    except:
                        # If anything goes wrong with any of the detections, flag the entire tracklet as something to be ignored
                        if trkID not in trkDict:
                            trkDict[trkID] = { 'timeUTC' : [] , 'UV': [] }
                        trkDict[trkID]['ACCEPT']=False
    # if anything remains in trkDict ...
    # ...do_tracklet_calculations_on_accumulated_contents_of_tracklet_dictionary
    outputListOfStringsForTracklets = do_tracklet_calculations_on_contents_of_tracklet_dictionary(trkDict, trackletKeys)
    # ...write the detection & tracklet strings to file
    append_strings_to_files(outputListOfStringsForDetections , outputListOfStringsForTracklets, numberString)


    return orbitID_Dict

def do_tracklet_calculations_on_contents_of_tracklet_dictionary(trkDict, trackletKeys):
    '''
        _process_detections causes trkDict to accumulate detection info
        Now we want to calculate tracklet-level (or detection-to-detection) quantities
    '''
    outputListOfStringsForTracklets = []
    for trkID in trkDict:
        
        
        # Check whether there were any problems with any of the detections
        if 'ACCEPT' not in trkDict[trkID] or trkDict[trkID]['ACCEPT'] == True:
            times = trkDict[trkID]['timeUTC']
            UVs   = trkDict[trkID]['UV']
            # ensure that they are sorted
            try:
                times, UVs = zip(*sorted(zip(times, UVs)))
            except:
                print('Problem with the time, UV sort ...')
                print('trkID = ', trkID)
                print('times, UVs = ', times, UVs )
                trkDict[trkID]['ACCEPT'] = False
            
            # get angles between adjacent observations
            vecAngSepn = [ angle_unitvectors(uv1, uv2)[0] for uv1, uv2 in zip( UVs[:-1], UVs[1:]) ]
            deltaTimes    = (np.array( times[1:] ) - np.array( times[:-1] ))*3600.*24.
            # VECTOR OF ANGULAR RATES between adjacent observations
            vecAngRate    = [a/t for a,t in zip(vecAngSepn,deltaTimes) ]
            meanAngRate = np.mean(vecAngRate)
            rms = None
            
            
            trkDict[trkID]['trkID'] = trkID
            trkDict[trkID]['vecAngSepn'] = list(vecAngSepn)
            trkDict[trkID]['vecAngRate'] = list(vecAngRate)
            trkDict[trkID]['meanAngRate'] = meanAngRate
            trkDict[trkID]['rms'] = rms
            
            # save the data line as a string
            outputstr =  " , ".join( [ str(trkDict[trkID][key]) for key in trackletKeys ] )
            outputListOfStringsForTracklets.append(outputstr)

        # if there were any problems with a tracklet (either at the detection-level or the racklet-level), don't use this data
        else:
            pass
            
    return outputListOfStringsForTracklets

def append_strings_to_files(outputListOfStringsForDetections , outputListOfStringsForTracklets, numberString):
    '''
        ...
    '''
    # detections
    outputfilepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_%s_real_detections.csv' % numberString)
    _append_to_file(outputfilepath , outputListOfStringsForDetections)

    # tracklets
    outputfilepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_%s_real_tracklets.csv' % numberString)
    _append_to_file(outputfilepath , outputListOfStringsForTracklets)


def _process_orbits(dataList ):
    '''
        dataList looks like ...
        desig_pkd,peri_dist,eccentricity,incl,arg_peri,asc_node,peri_time
        K17A00000Z,1.860740581,0.327816993,11.9724421,24.3326162,353.2247911,2459182.9309837
        
    '''

    # data containers
    orbitDict = {}
    dict_of_Strings_keyed_on_orbitID = {}
    
    # create the header line & append it to the output container
    keys = sorted(data.object_field_definitions.keys())
    headerString = "# " + " , ".join( keys )
    
    for line in dataList:
        
        # split each line
        objectID, orbit_q, orbit_e, orbit_i, orbit_AP, orbit_LAN, orbit_TP = line.strip().split(',')
        
        # if this orbit corresponds to an object in the detection/tracklets, then we want that data. Otherwise, we are not interested
        
        orbitDict['objectID']=objectID
        orbitDict['orbit_q']=orbit_q
        orbitDict['orbit_e']=orbit_e
        orbitDict['orbit_i']=orbit_i
        orbitDict['orbit_AP']=orbit_AP
        orbitDict['orbit_LAN']=orbit_LAN
        orbitDict['orbit_TP']=orbit_TP

        # NEO ?
        orbitDict['isNEO'] = True if float(orbit_q) < 1.3 else False
        orbitDict['objectType'] = None

        # save the data line as a string
        outputstr =  " , ".join( [ str(orbitDict[key]) for key in keys ] )
        dict_of_Strings_keyed_on_orbitID[objectID] = outputstr

    return headerString, dict_of_Strings_keyed_on_orbitID





def _write_to_file(filepath, outputListOfStrings ):
    with open (filepath, 'w') as fh:
        for line in outputListOfStrings:
            fh.write(line + "\n")
    print( "created ", filepath , flush=True)

def _append_to_file(filepath, outputListOfStrings ):
    with open (filepath, 'a') as fh:
        for line in outputListOfStrings:
            fh.write(line + "\n")
    print( "appended to ", filepath , flush=True)





# ----------- SELECT SOURCE FILE LENGTH ----
numberString = '1e5'


# ----------- ORBITS -----------------------
# I want to start by processing all of the orbits (because they are small and can all be held easily in memory)
# - After both they and the detections have been processed, I will down-select to only keep the orbits that have corresponding detections/tracklets

print("---ORBITS---")

# read the orbits
filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'raw_data' , 'sample_orbit_large.csv')
dataList = _read_from_file(filepath)[1:]
print("length of raw data = ", len(dataList))

# process the orbits
headerStringOrbits, dict_of_Strings_keyed_on_orbitID = _process_orbits(dataList)
print('headerStringOrbits', headerStringOrbits)
print('len(dict_of_Strings_keyed_on_orbitID) = ', len(dict_of_Strings_keyed_on_orbitID) )
key0 = list(dict_of_Strings_keyed_on_orbitID.keys())[0] ; print('\t key0=%s : value0=%s' % (key0, dict_of_Strings_keyed_on_orbitID[key0]) )



# ---------- DETECTIONS -------------------
print()
print("---DETECTIONS & TRACKLETS---")
# pre-sort step ...
#command = "sort -t, -k1,1 -k3,2 -k2,3 sample_obs_large.csv > sample_obs_large_sorted.csv"

# read the detections
print("reading...")
filepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'raw_data' , 'sample_obs_%s_sorted.csv' % numberString )
dataList = _read_from_file(filepath)[1:]
print(len(dataList))

# process the detections
print("processing...")
orbitID_Dict = _process_detections(dataList, numberString, dict_of_Strings_keyed_on_orbitID)
print('length of orbitID_dict returned from _process_detections step = ... ', len(orbitID_Dict) )
key0 = list( orbitID_Dict.keys())[0] ; print(' \t Example of orbitID from orbitID_Dict ... %s:%s' % (key0 , orbitID_Dict[key0]) )





# ----------- ORBITS -----------------------
print("--- TRIMMING ORBITS ... ---")
# only select the orbits that have data in the detection/tracklet dictionary

tmpListOfStrings = []
for k,v in dict_of_Strings_keyed_on_orbitID.items():
    if k in orbitID_Dict:
        tmpListOfStrings.append(v)

outputListOfStrings = [headerStringOrbits]
outputListOfStrings.extend(tmpListOfStrings)
print('len(outputListOfStrings) = %d ' % len(outputListOfStrings) )
print('outputListOfStrings[0] = ', outputListOfStrings[0])
print('outputListOfStrings[1] = ', outputListOfStrings[1])

# save the orbits to file
outputfilepath = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'sample_data' , 'sample_data_%s_real_objects.csv' % numberString )
_write_to_file(outputfilepath , outputListOfStrings)





'''
    Problems experienced with duplicate observations for ... 
    trkID =  00000DbFSK
    trkID =  00000DbFSJ
    trkID =  00000DoeSa

'''
