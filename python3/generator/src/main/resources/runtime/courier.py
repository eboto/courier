# Copyright 2017 Coursera Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# =============================================================================
""" The courier runtime.

This file was created and placed here during schema generation, so don't bother
editing it. If we were doing this right we would distribute it as a package
through `pip`, and that will probably eventually happen, but until then it gets
generated right here. Where it's safe.
"""



import avro.io
import avro.schema
import json
from collections.abc import MutableSequence, MutableMapping

def parse(courier_type, json_str):
    if (isinstance(json_str, bytes)):
        json_str = json_str.decode('utf-8')
    json_obj = json.loads(json_str)
    needs_validation = hasattr(courier_type, 'AVRO_SCHEMA') and courier_type.AVRO_SCHEMA is not INVALID_SCHEMA
    if (not needs_validation or avro.io.Validate(courier_type.AVRO_SCHEMA, json_obj)):
        constructor = courier_type.from_data if (hasattr(courier_type, 'from_data')) else courier_type
        return constructor(json_obj)
    else:
        raise ValidationError("Invalid json string while reading a '%s' type: %s" % (courier_type, json_str))

def serialize(courier_object):
    return json.dumps(data_value(courier_object))

def validate(courier_object):
    can_validate = hasattr(courier_object, '__class__') and \
        hasattr(courier_object.__class__, 'AVRO_SCHEMA') and \
        courier_object.AVRO_SCHEMA is not INVALID_SCHEMA
    if not can_validate:
        return
    else:
        value = data_value(courier_object)
        schema = courier_object.__class__.AVRO_SCHEMA
        if not avro.io.Validate(schema, value):
            raise ValidationError('Validity check failed for %s' % repr(courier_object))

def parse_avro_schema(schema_json):
    try:
        return avro.schema.Parse(schema_json)
    except (avro.schema.SchemaParseException, json.decoder.JSONDecodeError) as e:
        print(str(e))
        return INVALID_SCHEMA

def data_value(courier_object_or_primitive):
    if (hasattr(courier_object_or_primitive, 'data')):
        # Serialize the 'data' members of enums, records, and unions
        return getattr(courier_object_or_primitive, 'data')
    elif isinstance(courier_object_or_primitive, list):
        return [data_value(item) for item in courier_object_or_primitive]
    elif isinstance(courier_object_or_primitive, dict):
        return {k: data_value(v) for k, v in courier_object_or_primitive.items()}
    else:
        # Serialize ints and strs directly
        return courier_object_or_primitive

def construct_object(value, constructor):
    if hasattr(constructor, 'from_self_or_value'):
        return constructor.from_self_or_value(value)
    else:
        return value

def array(courier_type):
    return lambda items: Array(courier_type, items)

def map(courier_type):
    return lambda items: Map(courier_type, items)

class ValidationError(Exception):
    def __init__(self, message):
        super(ValidationError, self).__init__(message)

class Record:
    def __init__(self, data=None):
        self.data = data if data is not None else {}

    def _set_data_field(self, data_key, new_value, field_type_constructor, validate_new_value=True):
        old_data_value = UNINITIALIZED
        if data_key in self.data:
            old_data_value = self.data[data_key]

        if new_value in [None, OPTIONAL]:
            if data_key in self.data:
                del self.data[data_key]
        else:
            courier_obj = construct_object(new_value, field_type_constructor)
            self.data[data_key] = data_value(courier_obj)

        try:
            validate_new_value and validate(self)
        except ValidationError:
            if old_data_value is not UNINITIALIZED:
                self.data[data_key] = old_data_value
            raise ValidationError('%s is not a valid value for %s.%s' % (new_value, self.__class__.__name__, data_key))

    def _get_data_field(self, data_key, type_constructor):
        field_data = self.data.get(data_key)
        if field_data is not None:
            # TODO(py3) unify all of these `from_data` calls
            constructor = type_constructor.from_data if (hasattr(type_constructor, 'from_data')) else type_constructor
            courier_obj = constructor(field_data)
            if hasattr(courier_obj, 'as_value_type'):
                return courier_obj.as_value_type
            else:
                return courier_obj

