from __future__ import absolute_import

import datetime
import os
import traceback
import urllib
import json

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'schemalister.settings')

app = Celery('tasks', broker=os.environ.get('REDISTOGO_URL', 'redis://localhost'))

from getschema.models import Object, Field, Debug
from django.conf import settings
from . import utils
import requests


@app.task
def get_objects_and_fields(schema):
    instance_url = schema.instance_url
    org_id = schema.org_id
    access_token = schema.access_token

    # List of standard objects to include
    # standard_objects = (
    #     'Account',
    #     'AccountContactRelation',
    #     'AccountTeamMember',
    #     'Activity',
    #     'Asset',
    #     'Campaign',
    #     'CampaignMember',
    #     'Case',
    #     'Contact',
    #     'ContentVersion',
    #     'Contract',
    #     'ContractContactRole',
    #     'Event',
    #     'ForecastingAdjustment',
    #     'ForecastingQuota',
    #     'KnowledgeArticle',
    #     'Lead',
    #     'Opportunity',
    #     'OpportunityCompetitor',
    #     'OpportunityLineItem',
    #     'Order',
    #     'OrderItem',
    #     'Pricebook2',
    #     'PricebookEntry',
    #     'Product2',
    #     'Quote',
    #     'QuoteLineItem',
    #     'Solution',
    #     'Task',
    #     'User',
    #
    #     # Field Services Lightning Objects
    #     'Address',
    #     'AppExtension',
    #     'AssignedResource',
    #     'AssociatedLocation',
    #     'DigitalSignature',
    #     'FieldServiceMobileSettings',
    #     'LinkedArticle',
    #     'Location',
    #     'MaintenanceAsset',
    #     'MaintenancePlan',
    #     'OperatingHours',
    #     'ProductConsumed',
    #     'ProductItem',
    #     'ProductItemTransaction',
    #     'ProductRequest',
    #     'ProductRequestLineItem',
    #     'ProductRequired',
    #     'ProductTransfer',
    #     'ResourceAbsence',
    #     'ResourcePreference',
    #     'ServiceAppointment',
    #     'ServiceAppointmentStatus',
    #     'ServiceCrew',
    #     'ServiceCrewMember',
    #     'ServiceReport',
    #     'ServiceReportTemplate',
    #     'ServiceResource',
    #     'ServiceResourceCapacity',
    #     'ServiceResourceSkill',
    #     'ServiceTerritory',
    #     'ServiceTerritoryLocation',
    #     'ServiceTerritoryMember',
    #     'Shipment',
    #     'Skill',
    #     'SkillRequirement',
    #     'TimeSheet',
    #     'TimeSheetEntry',
    #     'TimeSlot',
    #     'WorkOrder',
    #     'WorkOrderLineItem',
    #     'WorkOrderStatus',
    #     'WorkOrderLineItemStatus',
    #     'WorkType',
    # )

    standard_objects = (
        'Account',
        'Asset',
        'Assigned_Resource__c',
        'Case',
        'Contact',
        'ContactLineItem',
        'Entitlement',
        'KnowledgeArticle',
        'KnowledgeArticleVersion',
        'Order',
        'OrderItem',
        'Payment__c',
        'Pricebook2',
        'Product2',
        'Service_Appointment__c',
        'ServiceContract',
        'User',
        'WorkOrder',
        'WorkOrderLineItem',
        'Account__e',
        'Case__e',
        'Work_Order__e',
        'Work_Order_Line__e'
    )

    headers = {
        'Authorization': 'Bearer ' + access_token,
        'content-type': 'application/json'
    }

    # Describe all sObjects
    url = instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) + '.0/sobjects/'
    all_objects = requests.get(url, headers=headers)

    print("**** GET: ", url)
    print("**** HEADERS: ", headers)

    try:

        if 'sobjects' in all_objects.json():

            for sObject in all_objects.json()['sobjects']:

                object_name = sObject['name']

                if object_name in standard_objects: # or sObject['name'].endswith('__c'):

                    # Skip managed package objects if we don't want them
                    # Counting to see if "__" appears twice in the object name.
                    if not schema.include_managed_objects and object_name.count('__') > 1:
                        continue

                    # Create object record
                    new_object = Object()
                    new_object.schema = schema
                    new_object.api_name = sObject['name']
                    new_object.label = sObject['label']
                    new_object.save()

                    # query for fields in the object
                    describeURL = instance_url + sObject['urls']['describe']

                    print("**** GET - describe(" + object_name + "): ", describeURL)

                    object_describe = requests.get(describeURL, headers=headers)

                    # because description is not part of the sObject describe's response we have to make a separate
                    # soql query to fieldDefinition

                    # curl
                    # -H 'Authorization: Bearer 00D0S000000DNyj!AQgAQM_Opn31IjPZVDtLhkNNxFzTYzo_tM1nNUTDG9mtlSACgj85sxPoMwQZPQEEHp4Bna73I.JM9x267zdV_jSYCnmdKnV.'
                    # -H 'Content-type: application/json'
                    # https://transformholding--qa.my.salesforce.com/services/data/v47.0/query/?q="select+Label,+QualifiedApiName,+Description+from+FieldDefinition+where+EntityDefinitionId='Account'"

                    query_url = instance_url + '/services/data/v' + str(settings.SALESFORCE_API_VERSION) \
                                + '.0/query/?q=' + urllib.quote_plus(
                        'select' + ' Label, QualifiedApiName, Description from FieldDefinition where EntityDefinitionId') \
                                + "=" + "'{0}'".format(object_name)

                    # print("===> queryUrl: ", query_url)
                    # print("*** GET - description(" + object_name + "): ", query_url)

                    object_description = requests.get(query_url, headers=headers)
                    field_descriptions = object_description.json()['records']

                    # print("******* Description JSON", object_description.json())

                    # Loop through fields
                    for field in object_describe.json()['fields']:

                        # Get the field name
                        field_name = field['name']

                        # Skip field if it's managed

                        if not schema.include_managed_objects and field_name.count('__') > 1:
                            continue

                        # Create field
                        new_field = Field()
                        new_field.object = new_object
                        new_field.api_name = field_name
                        new_field.label = field['label']

                        # find description for current api field name and return
                        description = ""
                        s = filter(lambda x: x["QualifiedApiName"] == field_name, field_descriptions)
                        if s:
                            description = json.loads(json.dumps(s))[0]['Description']

                        new_field.description = description

                        if 'inlineHelpText' in field:
                            new_field.help_text = field['inlineHelpText']

                        # lookup field
                        if field['type'] == 'reference':
                            new_field.data_type = 'Lookup ('

                            # Could be a list of reference objects
                            for referenceObject in field['referenceTo']:
                                new_field.data_type = new_field.data_type + referenceObject.title() + ', '

                            # remove trailing comma and add closing bracket
                            new_field.data_type = new_field.data_type[:-2]
                            new_field.data_type = new_field.data_type + ')'

                        # Formula field
                        elif field['calculated']:
                            new_field.data_type = 'Formula (' + FIELD_TYPES.get(field['type'],
                                                                                field['type'].title()) + ')'
                            new_field.formula = field.get('calculatedFormula')

                        # picklist values
                        elif field['type'] == 'picklist' or field['type'] == 'multipicklist':
                            new_field.data_type = field['type'].title() + ' ('

                            # Add in picklist values
                            for picklist in field['picklistValues']:
                                if new_field.data_type and picklist.get('label'):
                                    new_field.data_type = new_field.data_type + picklist.get('label', ' ') + '; '

                            # remove trailing comma and add closing bracket
                            new_field.data_type = new_field.data_type[:-2]
                            new_field.data_type = new_field.data_type + ')'

                        # Text
                        elif field['type'] == 'string':
                            new_field.data_type = 'Text (' + str(field['length']) + ')'

                        # Int
                        elif field['type'] == 'int':
                            new_field.data_type = 'Number (' + str(field['digits']) + ', 0)'

                        elif field['type'] == 'boolean':
                            new_field.data_type = 'Checkbox'

                        # everything else
                        else:
                            new_field.data_type = field['type'].title()

                            # Change Double to Number
                            if new_field.data_type == 'Double':
                                new_field.data_type = 'Number'

                            # If there is a length component, add to the field type
                            if 'length' in field and int(field['length']) > 0:
                                new_field.data_type += ' (' + str(field['length']) + ')'

                            # If there is a precision element
                            if 'precision' in field and int(field['precision']) > 0:
                                # Determine the number of digits
                                num_digits = int(field['precision']) - int(field['scale'])

                                # Set the precision and scale against the field
                                new_field.data_type += ' (' + str(num_digits) + ', ' + str(field['scale']) + ')'

                        # Add in additional attributes
                        attributes = []

                        if not field.get('nillable'):
                            attributes.append('Required')

                        if field.get('unique'):
                            attributes.append('Unique')

                        if field.get('externalId'):
                            attributes.append('External ID')

                        if field.get('caseSensitive'):
                            attributes.append('Case Sensitive')

                        if attributes:
                            new_field.attributes = ', '.join(attributes)

                        new_field.save()

            # If the user wants to see all the places the fields are used
            # run logic to query for other metadata
            if schema.include_field_usage:

                try:

                    # Get all fields for the schema
                    all_fields = Field.objects.filter(object__schema=schema)

                    # Get all layouts usage
                    utils.get_usage_for_component(all_fields, schema, 'Layout')

                    utils.get_usage_for_component(all_fields, schema, 'WorkflowRule')

                    utils.get_usage_for_component(all_fields, schema, 'WorkflowFieldUpdate')

                    utils.get_usage_for_component(all_fields, schema, 'WorkflowOutboundMessage')

                    utils.get_usage_for_component(all_fields, schema, 'EmailTemplate')

                    utils.get_usage_for_component(all_fields, schema, 'Flow')

                    utils.get_usage_for_component(all_fields, schema, 'ApexClass')

                    utils.get_usage_for_component(all_fields, schema, 'ApexComponent')

                    utils.get_usage_for_component(all_fields, schema, 'ApexPage')

                    utils.get_usage_for_component(all_fields, schema, 'ApexTrigger')

                    utils.build_usage_display(all_fields)

                    schema.status = 'Finished'

                except Exception as error:
                    schema.status = 'Error'
                    schema.error = traceback.format_exc()

            else:
                schema.status = 'Finished'

        else:

            schema.status = 'Error'
            schema.error = 'There was no objects returned from the query'

            debug = Debug()
            debug.debug = all_objects.text
            debug.save()

    except Exception as error:
        schema.status = 'Error'
        schema.error = traceback.format_exc()

    schema.finished_date = datetime.datetime.now()
    schema.save()

    return str(schema.id)


FIELD_TYPES = {
    'boolean': 'Checkbox',
    'int': 'Number',
    'string': 'Text'
}
