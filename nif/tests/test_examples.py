import logging
import os
from collections import Counter
from pathlib import Path

import nose
from nose.tools import assert_raises

from nif.annotation import *

from dotenv import load_dotenv
load_dotenv()

logger = logging.getLogger(__name__)


class TestMadridNif:
    def setUp(self):
        self.examples_path = Path(os.getenv('EXAMPLES_PATH'))
        self.madrid_paths = [
            self.examples_path / filename
            for filename in os.listdir(self.examples_path)
            if re.match(r'madrid.*\.nif', filename)
        ]

    def test_read(self):
        for file_path in self.madrid_paths:
            with file_path.open():
                try:
                    r = NIFDocument.parse_rdf(file_path.read_text())
                except Exception as e:
                    logger.warning(f'Problem parsing {file_path}.')
                    raise e
                g = rdflib.Graph().parse(data=file_path.read_text(), format='n3')
                assert len(g) <= len(r.rdf), (len(g), len(r.rdf))
            print(file_path)
            print(r.serialize(format='n3').decode())