"""
Rackspace CloudFiles Viewer
"""
from __future__ import print_function

import os
import json
import sys
import logging
import logging.config
import argparse 

from rcbu.client.auth import Authentication
from rcbu.cloud.files import CloudFiles


def prompt_get_data_centers(auth_engine):
    """
    Prompt the user to select a data center

    Returns either:
        NULL string to denote the user cancelled the operation
        Data center name
    """
    # Access the list of DCs from the service catalog
    cf_dcs = auth_engine.GetCloudFilesDataCenters()

    found_dc = False
    return_dc = ''
    #
    #   Access the list of datacenters from the service catalog
    #   Allow the user to either select one or cancel the operation
    #   Invalid selection repeats the loop
    #
    while not found_dc:
        # List the data centers from the service catalog
        print('Found Cloud Files Data Centers:')
        dc_counter = 0
        for dc in cf_dcs:
            print('\t' + str(dc_counter) + ') ' + dc)
            dc_counter += 1

        # Add cancel entry
        print('\t' + str(dc_counter) + ') quit')
        
        # Handle user input
        try:
            dc_selection = input('Please select data center: ')
            if dc_selection >= 0 and dc_selection < dc_counter:
                # List selection
                return_dc = cf_dcs[dc_selection]
                found_dc = True
            elif dc_selection is dc_counter:
                # Cancel operation
                return_dc = ''
                found_dc = True
            else:
                # Invalid input
                print('Invalid selection.')
                found_dc = False
        except SyntaxError:
            # Invalid input through exception handling from input()
            print('Invalid selection.')
            found_dc = False

    return return_dc


def prompt_get_uri(auth_engine, dc):
    """
    Prompt the user to select a uri (public or snet)

    Returns either:
        NULL string to denote the user cancelled the operation
        URI for the CloudFiles Network Access
    """
    # Access the list of URIs for the DC from the service catalog
    cf_uris = auth_engine.GetCloudFilesUri(dc)

    found_uri = False
    return_uri = ''
    #
    #   Access the list of URIs for the given data center from the service catalog
    #   Allow the user to either select one or cancel the operation
    #   Invalid selection repeats the loop
    #
    while not found_uri:
        # List the networks from the service catalog
        print('Available CloudFile Networks for ' + dc + ':')
        uri_counter = 0
        for uri in cf_uris:
            print('\t' + str(uri_counter) + ') ' + uri['name'] + ' - ' + uri['uri'])
            uri_counter += 1

        # Add the cancel entry
        print('\t' + str(uri_counter) + ') return to previous menu')

        # Handle user input
        try:
            uri_selection = input('Please select network: ')
            if uri_selection >= 0 and uri_selection < uri_counter:
                # List selection
                return_uri = cf_uris[uri_selection]['uri']
                found_uri = True
            elif uri_selection is uri_counter:
                # Cancel operation
                return_uri = ''
                found_uri = True
            else:
                # Invalid selection
                print('Invalid selection.')
                found_uri = False
        except SyntaxError:
            # Invalid input through exception handling from input()
            print('Invalid selection.')
            found_uri = False

    return return_uri