class Union:
    def __init__(self, data=None):
        self.data = data if data is not None else {}

    def _set_union(self, data_key, new_value):
        old_data = self.data

    @classmethod
    def from_self_or_value(cls, self_or_value):
        return self_or_value if isinstance(self_or_value, cls) else cls(value=self_or_value)

    def _set_from_value(self, new_value):
        old_data = self.data
        new_data_value = data_value(new_value)
        new_member_key = None

        for (member_key, type_info) in self.__class__._TYPES_BY_KEY.items():
            type = type_info['type']
            if member_key == 'array' and isinstance(new_value, MutableSequence):
                new_member_key = member_key
            elif member_key == 'map' and isinstance(new_value, MutableMapping):
                new_member_key = member_key
            elif isinstance(new_value, type):
                new_member_key = member_key
        if new_member_key is None:
            # TODO(py3): better error here
            raise ValueError('Unacceptable value "%s" for union schema %s' % (repr(new_value), str(self.__class__.AVRO_SCHEMA)))

        # Edit data mutably because it may belong to a larger data tree of
        # some other object
        self.data.clear()
        self.data[new_member_key] = new_data_value

class Array(MutableSequence):
    def __init__(self, courier_index_type, data=None):
        self.data = [] if data is None else data
        self._item_constructor = courier_index_type.from_data if hasattr(courier_index_type, 'from_data') else courier_index_type

    #
    # MutableSequence abstract method implementations
    #
    def __len__(self):
        return self.data.__len__()

    def __getitem__(self, key):
        """Returns either an item or a slice of the Array. For details, see:
        https://docs.python.org/3/reference/datamodel.html#object.__getitem__
        Arguments:
        key -- either an integer (index to the array), or a slice object
        """
        item_or_slice = self.data.__getitem__(key)
        if isinstance(key, slice):
            # The key was a slice. Return a new Courier Array.
            return Array(self._item_constructor, data=item_or_slice)

        # The key was an integer. Return an item of the underlying type.
        return self._construct_item(item_or_slice)

    def __setitem__(self, key, item):
        courier_obj = construct_object(item, self._item_constructor)
        return self.data.__setitem__(key, data_value(courier_obj))

    def __delitem__(self, key):
        return self.data.__delitem__(key)

    def insert(self, idx, item):
        return self.data.insert(idx, data_value(item))

    #
    # Built-in implementations
    #
    def __repr__(self):
        return 'courier.Array(' + repr(self.data) + ')'

    def __eq__(self, other):
        return isinstance(other, MutableSequence) and data_value(self) == data_value(other)

    #
    # Private implementations
    #
    def _construct_item(self, item):
        item = self._item_constructor(item)
        return item if not hasattr(item, 'as_value_type') else item.as_value_type

class Map(MutableMapping):
    def __init__(self, courier_index_type, data=None):
        self.data = {} if data is None else data
        self._item_constructor = courier_index_type.from_data if hasattr(courier_index_type, 'from_data') else courier_index_type

    def items(self):
        for key in self.data:
            yield (key, self._construct_item(self.data[key]))

    #
    # MutableMapping abstract method implementations
    #
    def __iter__(self):
        return self.data.__iter__()

    def __len__(self):
        return self.data.__len__()

    def __getitem__(self, key):
        return self._construct_item(self.data.__getitem__(key))

    def __setitem__(self, key, item):
        courier_obj = construct_object(item, self._item_constructor)
        return self.data.__setitem__(key, data_value(courier_obj))

    def __delitem__(self, key):
        return self.data.__delitem__(key)

    #
    # Built-in implementations
    #
    def __repr__(self):
        return 'courier.Map(' + repr(self.data) + ')'

    def __eq__(self, other):
        return isinstance(other, MutableMapping) and data_value(self) == data_value(other)

    #
    # Private implementations
    #
    def _construct_item(self, item):
        item = self._item_constructor(item)
        return item if not hasattr(item, 'as_value_type') else item.as_value_type

REQUIRED = "__COURIER_REQUIRED__"
OPTIONAL = "__COURIER_OPTIONAL__"
UNINITIALIZED = "__COURIER_UNINITIALIZED__"
INVALID_SCHEMA = "__COURIER_INVALID_SCHEMA__"
