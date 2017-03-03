import requests
import json
import re
import logging

from sphinxcontrib.swaggerdoc.property import *

from bravado_core.spec import Spec
from bravado_core.schema import collapsed_properties
from bravado_core.param import get_param_type_spec

class SwaggerSource(object):
    """
        Class to interract with a swagger specification file
        and Property objects. Use the bravado_core library
    """
    def __init__(self):
        super(SwaggerSource, self).__init__()
        self.config = {'use_models': True, 'validate_requests': False}

    def extract_model_name(self, swagger_ref):
        m = re.match("^#/definitions/(.*)", swagger_ref)
        if m:
            return m.group(1)
        else:
            return swagger_ref


    def load_from_dict(self, swager_dict):
        self.dict = swager_dict
        self.spec = Spec.from_dict(self.dict, config=self.config)

    def load_from_url(self, url):
        self.dict = requests.get(url).json()
        self.spec = Spec.from_dict(self.dict, config=self.config)


    def select_operations(self, only_resources=None, only_operations_ids=None):
        """
            Filter operations based on resource ids
            and operation ids
        """
        selected_operations = []
        for resource in self.spec.resources.values():
                logging.debug('resource.name = ' + resource.name)
                # Filter operations based on tags (or resource) if provided
                if only_resources == None or resource.name in only_resources:
                        for operation in resource.operations.values():
                                logging.debug('operation.operation_id = ' + operation.operation_id)
                                # Filter operations based on operations_ids if provided
                                if only_operations_ids == None or operation.operation_id in only_operations_ids:
                                        selected_operations.append(operation)

        return selected_operations

    def build_property(self, property_key, property_dict):
        """
            Factory method to build a Property object
            from a swagger schema dict
        """
        if "type" in property_dict:
            if property_dict["type"] == "array":
                if "$ref" in property_dict["items"]:
                    parameter = ObjectsArrayProperty(property_key, property_dict, self)
                elif "type" in property_dict["items"]:
                    parameter = PrimitivesArrayProperty(property_key, property_dict, self)
                else:
                    parameter = InlineObjectsArrayProperty(property_key, property_dict, self)
            elif property_dict["type"] == "object": # or has attr properties ?
                parameter = InlineObjectProperty(property_key, property_dict, self)
            else:
                parameter = PrimitiveProperty(property_key, property_dict, self)
        elif "$ref" in property_dict:
            parameter = ObjectProperty(property_key, property_dict, self)
        else:
            parameter = UnknownProperty(property_key)
        return parameter

    def get_properties_for_model(self, model_name):
        model_dic = self.dict.get("definitions").get(model_name)
        return self.get_properties_for_dict(model_dic)

    def get_properties_for_dict(self, model_dic):
        props = collapsed_properties(model_dic, self.spec)

        properties_list = []
        for property_key in props:
            property_dict = props[property_key]
            property = self.build_property(property_key, property_dict)
            properties_list.append(property)

        return properties_list

    def find_property_by_key(self, properties_array, key):
        for prop in properties_array:
            if prop.key == key:
                return prop
        return None

    def get_body_parameter(self, operation):
        return operation.params.get('body')

    def build_property_from_body_param(self, body_param):
        body_spec = get_param_type_spec(body_param)
        return self.build_property('body', body_spec)

    def get_type_from_param(self, parameter):
        """
            TODO : refactor this. Use the build_property method
            to build standard Property even for main POST params
            But for POST params, we need a additional
            "location" info (header/body/path..), so
            Property object needs to be refactored too
        """
        if "type" in parameter.param_spec:

            # Array
            if parameter.param_spec["type"] == "array":
                if "items" in parameter.param_spec:

                    # Array of primitives
                    if "type" in parameter.param_spec["items"]:
                        return "array of " + parameter.param_spec["items"]["type"]

                    # Array of objects
                    elif "$ref" in parameter.param_spec["items"]:
                        return "array of " + self.extract_model_name(parameter.param_spec["items"]["$ref"])

                    else:
                        return "array of unknown objects"

                else:
                    return "array of unknown"

            # Primitive type
            else:
                return parameter.param_spec["type"]


        # Object
        elif "schema" in parameter.param_spec:
            if "$ref" in parameter.param_spec["schema"]:
                return self.extract_model_name(parameter.param_spec["schema"]["$ref"])
            else:
                return "inline object"

        # Defaut
        else:
            return "unknown"