def prompt_get_container(cloudfiles_engine, cf_container_uri, cf_container_limit=10):
    """
    Prompt the user to select a container in Cloud Files
    
    Returns either:
        NULL string to denote the user cancelled the operation
        Container name
    """
    cf_container_marker = ''
    return_container = ''
    continue_container_search = True
    #
    #   Access the list of containers up to cf_container_limit in size
    #   List access must be repeated if the user wants more containers listed
    #
    while continue_container_search:
        # Access the list of containers for the user in cloud files
        cf_containers = cloudfiles_engine.GetContainers(cf_container_uri, cf_container_limit, cf_container_marker)

        found_container = False
        #
        #   Allow the user to select one, request more, or cancel the operation
        #   Invalid selection repeats the loop
        #
        while not found_container:
            # List the containers from CloudFiles
            container_counter = 0
            for container in cf_containers:
                print('\t' + str(container_counter) + ') ' + container['name'] + ' (Size: ' + str(container['bytes']) + ' bytes)')
                container_counter += 1

            # Determine if we need to provide the user the option to get more containers
            has_more_containers = False
            if len(cf_containers) and len(cf_containers) == cf_container_limit:
                print('\t' + str(container_counter) + ') Check for more containers')
                has_more_containers = True
                container_counter += 1
            
            # Add the cancel operation
            print('\t' + str(container_counter) + ') return to previous menu')

            # Handle user input
            try:
                container_selection = input('Please select container: ')
                if container_selection is container_counter:
                    # Cancel operation
                    return_container = ''
                    found_container = True              # Exit inner loop
                    continue_container_search = False   # Exit outer loop
                elif container_selection >= 0 and container_selection < container_counter:
                    # If there are more containers than len(cf_containers) is a phantom object that represents
                    #   the user request for more containers.
                    if has_more_containers and container_selection is len(cf_containers):
                        # Request more containers
                        cf_container_marker = cf_containers[len(cf_containers)-1]['name']
                        found_container = True              # Exit inner loop
                        continue_container_search = True    # Continue outer loop
                    else:
                        # List selection
                        print('Selected container #' + str(container_selection))
                        return_container = cf_containers[container_selection]['name']
                        found_container = True              # Exit inner loop
                        continue_container_search = False   # Exit outer loop
                else:
                    # Invalid selection
                    print('Invalid selection.')
                    found_container = False                 # Repeat inner loop
                    containue_container_search = True       # Repeat outer loop
            except SyntaxError:
                # Invalid selection through exception handling from input()
                print('Invalid selection.')
                found_container = False                 # Repeat inner loop
                containue_container_search = True       # Repeat outer loop
    return return_container


def prompt_download():
    """
    Ask the user if they want to download the object
    """
    while True:
        result = raw_input('Download? [y/n]')
        if result == 'y' or result == 'Y':
            return True
        elif result == 'n' or result == 'N':
            return False
        else:
            print('Invalid input. Please try again')


def prompt_list_container(cloudfiles_engine, cf_container_uri, cf_container, cf_object_limit=10):
    """
    List the contents of a container in CloudFiles for the user
    """
    cf_object_marker = ''
    continue_object_search = True
    #
    #   Access the list of objects up to cf_object_limit in size
    #   List access must be repeated if the user wants more objects listed
    #
    while continue_object_search:
        # Access the list of objects in the container from CloudFiles
        cf_objects = cloudfiles_engine.GetContainerObjects(cf_container_uri, cf_container, cf_object_limit, cf_object_marker)

        continue_list_objects = True
        #
        #   Allow the user to select one to display, request more, or cancel the operation
        #   Invalid selection repeats the loop
        #
        while continue_list_objects:
            # List the objects from CloudFiles
            object_counter = 0
            for cfobject in cf_objects:
                print('\t' + str(object_counter) + ') ' + cfobject['name'] + '(Size: ' + str(cfobject['bytes']) + ' bytes)')
                object_counter += 1

            # Determine if we need to provide the user the option to get more objects
            has_more_objects = False
            if len(cf_objects) and len(cf_objects) == cf_object_limit:
                print('\t' + str(object_counter) + ') Check for more objects')
                has_more_objects = True
                object_counter += 1

            # Add the cancel operation
            print('\t' + str(object_counter) + ') return to previous menu')

            # Handle user input
            try:
                object_selection = input('Please select object: ')
                if object_selection is object_counter:
                    # Cancel operation
                    continue_list_objects = False       # Exit inner loop
                    continue_object_search = False      # Exit outter loop
                elif object_selection >= 0 and object_selection < object_counter:
                    # If there are more objects than len(cf_objects) is a phantom object that represents
                    #   the user request for more objects.
                    if has_more_objects and object_selection is len(cf_objects):
                        # Request more containers
                        cf_object_marker = cf_objects[len(cf_objects)-1]['name']
                        continue_list_objects = False   # Exit inner loop
                        continue_object_search = True   # Continue outer loop
                    else:
                        # List information about the object
                        print('\t\tName: ' + cf_objects[object_selection]['name'])
                        print('\t\tSize: ' + str(cf_objects[object_selection]['bytes']) + ' bytes')
                        print('\t\tContent-Type: ' + cf_objects[object_selection]['content_type'])
                        print('\t\tLast Modified: ' + cf_objects[object_selection]['last_modified'])
                        print('\t\tHash: ' + cf_objects[object_selection]['hash'])

                        if prompt_download():
                            target_location = os.getcwd() + '/' + cf_objects[object_selection]['name']
                            cloudfiles_engine.DownloadObject(cf_container_uri, cf_container, cf_objects[object_selection], target_location)

                        # Wait for the user
                        try:
                            dummy = input('\tPress ENTER to continue')
                        except SyntaxError:
                            pass
                        continue_list_objects = True    # Continue inner loop
                        continue_object_search = True   # Continue outter loop
                else:
                    # Invalid selection
                    print('Invalid selection')
                    continue_list_objects = True        # Continue inner loop
                    continue_object_search = True       # Continue outter loop
            except SyntaxError:
                # Invalid selection through exception handling from input()
                print('Invalid selection')
                continue_list_objects = True        # Continue inner loop
                continue_object_search = True       # Continue outter loop


