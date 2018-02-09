from brewtils.models import Parameter


class MyModelWithDefaults(object):
    my_foo = Parameter(key="my_foo", multi=False, display_name="Foo", optional=False, type="String",
                       description="Foo With Defaults.", default="defaultFooFromModel")
    my_bar = Parameter(key="my_bar", multi=False, display_name="Bar", optional=False, type="String",
                       description="Bar With Defaults.", default="defaultBarFromModel")

    parameters = [my_foo, my_bar]


class MyListModel(object):
    my_choices_string = Parameter(key="my_choices_string", type="String", multi=False,
                                  display_name="Choices!",
                                  optional=False, description="This has some choices",
                                  choices=['a', 'b', 'c'])
    my_list_of_strings = Parameter(key="my_list_of_strings", multi=True,
                                   display_name="My List of Strings",
                                   optional=False, type="String",
                                   description="Just testing a list of Strings.")

    parameters = [my_choices_string, my_list_of_strings]


class MyNestedModel(object):
    my_nested_string = Parameter(key='my_nested_string', multi=False,
                                 display_name='My Nested String', optional=False,
                                 type='String', description='Just Testing a String')
    my_nested_int = Parameter(key="my_nested_int", multi=False, display_name="My Nested Int",
                              optional=False,
                              type="Integer", description="Just Testing an Int")

    parameters = [my_nested_string, my_nested_int]


class MyModel(object):
    my_string = Parameter(key='my_string', multi=False, display_name='My String', optional=False,
                          type='String', description='Just Testing a String')
    my_string_with_choices = Parameter(key='my_string_with_choices', multi=False, optional=False,
                                       type='String',
                                       display_name='My String With Choices',
                                       description='Just Testing a String with choices',
                                       choices=["A", "B", "C"])
    my_int = Parameter(key="my_int", multi=False, display_name="My Int", optional=False,
                       type="Integer", description="Just Testing an Int")
    my_float = Parameter(key="my_float", multi=False, display_name="My Float", optional=False,
                         type="Float", description="Just Testing a Float")
    my_bool = Parameter(key="my_bool", multi=False, display_name="My Bool", optional=False,
                        type="Boolean", description="Just Testing a Boolean")
    my_any = Parameter(key="my_any", multi=False, display_name="My Any", optional=False, type="Any",
                       description="Just Testing an Any")
    my_raw_dict = Parameter(key="my_raw_dict", multi=False, display_name="My Raw Dict",
                            optional=False,
                            type="Dictionary", description="Just Testing a Dictionary")
    my_nested_model = Parameter(key="my_nested_model", multi=False, display_name="My Nested Model",
                                optional=False, type="Dictionary",
                                description="Just Testing a Nested Model",
                                parameters=[MyNestedModel])
    my_list_of_strings = Parameter(key="my_list_of_strings", multi=True,
                                   display_name="My List of Strings",
                                   optional=False, type="String",
                                   description="Just testing a list of Strings.")
    my_optional_string = Parameter(key="my_optional_string", multi=False,
                                   display_name="My Optional",
                                   optional=True, type="String",
                                   description="Just testing an optional String.",
                                   default="test_opt")
    my_nullable_string = Parameter(key="my_nullable_string", multi=False,
                                   display_name="My Nullable String",
                                   optional=True, type="String",
                                   description="Just testing a nullable String.",
                                   nullable=True)
    my_list_of_models = Parameter(key="my_list_of_models", multi=True,
                                  display_name="My List of Models",
                                  optional=False, type="Dictionary",
                                  description="Just Testing a list of Models",
                                  parameters=[MyListModel])

    parameters = [my_string, my_string_with_choices, my_int, my_float, my_bool, my_any, my_raw_dict,
                  my_nested_model, my_list_of_strings, my_optional_string, my_nullable_string,
                  my_list_of_models]
