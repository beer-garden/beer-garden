import inspect

from brewtils.models import Parameter


class AutoBrewerObject:
    def updateClientClass(self, client, name=None, version=None):
        if name:
            client._bg_name = name
        else:
            client._bg_name = getattr(client, "__name__", client.__class__.__name__)

        if version:
            client._bg_version = version
        else:
            client._bg_version = getattr(client, "__version__", "0.0.0")
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

                        if str(func_parameter_value.annotation) in [
                            "<class 'inspect._empty'>",
                            "<class 'str'>",
                        ]:
                            pass
                        elif str(func_parameter_value.annotation) in ["<class 'int'>"]:
                            typeValue = "Integer"
                        elif str(func_parameter_value.annotation) in [
                            "<class 'float'>"
                        ]:
                            typeValue = "Float"
                        elif str(func_parameter_value.annotation) in ["<class 'bool'>"]:
                            typeValue = "Boolean"
                        elif str(func_parameter_value.annotation) in [
                            "<class 'object'>",
                            "<class 'dict'>",
                        ]:
                            typeValue = "Dictionary"

                        if (
                            str(func_parameter_value.default)
                            != "<class 'inspect._empty'>"
                        ):
                            default = func_parameter_value.default

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
