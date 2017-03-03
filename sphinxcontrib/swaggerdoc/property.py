class Property(object):
    """
        Abstract Class representing a property of a swagger "model"
        The property can be either :

            * a primitive : integer, string, boolean
            * a complex type:
                - an object described in the swagger "definitions" object
                - an inline object described with a list of properties
                - an array of primitives
                - an array of objects described in the swagger "definitions" object
                - an array of inline objects described with a list of properties
    """

    def __init__(self, key, property_dict, swagger_source):
        super(Property, self).__init__()
        self.swagger_source = swagger_source
        self.key = key
        self.description = property_dict.get('description', "")
        self.property_dict = property_dict


    def type_description(self):
        """
            String description of the Property
            By default return the type of the Property
            Should be overriden for complex a Property
        """
        return self.type

    @property
    def sub_type(self):
        """
            For primitive properties, returns the type of the property,
            For complex properties, returns information about the nested
            types (type of objects in arrays, ...)
        """
        return self.type

    @property
    def nested_properties(self):
        """
            Returns the list of Property nested inside this Property
            This list is empty for primitive or array of primitives Property
        """
        return []

    def nested_properties_to_describe(self):
        """
            Returns the list of nested Properties that needs
            to be described
        """
        types = ['object', 'objects_array', 'inline_objects_array', 'inline_object']
        selected_properties = []
        for prop in self.nested_properties:
            if prop.type in types:
                selected_properties.append(prop)
        return selected_properties

class ObjectProperty(Property):
    """docstring for ObjectProperty"""
    def __init__(self, key, property_dict, swagger_source):
        super(ObjectProperty, self).__init__(key, property_dict, swagger_source)
        self.type = "object"

    @property
    def sub_type(self):
        return self.swagger_source.extract_model_name(self.property_dict.get('$ref'))

    @property
    def nested_properties(self):
        return self.swagger_source.get_properties_for_model(self.sub_type)

    def type_description(self):
        return self.swagger_source.extract_model_name(self.property_dict.get('$ref'))

class ObjectsArrayProperty(Property):
    """docstring for ObjectsArrayProperty"""
    def __init__(self, key, property_dict, swagger_source):
        super(ObjectsArrayProperty, self).__init__(key, property_dict, swagger_source)
        self.type = "objects_array"

    @property
    def sub_type(self):
        return self.swagger_source.extract_model_name(self.property_dict.get('items').get('$ref'))

    @property
    def nested_properties(self):
        return self.swagger_source.get_properties_for_model(self.sub_type)

    def type_description(self):
        objects_name = self.swagger_source.extract_model_name(self.property_dict.get('items').get('$ref'))
        return "Array of " + self.sub_type

class PrimitivesArrayProperty(Property):
    def __init__(self, key, property_dict, swagger_source):
        super(PrimitivesArrayProperty, self).__init__(key, property_dict, swagger_source)
        self.type = "primitives_array"

    @property
    def sub_type(self):
        return self.property_dict.get('items').get('type')

    def type_description(self):
        return "Array of " + self.sub_type

class InlineObjectsArrayProperty(Property):
    def __init__(self, key, property_dict, swagger_source):
        super(InlineObjectsArrayProperty, self).__init__(key, property_dict, swagger_source)
        self.type = "inline_objects_array"

    @property
    def sub_type(self):
        return "Object"

    def type_description(self):
        return "Array of objects"

    @property
    def nested_properties(self):
        model_dict = self.swagger_source.extract_model_name(self.property_dict.get('items').get("properties"))
        return self.swagger_source.get_properties_for_dict(model_dict)

class PrimitiveProperty(Property):
    def __init__(self, key, property_dict, swagger_source):
        super(PrimitiveProperty, self).__init__(key, property_dict, swagger_source)
        self.type = property_dict.get('type', "")

class InlineObjectProperty(Property):
    def __init__(self, key, property_dict, swagger_source):
        super(InlineObjectProperty, self).__init__(key, property_dict, swagger_source)
        self.type = "inline_object"

    @property
    def sub_type(self):
        return "Object"

    @property
    def nested_properties(self):
        return self.swagger_source.get_properties_for_dict(self.property_dict)

    def type_description(self):
        return "Object"

class UnknownProperty(Property):
    def __init__(self, key, property_dict, swagger_source):
        super(UnknownProperty, self).__init__(key)
        self.type = "unknown"
