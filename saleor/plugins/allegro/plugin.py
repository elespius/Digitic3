from dataclasses import dataclass
from datetime import datetime
from typing import Any
from saleor.product.models import Product, AssignedProductAttribute, \
    AttributeValue
from saleor.plugins.models import PluginConfiguration
from django.shortcuts import redirect
from saleor.plugins.base_plugin import BasePlugin, ConfigurationTypeField
import requests
import webbrowser
import csv
import json
import uuid
from collections import defaultdict

@dataclass
class AllegroConfiguration:
    is_connected: str
    token_access: str
    token_value: str

class AllegroPlugin(BasePlugin):

    PLUGIN_ID = "allegro"
    PLUGIN_NAME = "Allegro"
    PLUGIN_NAME_2 = "Allegro"
    META_CODE_KEY = "AllegroPlugin.code"
    META_DESCRIPTION_KEY = "AllegroPlugin.description"
    DEFAULT_CONFIGURATION = [{"name": "is_connected", "value": None}, {"name": "token_access", "value": None}, {"name": "token_value", "value": None}]
    CONFIG_STRUCTURE = {
        "is_connected": {
            "type": ConfigurationTypeField.SECRET,
            "label": "Czy jest powiązdanie z Allegro?",
        },
        "token_access": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Pokazuje XXX:XXX.",
            "label": "Ważność tokena do:",
        },
        "token_value": {
            "type": ConfigurationTypeField.SECRET,
            "help_text": "Access token.",
            "label": "Wartość tokena.",
        }

    }

    DEFAULT_REDIRECT_URI = 'https://allegro.pl.allegrosandbox.pl/auth/oauth'
    CLIENT_ID = '55ad2cda731c4160a001fb195bd47b2d'
    CLIENT_SECRET = '71Uv6BqXFwVnhgw828COleU1swy5ZPG0TOb0dtTcfOzj5u0EvWrapeKly4N5fMnB'
    CALLBACK_URL = 'http://localhost:8000/allegro'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        configuration = {item["name"]: item["value"] for item in self.configuration}

        self.config = AllegroConfiguration(is_connected=configuration["is_connected"], token_access=configuration["token_access"], token_value=configuration["token_value"])

        if(configuration['token_value'] == None):
            allegro_auth = AllegroAuth()
            allegro_auth.get_access_code(self.CLIENT_ID, self.CLIENT_SECRET, self.CALLBACK_URL, self.DEFAULT_REDIRECT_URI)

    @classmethod
    def validate_plugin_configuration(cls, plugin_configuration: "PluginConfiguration"):
        """Validate if provided configuration is correct."""
        configuration = plugin_configuration.configuration
        configuration = {item["name"]: item["value"] for item in configuration}

        access_key = configuration.get("Access key")

    @classmethod
    def save_plugin_configuration(cls, plugin_configuration: "PluginConfiguration", cleaned_data):

        current_config = plugin_configuration.configuration

        configuration_to_update = cleaned_data.get("configuration")

        if configuration_to_update:
            cls._update_config_items(configuration_to_update, current_config)
        if "active" in cleaned_data:
            plugin_configuration.active = cleaned_data["active"]
        cls.validate_plugin_configuration(plugin_configuration)
        plugin_configuration.save()
        if plugin_configuration.configuration:
            # Let's add a translated descriptions and labels
            cls._append_config_structure(plugin_configuration.configuration)
        return plugin_configuration





    def product_created(self, product: "Product", previous_value: Any) -> Any:

        # manager = get_plugins_manager()
        # plugin = manager.get_plugin(AllegroPlugin.PLUGIN_ID)
        # print('Token', plugin.config.token_value)

        print('Product create')

        allegro_api = AllegroAPI(self.config.token_value)
        allegro_api.product_publish(saleor_product=product)

