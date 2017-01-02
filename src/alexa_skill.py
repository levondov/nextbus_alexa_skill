"""
Template based on the alexa color example written in python
"""

from __future__ import print_function
#from src.nextbus import *
import requests
import xml.etree.ElementTree as ET 

# api xml url from nextbus
nextbus = 'http://webservices.nextbus.com/service/publicXMLFeed?command=predictions';

# --------------- Helpers that build all of the responses ----------------------

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': "SessionSpeechlet - " + title,
            'content': "SessionSpeechlet - " + output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }


# --------------- Functions that control the skill's behavior ------------------

def get_prediction(agency='actransit',stopId='56730'):
    """ default stop id and agency just for testing 
    makes a request and grabs xml data from nextbus api """
    
    api_url = nextbus + '&a=' + agency + '&stopId=' + stopId
    return requests.get(api_url)

def parse_prediction(response):
    """ parses the xml response from nextbus api """
    
    root = ET.fromstring(response.content)
    
    try:
        # grab the stop location
        stop_location = root[0].attrib['stopTitle']
    except:
        stop_location = False
    try:        
        # grab the times for the next incoming buses (in minutes)
        stop_nextbus_times = []
        for stop in root.iter('prediction'):
            stop_nextbus_times.append(stop.attrib['minutes'])
    except:
        stop_nextbus_times = False
                
    # Grab the message posted under predictions just in case
    # e.g. bus routes stopped for holiday etc...
    # note message should be under body>predictions>message
    # might be a better way to check for this in the future
    stop_message = root[0][0].attrib['text']
    stop_busid = root[0].attrib['routeTag']
        
    return stop_location,stop_nextbus_times,stop_busid,stop_message
    
    
def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the University of Maryland bus route alexa skill. " \
                    "You can request arrival times for a specific stop by saying, " \
                    "when is the next bus coming at stop ID."
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "You can find your bus stop's ID online at next bus's website. " \
                    "Once you have a bus stop ID you can make a request, for example, " \
                    "when is the next bus coming at stop three zero nine six five."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_end_request():
    card_title = "Session Ended"
    speech_output = "Have a nice day!"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))

def get_bus_arrival_session(intent, session):

    session_attributes = {}
    reprompt_text = {}
        
    reprompt_text = None
    intent_stopID = intent_request['intent']['stopID']
    
    r = get_prediction(stopId=intent_stopID)
    stop_location,stop_nextbus_times,stop_bus_id,stop_message = parse_prediction(r)
    
    if stop_nextbus_times:
        speech_output = "The " + stop_bus_id + " will be arriving in "
        
        N = len(stop_nextbus_times)        
        speech_times = ''
        for i,times in enumerate(stop_nextbus_times):
            if (i+1) == N:
                speech_times = speech_times + 'and ' + times + ' minutes '
            else:
                speech_times = speech_times + times + ', '
                
        speech_output = speech_output + speech_times + 'at ' + stop_location + '.'
        should_end_session = True
    else:
        # no times available to post.
        if stop_bus_id or stop_message:
            # if a bus name and message is available
            speech_output = 'There is no incoming bus at this moment at ' + stop_location
        else:
            speech_output = 'There is something wrong with the stop ID you gave me, please try again.'
        should_end_session = True
            
            

    # Setting reprompt_text to None signifies that we do not want to reprompt
    # the user. If the user does not respond or says something that is not
    # understood, the session will end.
    return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))


# --------------- Events ------------------

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
          + ", sessionId=" + session['sessionId'])


def on_launch(launch_request, session):
    """ Called when the user launches the skill without specifying what they
    want
    """

    print("on_launch requestId=" + launch_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # Dispatch to your skill's launch
    return get_welcome_response()


def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])

    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "WhatsMyBusArrivalIntent":
        return get_bus_arrival_session(intent, session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request()
    else:
        raise ValueError("Invalid intent")


def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.

    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    # add cleanup logic here


# --------------- Main handler ------------------

def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])

    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if event['session']['new']:
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if event['request']['type'] == "LaunchRequest":
        return on_launch(event['request'], event['session'])
    elif event['request']['type'] == "IntentRequest":
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])

