import requests
import xml.etree.ElementTree as ET 

# api xml url from nextbus
nextbus = 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions';

def get_prediction(agency='actransit',stopId='56730'):
    """ default stop id and agency just for testing 
    makes a request and grabs xml data from nextbus api """
    
    api_url = nextbus + '&a=' + agency + '&stopId=' + stopId
    return requests.get(api_url)

def parse_prediction(response):
    """ parses the xml response from nextbus api """
    #############
    #
    # This function creates a list of dictionaries, each dictionary contains a bus's info
    #   each bus has the following dictionary entries:
    #       'stop location' - location of the bus stop
    #       'bus id' - the bus name/number
    #       'direction' - the direcation the bus is heading
    #       'message' - a message posted for that specific bus, e.g. closed for holidays
    #       'times' - a list of arrival times
    #
    #############
    #
    # create a dictionary object for each bus that contains the 
    # bus name, direction, location, arrival times, and messages
    root = ET.fromstring(response.content)
    
    # list of different buses at the stop
    N = len(root)
    busObjs = [{} for _ in range(N)]       
        
    # cycle through all buses at stop        
    for busObj,bus in zip(busObjs,root):
        # grab the stop location
        try:
            busObj['stop location'] = root[0].attrib['stopTitle']    
        except:
            busObj['stop location'] = False 
    
        # cycle through the different buses
        # and grab the bus names
        try:
            busObj['bus id'] = bus.attrib['routeTag']
        except:
            busObj['bus id'] = False
            
        # for each bus grab arrival times, message, and bus direction
        
        # grab first bus direction
        try:
            busObj['direction'] = bus[0].attrib['title']
        except:
            busObj['direction'] = False
        
        # grab first bus message
        try:
            busObj['message'] = bus[0].attrib['text']
        except:
            busObj['message'] = False
        
        # grab bus arrival times        
        arrival_times = []
        for prediction in bus.iter('prediction'):
             arrival_times.append(prediction.attrib['minutes'])
        busObj['times'] = arrival_times
        
    return busObjs
        

### example call       
#r = get_prediction('actransit','55570')
#bus = parse_prediction(r)
#print bus