class AllegroAuth:

    def get_access_code(self, client_id, api_key, redirect_uri,
                        oauth_url):
        # zmienna auth_url zawierać będzie zbudowany na podstawie podanych parametrów URL do zdobycia kodu
        auth_url = '{}/authorize' \
                   '?response_type=code' \
                   '&client_id={}' \
                   '&api-key={}' \
                   '&redirect_uri={}&prompt=confim'.format(oauth_url, client_id, api_key,
                                                         redirect_uri)

        webbrowser.open(auth_url)

        return True


    def sign_in(self, client_id, client_secret, access_code, redirect_uri, oauth_url):


        token_url = oauth_url + '/token'

        access_token_data = {'grant_type': 'authorization_code',
                             'code': access_code,
                             'redirect_uri': redirect_uri}

        response = requests.post(url=token_url,
                                 auth=requests.auth.HTTPBasicAuth(client_id, client_secret), data=access_token_data)
        access_token = response.json()['access_token']

        print('accessToken: ' + access_token)

        cleaned_data = {
            "configuration": [{"name": "token_value", "value": access_token}]}

        AllegroPlugin.save_plugin_configuration(plugin_configuration=PluginConfiguration.objects.get(
            identifier=AllegroPlugin.PLUGIN_ID), cleaned_data=cleaned_data, )

        return response.json()


    def resolve_auth(request):

        allegro_auth = AllegroAuth()

        access_code = request.GET["code"]

        CLIENT_ID = '55ad2cda731c4160a001fb195bd47b2d'
        CLIENT_SECRET = '71Uv6BqXFwVnhgw828COleU1swy5ZPG0TOb0dtTcfOzj5u0EvWrapeKly4N5fMnB'
        CALLBACK_URL = 'http://localhost:8000/allegro'
        DEFAULT_REDIRECT_URI = 'https://allegro.pl.allegrosandbox.pl/auth/oauth'

        allegro_auth.sign_in(CLIENT_ID, CLIENT_SECRET, access_code,
                              CALLBACK_URL, DEFAULT_REDIRECT_URI)


        return redirect('http://localhost:9000')


