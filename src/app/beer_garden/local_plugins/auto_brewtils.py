from brewtils.models import Parameter
from brewtils import Plugin

import inspect

class AutoBrewObject:

    def updateClientClass(self, client, name = None, version = None):
        if name:
            client._bg_name = name
        else:
            client._bg_name = client.__class__.__name__

        if version:
            client._bg_version = version
        else:
            client._bg_version = getattr(client, "__version__", None)
        client._bg_commands = []
        client._current_request = None

        self.addFunctions(client)

        return client

    def addFunctions(self, client):

        for func in dir(client):
            if callable(getattr(client, func)):
                if not func.startswith("_"):

                    # https://docs.python.org/3/library/inspect.html#inspect.signature
                    _wrapped = getattr(client, func)
                    signature = inspect.signature(_wrapped)

                    for func_parameter in signature.parameters:

                        func_parameter_value = signature.parameters[func_parameter]

                        key = func_parameter_value.name
                        if key == "self":
                            continue

                        func_parameter_value.default
                        typeValue = "String"
                        default = None
                        optional = False
                        is_kwarg = False

                        if str(func_parameter_value.annotation) in ["<class 'inspect._empty'>", "<class 'str'>"]:
                            pass
                        elif str(func_parameter_value.annotation) in ["<class 'int'>", "<class 'float'>"]:
                            typeValue = "Integer"
                        elif str(func_parameter_value.annotation) in ["<class 'object'>", "<class 'dict'>"]:
                            typeValue = "Dictionary"

                        if str(func_parameter_value.default) != "<class 'inspect._empty'>":
                            default = func_parameter_value.default

                        #   TODO: Support kwargs
                        # if "kwargs" == key:
                        #     is_kwarg = True
                        #     optional = True

                        new_parameter = Parameter(
                                key=key,
                                type=typeValue,
                                multi=False,
                                display_name=key,
                                optional=optional,
                                default=default,
                                description=None,
                                choices=None,
                                parameters=None,
                                nullable=None,
                                maximum=None,
                                minimum=None,
                                regex=None,
                                form_input_type=None,
                                type_info=None,
                                is_kwarg=is_kwarg,
                                model=None,
                            )

                        _wrapped.parameters = getattr(_wrapped, "parameters", [])
                        _wrapped.parameters.append(new_parameter)

                        # TODO: Add description wrapper from Doc String

        return client