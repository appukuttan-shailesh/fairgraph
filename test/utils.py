# encoding: utf-8
"""
Utility classes and functions for testing fairgraph, in particular various mock objects
including a mock Http client which returns data loaded from the files in the test_data directory.
"""

import json
import os
import random
from datetime import datetime
from copy import deepcopy
try:
    from urllib.parse import parse_qs, urlparse
    basestring = str
except ImportError:
    from urlparse import parse_qs, urlparse  # py2

import uuid

import pytest
from openid_http_client.http_client import HttpClient

from pyxus.client import NexusClient, NexusConfig
from pyxus.resources.entity import Instance
from pyxus.resources.repository import (ContextRepository, DomainRepository,
                                        InstanceRepository,
                                        OrganizationRepository,
                                        SchemaRepository)
import fairgraph.client
from fairgraph.base import as_list, KGObject, MockKGObject, KGProxy
from fairgraph.commons import QuantitativeValue, OntologyTerm


test_data_lookup = {}


class MockHttpClient(HttpClient):

    def __init__(self, *args, **kwargs):
        #super().__init__(*args, **kwargs)  # for when we drop Python 2 support
        super(MockHttpClient, self).__init__(*args, **kwargs)
        self.cache = {}
        self.request_count = 0

    def _request(self, method_name, endpoint_url, data=None, headers=None, can_retry=True):
        self.request_count += 1
        full_url = self._create_full_url(endpoint_url)
        print(full_url)
        parts = urlparse(full_url)
        query = parse_qs(parts.query)
        # to do: handle the query part
        if method_name == 'get':
            test_data_path = test_data_lookup[parts.path]
            if test_data_path in self.cache:
                data = self.cache[test_data_path]
            else:
                with open(test_data_path, "r") as fp:
                    data = json.load(fp)
                self.cache[test_data_path] = data
            if "filter" in parts.query:
                query = parse_qs(parts.query)
                filtr = eval(query['filter'][0])
                if filtr.get("path") == "nsg:brainLocation / nsg:brainRegion":
                    results = [item for item in data["results"]
                               if as_list(item["source"]["brainLocation"]["brainRegion"])[0]["@id"] == filtr["value"]]
                elif filtr.get("path") in ("schema:givenName", "schema:familyName"):
                    results = [item for item in data["results"]
                               if item["source"][filtr["path"].split(":")[1]] == filtr["value"]]
                elif filtr.get("path") == "prov:used / rdf:type":
                    results = [item for item in data["results"]
                               if filtr["value"] in data["results"][0]["source"]["prov:used"]["@type"]]
                elif "op" in filtr:
                    # James Bond does not exist
                    if filtr["value"][0]["value"] in ("James", "Bond"):
                        results = []
                    elif filtr["value"][0]["value"] in ("Katherine", "Johnson"):
                        results = [item for item in data["results"]
                                   if item["source"]["familyName"] == "Johnson"]
                else:
                    raise NotImplementedError("todo")
                data = deepcopy(data)  # don't want to mess with the cache
                data["results"] = results
            return data
        elif method_name == 'post':
            # assume success, generate random uuid
            response = {
                "@context": "https://nexus-int.humanbrainproject.org/v0/contexts/nexus/core/resource/v0.3.0",
                "@id": "https://nexus-int.humanbrainproject.org/v0{}/{}".format(endpoint_url, uuid.uuid4()),
                "nxv:rev": 1
            }
            return response
        else:
            raise NotImplementedError("to do")


class MockNexusClient(NexusClient):

    def __init__(self, scheme=None, host=None, prefix=None, alternative_namespace=None, auth_client=None):
        self.version = None
        self.namespace = alternative_namespace if alternative_namespace is not None else "{}://{}".format(scheme, host)
        self.env = None
        self.config = NexusConfig(scheme, host, prefix, alternative_namespace)
        self._http_client = MockHttpClient(self.config.NEXUS_ENDPOINT, self.config.NEXUS_PREFIX, auth_client=auth_client,
                                           alternative_endpoint_writing=self.config.NEXUS_NAMESPACE)
        self.domains = DomainRepository(self._http_client)
        self.contexts = ContextRepository(self._http_client)
        self.organizations = OrganizationRepository(self._http_client)
        self.instances = InstanceRepository(self._http_client)
        self.schemas = SchemaRepository(self._http_client)