class AllegroAPI:

    token = None

    def __init__(self, token):
        self.token = token


    def get_category(self, id):

        path = '/Users/patryk/data_with_ids.csv'

        dictionary_with_categories = csv.DictReader(open(path))
        category = next(filter(lambda p: p['id'] == str(id), dictionary_with_categories), None)

        return category


    def product_publish(self, saleor_product) :

        # print('Is published ', ['http://localhost:8000' + pi.image.url for pi in ProductImage.objects.filter(product=product)])

        if saleor_product.private_metadata.get('publish.target') and saleor_product.private_metadata.get('publish.target') == 'allegro'\
                and saleor_product.private_metadata.get('publish.status') == 'unpublished':

            category = self.get_category(saleor_product.product_type.id)
            require_parameters = self.get_require_parameters(category['index'])

            parameters_mapper = ParametersMapperFactory().getMapper(category['name'])

            parameters = parameters_mapper.set_product(saleor_product).set_category(category).set_require_parameters(require_parameters).run_mapper()

            product_mapper = ProductMapperFactory().getMapper()

            allegro_product = self.create_allegro_api_product(product=saleor_product, parameters=parameters, category_id=category['index'])


            product = product_mapper.set_saleor_product(saleor_product) \
                .set_saleor_images(self.upload_images())\
                .set_saleor_parameters(parameters)\
                .set_saleor_category(category).run_mapper()



            offer = self.publish_to_allegro(allegro_product=product)

            if 'errors' in offer:
                print('Wystąpił bład z zapisem', offer['errors'])
            else:
                self.update_status_and_publish_data_in_private_metadata(saleor_product)
                offer_publication = self.offer_publication(offer['id'])
        else:
            self.set_allegro_private_metadata(saleor_product)



    def publish_to_allegro(self, allegro_product):

        endpoint = 'sale/offers'
        response = self.post_request(endpoint=endpoint, data=allegro_product)
        return json.loads(response.text)

    def post_request(self, endpoint, data):

        url = 'https://api.allegro.pl.allegrosandbox.pl/' + endpoint
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.post(url, data=json.dumps(data), headers=headers)

        return response

    def get_request(self, endpoint):

        url = 'https://api.allegro.pl.allegrosandbox.pl/' + endpoint
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.get(url, headers=headers)

        return response

    def put_request(self, endpoint, data):

        url = 'https://api.allegro.pl.allegrosandbox.pl/' + endpoint
        headers = {'Authorization': 'Bearer ' + self.token,
                   'Accept': 'application/vnd.allegro.public.v1+json',
                   'Content-Type': 'application/vnd.allegro.public.v1+json'}
        response = requests.put(url, data=json.dumps(data), headers=headers)

        return response


    def get_require_parameters(self, category_id):

        endpoint = 'sale/categories/' + category_id + '/parameters'
        response = self.get_request(endpoint)
        requireParams = [param for param in json.loads(response.text)['parameters'] if param['required'] == True]

        return requireParams



    def create_allegro_api_product(self, product, parameters, category_id):

        nested_dict = lambda: defaultdict(nested_dict)
        allegro_product = nested_dict()

        allegro_product['afterSalesServices'] = {}
        allegro_product['afterSalesServices']['impliedWarranty']= {"id": "59f8273f-6dff-4242-a6c2-60dd385e9525"}
        allegro_product['afterSalesServices']['returnPolicy'] = {"id": "8b0ecc6b-8812-4b0f-b8a4-a0b56585c403"}
        allegro_product['afterSalesServices']['warranty'] = {"id": "d3605a54-3cfb-4cce-8e1b-1c1adafb498c"}
        allegro_product['category'] = {}
        allegro_product['delivery'] = {}
        allegro_product['delivery']['additionalInfo'] = 'test'
        allegro_product['delivery']['handlingTime'] = 'PT72H'
        allegro_product['delivery']['shipmentDate'] = '2020-07-24T08:03:59Z'
        allegro_product['delivery']['shippingRates'] = { "id": "9d7f48de-87a3-449f-9028-d83512a17003" }
        allegro_product['location'] = {}
        allegro_product['location']['countryCode'] = 'PL'
        allegro_product['location']['province'] = 'WIELKOPOLSKIE'
        allegro_product['location']['city'] = 'Pozna\u0144'
        allegro_product['location']['postCode'] = '60-122'
        allegro_product['payments'] = {}
        allegro_product['payments']['invoice'] = 'NO_INVOICE'
        allegro_product['sellingMode'] = {}
        allegro_product['sellingMode']['format'] = 'AUCTION'
        allegro_product['sellingMode']['startingPrice'] = {}
        allegro_product['sellingMode']['startingPrice']['amount'] = str(product.minimal_variant_price_amount)
        allegro_product['sellingMode']['startingPrice']['currency'] = 'PLN'
        allegro_product['name'] = product.name


        allegro_product['images'] = [
                {
                    "url": self.upload_images()
                }]

        allegro_product['description'] = {}

        product_sections = []
        product_items = []


        product_items.append({
            'type': 'TEXT',
            'content': '<h1>' + product.plain_text_description + '</h1>'
        })

        product_sections.append({'items': product_items})

        allegro_product['description']['sections'] = product_sections


        allegro_product['stock'] = {}
        allegro_product['stock']['available'] = 1
        allegro_product['stock']['unit'] = 'SET'

        allegro_product['publication'] = {}
        allegro_product['publication']['duration'] = 'PT72H'
        allegro_product['publication']['endingAt'] = ''
        allegro_product['publication']['startingAt'] = '2020-07-24T08:03:59Z'
        allegro_product['publication']['status'] = 'INACTIVE'
        allegro_product['publication']['endedBy'] = 'USER'
        allegro_product['publication']['republish'] = 'False'
        allegro_product['parameters'] = []
        allegro_product['parameters'] = parameters
        allegro_product['category'] = {'id': category_id}

        return allegro_product



    def upload_images(self):

        endpoint = 'sale/images'

        data = {
             "url": "https://cdn.shoplo.com/0986/products/th2048/bca3/197520-eleganckie-body-z-dekoltem-v.jpg"
        }

        response = self.post_request(endpoint=endpoint, data=data)

        return json.loads(response.text)['location']

    def update_status_and_publish_data_in_private_metadata(self, product):

        product.store_value_in_private_metadata({'publish.status': 'published'})
        product.store_value_in_private_metadata({'publish.date': datetime.today().strftime('%Y-%m-%d-%H:%M:%S')})
        product.save(update_fields=["private_metadata"])

    def set_allegro_private_metadata(self, product):

        product.store_value_in_private_metadata({'publish.target': 'allegro'})
        product.store_value_in_private_metadata({'publish.status': 'unpublished'})
        product.store_value_in_private_metadata({'publish.date': ''})
        product.save(update_fields=["private_metadata"])

    def offer_publication(self, offer_id):

        endpoint = 'sale/offer-publication-commands/' + str(uuid.uuid1())
        data = {
            "publication": {
                "action": "ACTIVATE"
            },
            "offerCriteria": [
                {
                    "offers": [
                        {
                            "id": offer_id
                        }
                    ],
                    "type": "CONTAINS_OFFERS"
                }
            ]
        }
        response = self.put_request(endpoint=endpoint, data=data)

        return json.loads(response.text)


