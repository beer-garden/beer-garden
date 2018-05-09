#!/usr/bin/env python

"""
Run this to regenerate 'default' configuration files.

You'll need to do this if you change a spec file (after you make sure
everything upgrades cleanly).
"""

from bartender.specification import SPECIFICATION as bt_spec
from bg_utils import generate_config_file
from brew_view.specification import SPECIFICATION as bv_spec
from yapconf import YapconfSpec


generate_config_file(YapconfSpec(bt_spec), ['--config', './bartender.json'], file_type='json')
generate_config_file(YapconfSpec(bt_spec), ['--config', './bartender.yaml'], file_type='yaml')
generate_config_file(YapconfSpec(bv_spec), ['--config', './brew_view.json'], file_type='json')
generate_config_file(YapconfSpec(bv_spec), ['--config', './brew_view.yaml'], file_type='yaml')
