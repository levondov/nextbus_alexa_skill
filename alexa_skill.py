"""
Template based on the alexa color example written in python
"""

from __future__ import print_function
from src.nextbus import *
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
            'title': "Bus Times",
            'content': output
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
    
    
def bus_response(busObj):
    #
    #   bus_exists - 2x1 boolean list
    #       bus_exists[0] - If the bus has an arrival time
    #       bus_exists[1] - Does bus exists or is it an incorrect stopid
    #
    #
    if busObj['times'] and busObj['bus id']:
        # if there is a bus name and arrival time
        speech_output = 'The ' + busObj['bus id'] + ' '
        
        if busObj['direction']:
        # if there is a direction
            speech_output = speech_output + 'heading to ' + busObj['direction'] + ' will arrive in '
        
        else:
            speech_output = speech_output + 'will be arriving in '
        
        N = len(busObj['times'])
        if N == 1:
            speech_times = busObj['times'][0] + ' minutes. '
        else:
            speech_times = ''
            for i,times in enumerate(busObj['times']):
                if (i+1) == N:
                    speech_times = speech_times + 'and ' + times + ' minutes. '
                else:
                    speech_times = speech_times + times + ', '
        speech_output = speech_output + speech_times
        bus_exists = [True, True]
    else:
        # no times available to post.
        if busObj['bus id']:
            # if a bus name and message is available
            speech_output = '' # Does not matter as it will not be used
            bus_exists = [False, True]
        else:
            speech_output = 'I could not find a bus stop with the stop ID you gave me. '
            bus_exists = [False, False]
        
    return speech_output,bus_exists

# --------------- Functions that control the skill's behavior ------------------
    
def get_welcome_response():
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """

    session_attributes = {}
    card_title = "Welcome"
    speech_output = "Welcome to the bus updates skill for the amazon echo. " \
                    "This skill will grab bus arrival times for the University of Maryland dots bus system, " \
                    "To get started, you need to give me a bus stop ID to search. "
    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    reprompt_text = "You can find your bus stop's ID online at next bus's website. " \
                    "Once you have a bus stop ID you can make a request, for example, " \
                    "when is the next bus coming at stop one zero zero zero one."
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
    should_end_session = 'True'
        
    reprompt_text = None
    intent_stopID = intent['slots']['stop']['value']
    
    if intent_stopID is 'stop' or intent_stopID is 'cancel':
        return handle_session_end_request()
    
    r = get_prediction('umd',stopId=intent_stopID)
    busObjs = parse_prediction(r)
    
    speech_output = ''
    buses_with_no_times = []
    for busObj in busObjs:
        # for each bus in the route get a response
        response,bus_exists = bus_response(busObj)
        if bus_exists[0]:
        # bus has an arrival time, add it to speech_output
            speech_output = speech_output + response
        elif (not bus_exists[0]):
        # no bus arrival time exists, check further
            if bus_exists[1]:
            # bus exists, but has no arrival time, add it to the list
                buses_with_no_times.append(busObj['bus id'])
            else:
            # something is wrong with the stopID, break for loop and return message
                speech_output = speech_output + response
                return build_response(session_attributes, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))
        
    # Build and add in buses with no arrival times
    speech_tmp = 'No available times for the '
    for bus in buses_with_no_times:
        if bus is buses_with_no_times[-1]:
            speech_tmp = speech_tmp + 'and ' + bus + ' buses. '
        else:
            speech_tmp = speech_tmp + bus + ', '
            
    speech_seasonal = ''
    speech_output = speech_output + speech_tmp + speech_seasonal

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