class ParametersMapper:

    def __init__(self, mapper):
        self.mapper = mapper

    def mapper(self):
        return self.mapper.map()


class SimpleParametersMapper():

    def __init__(self):
        self.mapped_parameters = []

    def map(self):
        return self

    def set_product_attributes(self, product_attributes):
        self.product_attributes = product_attributes

        return self

    def set_require_parameters(self, require_parameters):
        self.require_parameters = require_parameters

        return self

    def map_state(self):

        PARAMETER_NAME = 'Stan'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_brand(self):

        PARAMETER_NAME = 'Marka'


        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_size(self):


        PARAMETER_NAME = 'Rozmiar'


        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_fashion(self):


        PARAMETER_NAME = 'Fason'


        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))

        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))


        return self


    def map_set(self):


        PARAMETER_NAME = 'Zestaw'


        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))

        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self


    def map_pattern(self):

        PARAMETER_NAME = 'Wzór dominujący'


        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_color(self):

        PARAMETER_NAME = 'Kolor'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_material(self):

        PARAMETER_NAME = 'Materiał dominujący'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_clasp(self):

        PARAMETER_NAME = 'Zapięcie'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_type(self):

        PARAMETER_NAME = 'Rodzaj'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def map_features(self):

        PARAMETER_NAME = 'Cechy dodatkowe'

        if PARAMETER_NAME in [attributes['name'] for attributes in self.product_attributes]:
            attribute = next((attribute for attribute in self.product_attributes if
                              attribute["name"] == PARAMETER_NAME), False)

            self.mapped_parameters.append(self.assign_parameter(attribute))
        else:
            self.mapped_parameters.append(self.assign_missing_parameter(PARAMETER_NAME))

        return self

    def get_product_attributes(self):

        assigned_product_attributes = AssignedProductAttribute.objects.filter(
            product=self.product)

        attributes = []

        for assigned_product_attribute in assigned_product_attributes:
            try:
                attributes.append(
                    {'name': str(assigned_product_attribute.assignment.attribute),
                     'value': str(AttributeValue.objects.get(
                         assignedproductattribute=assigned_product_attribute))})
            except AttributeValue.DoesNotExist:
                pass

        attributes_name = [str(attribute['name']).split(' ')[0] for attribute in
                           attributes]

        return attributes, attributes_name

    def run_mapper(self):

        product_attributes, product_attributes_name = self.get_product_attributes()

        self.set_product_attributes(product_attributes)

    def assign_parameter(self, atr):

        param = next((param for param in self.require_parameters if
                      param["name"] ==
                      str(atr.get('name'))), False)
        value = next((value for value in param['dictionary'] if
                      value["value"] == str(atr.get('value'))), False)

        return {'id': param['id'], 'valuesIds': [value['id']], "values": [],
                "rangeValue": None}

    def assign_missing_parameter(self, name):

        param = next((param for param in self.require_parameters if
                      param["name"] == name), False)

        value = param['dictionary'][0]

        return {'id': param['id'], 'valuesIds': [value['id']], "values": [],
                "rangeValue": None}

