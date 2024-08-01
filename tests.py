import unittest
from textwrap import dedent
from unittest import TestCase
from typing import Callable, Any
from dataclasses import dataclass


@dataclass
class Field:
    """
    Defines a field with a label and preconditions
    """
    label: str
    precondition: Callable[[Any], bool] = None

    def __init__(self, label, precondition=None):
        self.label = label
        self.precondition = precondition


# Record and supporting classes here
class RecordMeta(type):
    def __new__(cls, name, bases, attrs, **kwargs):
        # Implement the class creation by manipulating the attr dictionary
        new_attrs = {}
        for att_name, attr_value in attrs.items():
            if not att_name.startswith('__'):  # Ignore built-in attributes
                new_attrs[att_name] = attrs[att_name]

        new_annotations = {}
        for base_class in bases:
            for parent_class in base_class.__mro__:
                if '__annotations__' in parent_class.__dict__ is not None:
                    new_annotations.update(parent_class.__annotations__)

        attrs.update(new_attrs)
        attrs.get('__annotations__', {}).update(new_annotations)

        return super(RecordMeta, cls).__new__(cls, name, bases, attrs)


class Record(metaclass=RecordMeta):
    fields = {}

    def __setattr__(self, attr, value):
        """
        Overrides attribute's field object assignment with actual field value.
        e.g., name = Field(label=...) becomes name = 'James'
        """
        if hasattr(self, attr) and not isinstance(getattr(self, attr), Field):
            raise AttributeError("Cannot modify attribute after initialization")
        else:
            new_value = value
            self.fields[attr] = getattr(self, attr) # Save for later
            super().__setattr__(attr, new_value)

    def __init__(self, **kwargs):
        params = list(self.__annotations__.keys())
        for parameter in kwargs:
            # Check if parameter is class attribute
            if parameter in params:
                # verify correct type
                if self.__annotations__.get(parameter) is type(kwargs.get(parameter)):
                    # Evaluate precondition
                    precon = getattr(self, parameter).precondition
                    if precon is not None and not precon(kwargs.get(parameter)):
                        raise TypeError(f"Parameter {parameter} = {kwargs.get(parameter)} failed precondition")
                    # Save field value
                    setattr(self, parameter, kwargs.get(parameter))
                    params.remove(parameter)
                else:
                    raise TypeError(f"Invalid param type, expected {self.__annotations__.get(parameter)}, got "
                                    f"{type(kwargs.get(parameter))}")
            else:
                raise TypeError("Unknown parameter '%s'" % parameter)

        if len(params) > 0:
            raise TypeError("Missing params %s" % params)

    def __str__(self):
        formatted_string = f"{self.__class__.__name__}("
        for attr in self.__annotations__.keys():
            formatted_string += f"\n  # {self.fields.get(attr).label}\n  {attr}={attr_friendly_display(getattr(self, attr))}\n"
        formatted_string += ")"
        return formatted_string


def attr_friendly_display(attribute_value):
    if isinstance(attribute_value, str):
        return f"'{attribute_value}'"
    else:
        return str(attribute_value)



# Usage of Record
class Person(Record):
    """
    A simple person record
    """
    name: str = Field(label="The name")
    age: int = Field(label="The person's age", precondition=lambda x: 0 <= x <= 150)
    income: float = Field(label="The person's income", precondition=lambda x: 0 <= x)


class Named(Record):
    """
    A base class for things with names
    """
    name: str = Field(label="The name")


class Animal(Named):
    """
    An animal
    """
    habitat: str = Field(label="The habitat", precondition=lambda x: x in ["air", "land", "water"])
    weight: float = Field(label="The animals weight (kg)", precondition=lambda x: 0 <= x)


class Dog(Animal):
    """
    A type of animal
    """
    bark: str = Field(label="Sound of bark")


# Tests
class RecordTests(TestCase):
    def test_creation(self):
        Person(name="JAMES", age=110, income=24000.0)
        with self.assertRaises(TypeError):
            Person(name="JAMES", age=160, income=24000.0)
        with self.assertRaises(TypeError):
            Person(name="JAMES")
        with self.assertRaises(TypeError):
            Person(name="JAMES", age=-1, income=24000.0)
        with self.assertRaises(TypeError):
            Person(name="JAMES", age="150", income=24000.0)
        with self.assertRaises(TypeError):
            Person(name="JAMES", age="150", wealth=24000.0)

    def test_properties(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        self.assertEqual(james.age, 34)
        with self.assertRaises(AttributeError):
            james.age = 32

    def test_str(self):
        james = Person(name="JAMES", age=34, income=24000.0)
        correct = dedent("""
        Person(
          # The name
          name='JAMES'

          # The person's age
          age=34

          # The person's income
          income=24000.0
        )
        """).strip()
        self.assertEqual(str(james), correct)

    def test_dog(self):
        mike = Dog(name="mike", habitat="land", weight=50., bark="ARF")
        self.assertEqual(mike.weight, 50)


if __name__ == '__main__':
    unittest.main()
