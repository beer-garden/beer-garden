import logging.config
from argparse import ArgumentParser

import yapconf

logger = logging.getLogger(__name__)


def parse_args(spec, item_names, cli_args):
    """Parse command-line arguments for specific item names

    Args:
        spec (yapconf.YapconfSpec): Specification for the application
        item_names(List[str]): Names to parse
        cli_args (List[str]): Command line arguments

    Returns:
        dict: Argument values
    """

    def find_item(spec, item_name):
        name_parts = item_name.split(spec._separator)
        base_name = name_parts[0]
        to_return = spec.get_item(base_name)
        for name in name_parts[1:]:
            to_return = to_return.children[name]
        return to_return

    parser = ArgumentParser()
    for item_name in item_names:
        item = find_item(spec, item_name)
        item.add_argument(parser)

    args = vars(parser.parse_args(cli_args))
    for item_name in item_names:
        name_parts = item_name.split(spec._separator)
        if len(name_parts) <= 1:
            if args[name_parts[0]] is None:
                args[name_parts[0]] = find_item(spec, item_name).default
            continue

        current_arg_value = args.get(name_parts[0], {})
        default_value = {}
        item = spec.get_item(name_parts[0])
        for name in name_parts[1:]:
            default_value[name] = {}
            item = item.children[name]
            current_arg_value = current_arg_value.get(name, {})
        default_value[name_parts[-1]] = item.default
        if not current_arg_value:
            if not args.get(name_parts[0]):
                args[name_parts[0]] = {}
            args[name_parts[0]].update(default_value)

    return args