class ComplexParametersMapper(SimpleParametersMapper):

    def map(self):
        return self

    def set_product(self, product):
        self.product = product

        return self

    def set_category(self, category):
        self.category = category

        return self

    def run_mapper(self):

        attributes, attributes_name = self.get_product_attributes()

        self.set_product_attributes(attributes)




        for require_parameter in self.require_parameters:
            self.assign_mapper(require_parameter['name'])

        return self.mapped_parameters

    def append_missing_categories(self, parameters, missing_parameters):

        for missing_parameter in missing_parameters:
            parameters.append(missing_parameter)

        return parameters

    def assign_mapper(self, parameter):

        print(parameter)

        if parameter == 'Stan':
            self.map_state()

        if parameter == 'Marka':
            self.map_brand()

        if parameter == 'Rozmiar':
            self.map_size()

        if parameter == 'Kolor':
            self.map_color()

        if parameter == 'Fason':
            self.map_fashion()

        if parameter == 'Zestaw':
            self.map_set()

        if parameter == 'Wzór dominujący':
            self.map_pattern()

        if parameter == 'Materiał dominujący':
            self.map_material()

        if parameter == 'Cechy dodatkowe':
            self.map_features()

        if parameter == 'Zapięcie':
            self.map_clasp()

        if parameter == 'Rodzaj':
            self.map_type()


class ParametersMapperFactory:

    def getMapper(self, category):

        if category == 'Body':
            mapper = ParametersMapper(SimpleParametersMapper).mapper()
            return mapper

        if category == 'Majtki':
            mapper = ParametersMapper(ComplexParametersMapper).mapper()
            return mapper

        else:
            mapper = ParametersMapper(ComplexParametersMapper).mapper()
            return mapper


class ProductMapper:

    def __init__(self, mapper):
        self.mapper = mapper

    def mapper(self):
        return self.mapper.map()





class ProductMapperFactory:

    def getMapper(self):

        mapper = ProductMapper(AllegroProductMapper).mapper()
        return mapper

