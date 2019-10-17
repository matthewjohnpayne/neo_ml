'''
    
    Define data structures for ingesting neo data
    Intended for machine learning class with C. Nugent @ Olin
    October 2019 
    
    Additional documentation can be found at 
    https://docs.google.com/document/d/1IQfrNybRuYe4H3vv6nQQGbgDXLxGWLdKmQykB5gCzSg/edit?usp=sharing
    https://docs.google.com/document/d/1HTnXRNGVyprxFUJaoBT3BeXZ07UaVWwNvLhE89zKPUM/edit?usp=sharing
    
'''


# -----------------------------------
# Third-party imports
# -----------------------------------
import sys, os
import numpy as np


# -----------------------------------
# Define data structures for neo_ml
# -----------------------------------
detection_field_definitions = {
    'detID'         : 'Unique Detection ID',
    'trkID'         : 'Unique Tracklet ID ',
    'timeUTC'       : 'Time of each observation [JDUTC]',
    'Obs_X'         : 'X-Position of the Observatory w.r.t. the Sun at the time of detection. Ecliptic coordinate Frame. [au]',
    'Obs_Y'         : 'Y-Position of the Observatory w.r.t. the Sun at the time of detection. Ecliptic coordinate Frame. [au]',
    'Obs_Z'         : 'Z-Position of the Observatory w.r.t. the Sun at the time of detection. Ecliptic coordinate Frame. [au]',
    'UV_X'          : 'X-Component of unit vector from the observatory to the detection position. Ecliptic coordinate Frame.',
    'UV_Y'          : 'Y-Component of unit vector from the observatory to the detection position. Ecliptic coordinate Frame.',
    'UV_Z'          : 'Z-Component of unit vector from the observatory to the detection position. Ecliptic coordinate Frame.',
    'Vmag'          : 'Equivalent V-band magnitude of the detection',
    'obsCode'       : 'A unique code to label the observatory which undertook the detection',
    'eclipticLat'   : 'Latitude of the observation from the plane of the ecliptic [radians]',
    'solarElong'    : 'Angular separation between the Sun and the detection, with Earth as the reference point [radians]',
}
tracklet_field_definitions = {
    'trkID'         : 'Unique Tracklet ID ',
    'objectID'      : 'Unique Object ID (enables labelling of object-type for known objects)',
    'vecAngSepn'    : 'Vector of angular separations between adjacent observations [radians]',
    'vecAngRate'    : 'Vector of angular rates between adjacent observations [radians / s]',
    'meanAngRate'   : 'Mean angular rate for the entire tracklet [radians / s]',
    'rms'           : 'RMS deviation from best-fit straight line',
}
object_field_definitions = {
    'objectID'      : 'Unique Object ID',
    'isNEO'         : 'Label whether a known object is an NEO [boolean]',
    'objectType'    : 'Sub-classification of object into various types [integer]',
    'orbit_q'	    : 'Nominal/best-fit Keplerian orbit for the object: percenter distance [au]',
    'orbit_e'       : 'Nominal/best-fit Keplerian orbit for the object: eccentricity',
    'orbit_i'	    : 'Nominal/best-fit Keplerian orbit for the object: inclination [rad]',
    'orbit_AP'	    : 'Nominal/best-fit Keplerian orbit for the object: arg. of peri. [rad]',
    'orbit_LAN'	    : 'Nominal/best-fit Keplerian orbit for the object: long. asc. node [rad]',
    'orbit_TP'      : 'Nominal/best-fit Keplerian orbit for the object: time peri. pass [JDUTC]',
}
