import os
import sys
from difflib import Differ

from bartender.specification import SPECIFICATION as bt_spec
from bg_utils import generate_config_file
from brew_view.specification import SPECIFICATION as bv_spec
import brew_view
import pytest
from yapconf import YapconfSpec
from pprint import pprint


class TestDefaultConfigs(object):

    @pytest.mark.parametrize('file_name', ['brew_view', 'bartender'])
    @pytest.mark.parametrize('file_type', ['json', 'yaml'])
    def test_default_config(self, tmpdir, file_name, file_type):
        generated_file = os.path.join(str(tmpdir), file_name+'.'+file_type)
        reference_file = os.path.join(os.path.dirname(__file__), 'source', 'defaults',
                                      file_name+'.'+file_type)

        spec = YapconfSpec(bt_spec if file_name == 'bartender' else bv_spec)
        generate_config_file(spec, ["--config", generated_file], file_type=file_type)

        with open(generated_file, 'r') as f, open(reference_file, 'r') as g:
            generated_lines = f.readlines()
            reference_lines = g.readlines()
            for x, y in zip(generated_lines, reference_lines):
                x = x.strip()
                y = y.strip()

                if (x.startswith('"config"') and y.startswith('"config"')) or \
                   (x.startswith('config') and y.startswith('config')):
                    continue

                assert x.strip() == y.strip()