class AllegroProductMapper:

    def __init__(self):

        nested_dict = lambda: defaultdict(nested_dict)
        nest = nested_dict()
        self.product = nest

    def map(self):
        return self

    def set_saleor_product(self, saleor_product):
        self.saleor_product = saleor_product
        return self

    def set_implied_warranty(self, id):
        self.product['afterSalesServices']['impliedWarranty']['id'] = id
        return self

    def set_return_policy(self, id):
        self.product['afterSalesServices']['returnPolicy']['id'] = id
        return self

    def set_warranty(self, id):
        self.product['afterSalesServices']['warranty']['id'] = id
        return self

    def set_category(self, category):
        self.product['category']['id'] = category
        return self

    def set_saleor_category(self, category):
        self.saleor_category = category
        return self

    def set_delivery_additional_info(self, id):
        self.product['delivery']['additionalInfo'] = id
        return self

    def set_delivery_handling_time(self, id):
        self.product['delivery']['handlingTime'] = id
        return self

    def set_delivery_shipment_date(self, id):
        self.product['delivery']['shipmentDate'] = id
        return self

    def set_delivery_shipping_rates(self, id):
        self.product['delivery']['shippingRates']['id'] = id
        return self

    def set_location_country_code(self, id):
        self.product['location']['countryCode'] = id
        return self

    def set_location_province(self, id):
        self.product['location']['province'] = id
        return self

    def set_location_city(self, id):
        self.product['location']['city'] = 'Poznań'
        return self

    def set_location_post_code(self, id):
        self.product['location']['postCode'] = id
        return self

    def set_invoice(self, id):
        self.product['payments']['invoice'] = id
        return self

    def set_format(self, id):
        self.product['sellingMode']['format'] = id
        return self

    def set_starting_price_amount(self, id):
        self.product['sellingMode']['startingPrice']['amount'] = id
        return self

    def set_starting_price_currency(self, id):
        self.product['sellingMode']['startingPrice']['currency'] = id
        return self

    def set_name(self, id):
        self.product['name'] = id
        return self

    def set_saleor_images(self, id):
        self.saleor_images = id
        return self

    def set_images(self, id):

        self.product['images'] = [{'url': id}]
        return self


    def set_description(self, id):

        product_sections = []
        product_items = []

        product_items.append({
            'type': 'TEXT',
            'content': '<h1>' + id + '</h1>'
        })

        product_sections.append({'items': product_items})

        self.product['description']['sections'] = product_sections

        return self

    def set_stock_available(self, id):
        self.product['stock']['available'] = id
        return self

    def set_stock_unit(self, id):
        self.product['stock']['unit'] = id
        return self

    def set_publication_duration(self, id):
        self.product['publication']['duration'] = id
        return self

    def set_publication_ending_at(self, id):
        self.product['publication']['endingAt'] = id
        return self

    def set_publication_starting_at(self, id):
        self.product['publication']['startingAt'] = id
        return self

    def set_publication_status(self, id):
        self.product['publication']['status'] = id
        return self

    def set_publication_ended_by(self, id):
        self.product['publication']['endedBy'] = id
        return self

    def set_publication_republish(self, id):
        self.product['publication']['republish'] = id
        return self

    def set_saleor_parameters(self, id):
        self.saleor_parameters = id
        return self

    def set_parameters(self, id):
        self.product['parameters'] = id
        return self



    def run_mapper(self):

        self.set_implied_warranty('59f8273f-6dff-4242-a6c2-60dd385e9525')
        self.set_return_policy('8b0ecc6b-8812-4b0f-b8a4-a0b56585c403')
        self.set_warranty('d3605a54-3cfb-4cce-8e1b-1c1adafb498c')
        self.set_category(self.saleor_category['index'])
        self.set_delivery_additional_info('test')
        self.set_delivery_handling_time('PT72H')
        self.set_delivery_shipment_date('2020-07-24T08:03:59Z')
        self.set_delivery_shipping_rates('9d7f48de-87a3-449f-9028-d83512a17003')

        self.set_location_country_code('PL')
        self.set_location_province('WIELKOPOLSKIE')
        self.set_location_city('Pozna\u0144')
        self.set_location_post_code('60-122')

        self.set_invoice('NO_INVOICE')

        self.set_format('AUCTION')

        self.set_starting_price_amount(str(self.saleor_product.minimal_variant_price_amount))
        self.set_starting_price_currency('PLN')
        self.set_name(self.saleor_product.name)
        self.set_images(self.saleor_images)

        self.set_description(self.saleor_product.plain_text_description)

        # FIXME: po sprzedaniu przedmiotu na tym parametrze update?
        self.set_stock_available('1')

        self.set_stock_unit('SET')
        self.set_publication_duration('PT72H')
        self.set_publication_ending_at('')
        self.set_publication_starting_at('2020-07-24T08:03:59Z')
        self.set_publication_status('INACTIVE')
        self.set_publication_ended_by('USER')
        self.set_publication_republish('False')

        self.set_parameters(self.saleor_parameters)

        return self.product