@pytest.fixture
def kg_client():
    fairgraph.client.NexusClient = MockNexusClient
    client = fairgraph.client.KGClient("thisismytoken")
    #token = os.environ["HBP_token"]
    #client = fairgraph.client.KGClient(token)
    return client


lorem_ipsum = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor
incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation
ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit
in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat
non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""

lli = len(lorem_ipsum)


def _random_text():
    start = random.randint(0, lli//2)
    end = random.randint(lli//2, lli)
    return lorem_ipsum[start:end]


def random_uuid():
    return uuid.uuid4()


def generate_random_object(cls, all_fields=True):
    attrs = {}
    for field in cls.fields:
        if all_fields or field.required:
            obj_type = field.types[0]  # todo: pick randomly if len(field.types) > 1
            if not field.intrinsic:
                value = None
            elif obj_type == basestring:
                value = _random_text()
            elif obj_type == int:
                value = random.randint(1, 10)
            elif issubclass(obj_type, KGObject):
                if obj_type == KGObject:
                    # specific type is not determined
                    # arbitrarily, let's choose minds.Dataset
                    value = MockKGObject(id=random_uuid(), type=["minds:Dataset"])
                else:
                    value = MockKGObject(id=random_uuid(), type=getattr(obj_type, "type", None))
            elif obj_type == QuantitativeValue:
                # todo: subclass QV so we can specify the required dimensionality in `fields`
                value = QuantitativeValue(random.uniform(-10, 10),
                                        random.choice(list(QuantitativeValue.unit_codes)))
            elif issubclass(obj_type, OntologyTerm):
                value = obj_type(random.choice(list(obj_type.iri_map)))
            elif obj_type == datetime:
                value = datetime.now()
            elif obj_type == bool:
                value = random.choice([True, False])
            else:
                raise NotImplementedError(str(obj_type))
            attrs[field.name] = value
    return cls(**attrs)


class BaseTestKG(object):

    def test_round_trip_random(self, kg_client):
        cls = self.class_under_test
        if cls.fields:
            obj1 = generate_random_object(cls)
            instance = Instance(cls.path, obj1._build_data(kg_client), Instance.path)
            instance.data["@id"] = random_uuid()
            instance.data["@type"] = cls.type
            obj2 = cls.from_kg_instance(instance, kg_client)
            for field in cls.fields:
                if field.intrinsic:
                    val1 = getattr(obj1, field.name)
                    val2 = getattr(obj2, field.name)
                    if issubclass(field.types[0], KGObject):
                        assert isinstance(val1, MockKGObject)
                        assert isinstance(val2, KGProxy)
                        assert val1.type == val2.cls.type
                    else:
                        assert val1 == val2
                # todo: test non-intrinsic fields

    def test_round_trip_minimal_random(self, kg_client):
        cls = self.class_under_test
        if cls.fields:
            obj1 = generate_random_object(cls, all_fields=False)
            instance = Instance(cls.path, obj1._build_data(kg_client), Instance.path)
            instance.data["@id"] = random_uuid()
            instance.data["@type"] = cls.type
            obj2 = cls.from_kg_instance(instance, kg_client)
            for field in cls.fields:
                if field.intrinsic and field.required:
                    val1 = getattr(obj1, field.name)
                    val2 = getattr(obj2, field.name)
                    if issubclass(field.types[0], KGObject):
                        assert isinstance(val1, MockKGObject)
                        assert isinstance(val2, KGProxy)
                        assert val1.type == val2.cls.type
                    else:
                        assert val1 == val2
                # todo: test non-intrinsic fields