import json
import os
import sys
from ruamel.yaml import YAML
from shutil import copyfile

from bartender.specification import SPECIFICATION as bt_spec
from bg_utils import generate_config_file, update_config_file
from brew_view.specification import SPECIFICATION as bv_spec
import brew_view
import pytest
from yapconf import YapconfSpec
from pprint import pprint


@pytest.mark.parametrize('file_name', ['brew-view', 'bartender'])
@pytest.mark.parametrize('file_type', ['json', 'yaml'])
def test_generate(tmpdir, file_name, file_type):
    generated_file = os.path.join(str(tmpdir), file_name+'.'+file_type)
    reference_file = os.path.join(os.path.dirname(__file__), 'defaults',
                                  file_name+'.'+file_type)

    spec = YapconfSpec(bt_spec if file_name == 'bartender' else bv_spec)
    generate_config_file(spec, ["-c", generated_file, "-t", file_type])

    with open(generated_file, 'r') as f, open(reference_file, 'r') as g:
        if file_type == 'json':
            generated_config = json.load(f)
            reference_config = json.load(g)
        elif file_type == 'yaml':
            yaml = YAML()
            generated_config = yaml.load(f)
            reference_config = yaml.load(g)

    # These are always going to be different
    del generated_config['configuration']['file']
    del reference_config['configuration']['file']

    assert generated_config == reference_config


@pytest.mark.parametrize('start_version', ['2.3.5'])
@pytest.mark.parametrize('file_name', ['brew-view', 'bartender'])
@pytest.mark.parametrize('file_type', ['json', 'yaml'])
def test_update(tmpdir, start_version, file_name, file_type):
    """Ensure that configuration files update correctly

    This method can't be used to switch files between formats.
    """
    spec = YapconfSpec(bt_spec if file_name == 'bartender' else bv_spec)

    # Yaml support was added after 2.3.5, so there won't been a source there
    if start_version == '2.3.5' and file_type == 'yaml':
        return

    # This is the file that we expect to generate
    expected_file = os.path.join(os.path.dirname(__file__), 'expected',
                                 start_version+'-'+file_name+'.'+file_type)

    # This is the starting file. First copy to tmpdir since update modifies
    source_file = os.path.join(os.path.dirname(__file__), start_version,
                               file_name+'.'+file_type)
    test_file = os.path.join(tmpdir, file_name+'.'+file_type)
    copyfile(source_file, test_file)

    update_config_file(spec, ['-c', test_file])

    with open(test_file, 'r') as f, open(expected_file, 'r') as g:
        if file_type == 'json':
            test_config = json.load(f)
            expected_config = json.load(g)
        elif file_type == 'yaml':
            yaml = YAML()
            test_config = yaml.load(f)
            expected_config = yaml.load(g)

    assert test_config == expected_config

