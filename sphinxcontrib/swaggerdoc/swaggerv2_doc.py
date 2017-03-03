# -*- coding: utf-8 -*-
import traceback
from docutils import nodes
from docutils.parsers.rst import Directive
from docutils.parsers.rst import directives
from sphinx.locale import _
from sphinxcontrib.swaggerdoc.swagger_source import SwaggerSource


class swaggerv2doc(nodes.General, nodes.Element):
    pass

class SwaggerV2DocDirective(Directive):
    """
        Display list of OpenAPI endpoints from a url or a file

        Examples :

        .. swaggerv2doc:: http://petstore.swagger.io/v2/swagger.json
            :resources: pet,store

        .. swaggerv2doc:: http://petstore.swagger.io/v2/swagger.json
            :operations_ids: getPetById
    """

    has_content = False
    required_arguments = 1
    optional_arguments = 2
    final_argument_whitespace = True

    option_spec = {
        'resources': directives.unchanged,
        'operations_ids': directives.unchanged
    }

    def log(self, message):
        self.env.app.info("[swaggerdoc] " + message)

    def run(self):
        self.env = self.state.document.settings.env

        # Read directive options
        swagger_source_url = self.arguments[0]
        selected_resources = self.get_selected_resources()
        selected_operations_ids = self.get_selected_operations_ids()
        self.log("Running SawaggerDoc directive for url : %s " % self.arguments[0])
        self.log("Selected Resources : %s" % selected_resources)
        self.log("Selected Operations Ids : %s" % selected_operations_ids)

        try:
            # Retrieve and build swagger source
            self.swagger_source = SwaggerSource()
            self.swagger_source.load_from_url(swagger_source_url)

            # Select API methods to render
            selected_operations = self.swagger_source.select_operations(
                only_resources=selected_resources,
                only_operations_ids= selected_operations_ids
            )
            self.log("Number of operations to build: %s" % len(selected_operations))

            # Build
            operations_nodes = self.build_operations_nodes(selected_operations)
            return operations_nodes

        except Exception as e:
            error_message = "Unable to process OpenApi file: %s" % swagger_source_url
            print(error_message)
            traceback.print_exc()

            error = nodes.error()
            error_message_node = nodes.paragraph()
            error_message_node += nodes.Text(error_message)
            error_advice_node = nodes.paragraph()
            error_advice_node += nodes.Text('Please check that the URL is a valid Swagger api-docs URL and it is accesible')
            error += error_message_node
            error += error_advice_node
            return [error]



    def build_operations_nodes(self, selected_operations):
        operations_nodes = []
        for operation in selected_operations:
            operations_nodes.append(self.build_operation_node(operation))
        return operations_nodes

    def build_operation_node(self, operation):
        self.log("Build operation node : %s %s (id: %s)" % (operation.http_method.upper(), operation.path_name, operation.operation_id))
        title = operation.http_method.upper() + ' ' + operation.path_name
        operation_node = nodes.section(ids=[title])
        operation_node += nodes.title(text=title)

        operation_node += self.build_operation_description_node(operation)
        operation_node += self.build_operation_request_node(operation)
        # TODO : operation_node += self.build_operation_response_node(operation)
        return operation_node

    def build_operation_description_node(self, operation):
        title = "Description"
        operation_description_node = nodes.section(ids=[title])
        operation_description_node += nodes.title(text=title)
        operation_description_node += nodes.paragraph(text=operation.op_spec.get('description'))
        return operation_description_node

    def build_operation_request_node(self, operation):
        title = "Request parameters"
        operation_request_node = nodes.section(ids=[title])
        operation_request_node += nodes.title(text=title)

        properties_sections = []

        # Build "main" param table
        self.add_main_params_section(
            properties_sections,
            operation
        )

        # Add all properties sections to the the node
        for properties_section in properties_sections:
            operation_request_node += properties_section

        return operation_request_node

    def create_table_row(self, row_cells):
        row = nodes.row()
        for cell in row_cells:
            entry = nodes.entry()
            row += entry
            entry += nodes.paragraph(text=cell)
        return row

    def add_main_params_section(self, properties_sections, operation):
        """
            Build the Main param section
            Note: this is done in a separate method because the
            main param is a special one: each param of the endpoint
            needs a "location" (header/body/path/...)

            TODO: maye remove this and try to handle the operation
            as an other property to describe
        """
        self.log("Add main params section")
        main_params_header = ['Name', 'Position', 'Description', 'Type']
        main_params_colwidths = [10, 10, 60, 20]

        title = 'Call parameters'
        subsection = nodes.section(ids=[title])
        subsection += nodes.title(text=title)

        # Build Table Header
        thead = nodes.thead()
        thead += self.create_table_row(main_params_header)

        # Build Table Body
        tbody = nodes.tbody()
        parameters = operation.params
        for parameter in parameters: #TODO
            row_data = []
            row_data.append(parameters[parameter].name)
            row_data.append(parameters[parameter].location)
            row_data.append(parameters[parameter].description)
            row_data.append(self.swagger_source.get_type_from_param(parameters[parameter]))
            tbody += self.create_table_row(row_data)

        # Build Table Group
        tgroup = nodes.tgroup(cols=len(main_params_header))
        for colwidth in main_params_colwidths:
            tgroup += nodes.colspec(colwidth=colwidth)

        tgroup += thead
        tgroup += tbody

        # Build Table
        table = nodes.table()
        table += tgroup

        # Add table to the section
        subsection += table
        properties_sections.append(subsection)

        # When a body param exists
        # Build a Property from the body param and a section to describe it
        body_param = self.swagger_source.get_body_parameter(operation)
        if body_param:
            body_property = self.swagger_source.build_property_from_body_param(body_param)
            self.add_nested_params_section(
                properties_sections,
                body_property
            )

    def add_nested_params_section(self, properties_sections, property):
        """
            Build a section and a table for a non primitive Property
            that reference nested other Property

            Note: This method is recursive
            For each nested Property that require a description, we call
            this method on this property to add dedicated section

        """
        self.log("Add nested params section for property : %s" % property.key)

        nested_params_header = ['Name', 'Description', 'Type']
        nested_params_colwidths = [20, 60, 20]

        title = "%s parameter (%s)" % (property.key, property.sub_type)
        subsection = nodes.section(ids=[title])
        subsection += nodes.title(text=title)

        properties = property.nested_properties

        # Build Table Header
        thead = nodes.thead()
        thead += self.create_table_row(nested_params_header)

        # Build Table Body
        tbody = nodes.tbody()
        for prop in properties: #TODO
            row_data = []
            row_data.append(prop.key)
            row_data.append(prop.description)
            row_data.append(prop.type_description())
            tbody += self.create_table_row(row_data)

        # Build Table Group
        tgroup = nodes.tgroup(cols=len(nested_params_header))
        for colwidth in nested_params_colwidths:
            tgroup += nodes.colspec(colwidth=colwidth)

        tgroup += thead
        tgroup += tbody

        # Build Table
        table = nodes.table()
        table += tgroup


        subsection += table
        properties_sections.append(subsection)

        properties_to_describe = property.nested_properties_to_describe()
        for property_to_describe in properties_to_describe:
            self.add_nested_params_section(properties_sections, property_to_describe)



    def get_selected_resources(self):
        resources_option = self.options.get('resources')
        if resources_option:
            return resources_option.split(",")
        return None

    def get_selected_operations_ids(self):
        operations_ids_option = self.options.get('operations_ids')
        if operations_ids_option:
            return operations_ids_option.split(",")
        return None

