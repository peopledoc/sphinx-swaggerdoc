import unittest
import json

from sphinxcontrib.swaggerdoc.swagger_source import SwaggerSource
from sphinxcontrib.swaggerdoc.property import *

from bravado_core.param import Param

class TestSwaggerSource(unittest.TestCase):
    def setUp(self):
        spec_dict = json.loads(open('tests/swagger_files/petstore.json', 'r').read())
        self.swagger_source = SwaggerSource()
        self.swagger_source.load_from_dict(spec_dict)

    def test_select_operations(self):
        # By resources
        operations = self.swagger_source.select_operations(only_resources=['pet'])
        self.assertEqual(8, len(operations))

        # By resource id
        operations = self.swagger_source.select_operations(
          only_operations_ids=['addPet', 'uploadFile', 'getInventory']
        )
        self.assertEqual(3, len(operations))

    def test_get_properties_for_model(self):
        """
            Tests building properties for the Pet & Tag Model

            ```json
            "Pet":{
              "type":"object",
              "required":["name","photoUrls"],
              "properties":{
                "id":{"type":"integer","format":"int64"},
                "category":{"$ref":"#/definitions/Category"},
                "name":{"type":"string","example":"doggie"},
                "photoUrls":{"type":"array","items":{"type":"string"}},
                "tags":{"type":"array","items":{"$ref":"#/definitions/Tag"}},
                "status":{"type":"string","description":"pet status in the store","enum":["available","pending","sold"]}
              },
            },
            "Tag":{
              "type":"object",
              "properties":{
                "id":{"type":"integer","format":"int64"},
                "name":{"type":"string"}
              }
            }
            ```
        """
        properties = self.swagger_source.get_properties_for_model("Pet")
        self.assertIsNotNone(properties)
        self.assertEqual(6, len(properties))
        self.assertIsInstance(properties[0], Property)

        id_property = self.swagger_source.find_property_by_key(properties, "id")
        self.assertIsInstance(id_property, PrimitiveProperty)

        category_property = self.swagger_source.find_property_by_key(properties, "category")
        self.assertIsInstance(category_property, ObjectProperty)

        photo_urls_property = self.swagger_source.find_property_by_key(properties, "photoUrls")
        self.assertIsInstance(photo_urls_property, PrimitivesArrayProperty)

        tags_property = self.swagger_source.find_property_by_key(properties, "tags")
        self.assertIsInstance(tags_property, ObjectsArrayProperty)

    def test_nested_properties(self):
        """
            Tests building nested properties for the Pet & Tag Model
        """

        properties = self.swagger_source.get_properties_for_model("Pet")
        tags_property = self.swagger_source.find_property_by_key(properties, "tags")
        nested_tag_properties = tags_property.nested_properties

        self.assertEqual(2, len(nested_tag_properties))
        tag_id_property = self.swagger_source.find_property_by_key(nested_tag_properties, "id")
        self.assertIsInstance(tag_id_property, PrimitiveProperty)
        self.assertEqual(tag_id_property.sub_type, "integer")

    def test_extract_model_name(self):
        ref = "#/definitions/TestModel"
        self.assertEqual("TestModel", self.swagger_source.extract_model_name(ref))

        ref = "TestModel"
        self.assertEqual("TestModel", self.swagger_source.extract_model_name(ref))

    def test_build_property_from_body_param_object(self):
        """
            "/pet":{
              "post":{
                "tags":["pet"],
                ...
                "parameters":[
                  {
                    "in":"body",
                    "name":"body",
                    "description":"Pet object that needs to be added to the store",
                    "required":true,
                    "schema":{
                      "$ref":"#/definitions/Pet"
                  }
                 }
                ],
              }
            }
        """
        operation = self.swagger_source.select_operations(only_operations_ids=['addPet'])[0]
        body_param = self.swagger_source.get_body_parameter(operation)

        self.assertIsNotNone(body_param)
        self.assertIsInstance(body_param, Param)

        property = self.swagger_source.build_property_from_body_param(body_param)

        self.assertIsInstance(property, Property)
        self.assertIsInstance(property, ObjectProperty)

    def test_build_property_from_body_param_objects_array(self):
      """
        "/user/createWithList":{
         "post":{
            "tags":["user"],
            ...
            "parameters":[
               {
                  "in":"body",
                  "name":"body",
                  "description":"List of user object",
                  "required":true,
                  "schema":{
                     "type":"array",
                     "items":{
                        "$ref":"#/definitions/User"
                     }
                  }
               }
            ],
          }
        }
      """
      operation = self.swagger_source.select_operations(only_operations_ids=['createUsersWithListInput'])[0]
      body_param = self.swagger_source.get_body_parameter(operation)
      self.assertIsInstance(body_param, Param)
      property = self.swagger_source.build_property_from_body_param(body_param)
      self.assertIsInstance(property, Property)
      self.assertIsInstance(property, ObjectsArrayProperty)