def main():
    """
    Main Application Entry
    """
    #
    #   Program has several arguments:
    #       '--user' to specify a JSON formatted file with the following data:
    #           'user'
    #           'apikey'
    #           'request-limit'
    #       '--log-config' ti specify an INI file for configuring the Python logging system, namely
    #           for debug purposes
    #
    argument_parse = argparse.ArgumentParser(prog='cloudfilews-viewer', description='Rackspace CloudFiles Viewer')
    argument_parse.add_argument('--user', required=True, help='Specify a text file containing the JSON data for the \'user\' and \'apikey\' values for authentication', metavar='User Auth Data', type=argparse.FileType('r'))
    argument_parse.add_argument('--log-config', required=False, help='Specify the log configuration data', metavar='Log config')
    arguments = argument_parse.parse_args()

    # log config is optional
    try:
        log_config_file = str(arguments.log_config)
        logging.config.fileConfig(str(log_config_file))
    except LookupError:
        # Don't configure the logger
        pass

    # Load the user data
    user_data = json.load(arguments.user)
    print('Logging into CloudFiles...')
    print('\tUser: ' + user_data['user'])
    print('\tAPI-Key: ' + user_data['apikey'])
    # Authenticate the user
    auth_engine = Authentication(user_data['user'], user_data['apikey'])
    auth_token = auth_engine.AuthToken
    if auth_token is None:
        print('Invalid API Key or User Name')
        return -1

    # CloudFIles Access
    cloudfiles_engine = CloudFiles(True, auth_engine)
    print('Received AuthToken: ' + auth_token)

    # Loop over user selecting the data center
    continue_dc_search = True
    while continue_dc_search:
        cf_dc = prompt_get_data_centers(auth_engine)
        if not len(cf_dc):
            continue_dc_search = False
        else:
            print('Selected DC: ' + cf_dc)
            continue_uri_search = True
            # Loop over the user selecting the network/uri
            while continue_uri_search:
                cf_uri = prompt_get_uri(auth_engine, cf_dc)
                if not len(cf_uri):
                    continue_uri_search = False
                else:
                    print('Selected Network URI: ' + cf_uri)
                    continue_container_search = True
                    # Loop over the user selecting the container
                    while continue_container_search:
                        cf_container = prompt_get_container(cloudfiles_engine, cf_uri[8:], user_data['request-limit'])
                        if not len(cf_container):
                            continue_container_search = False
                        else:
                            print('Selected Container: ' + cf_container)
                            # Show the user the list of objects in the container
                            prompt_list_container(cloudfiles_engine, cf_uri[8:], cf_container, user_data['request-limit'])


if __name__ == "__main__":
    main()
