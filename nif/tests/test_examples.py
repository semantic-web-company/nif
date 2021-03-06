import logging
import os
from collections import Counter
from pathlib import Path

import nose
from nose.tools import assert_raises

from nif.annotation import *

# from dotenv import load_dotenv
# load_dotenv()

logger = logging.getLogger(__name__)


class TestMadridNif:
    def setUp(self):
        self.examples_path = Path(os.getenv('EXAMPLES_PATH', default='../examples'))
        self.madrid_paths = [
            self.examples_path / filename
            for filename in os.listdir(self.examples_path)
            if re.match(r'madrid.*\.nif', filename)
        ]
        self.aardwamte_path = self.examples_path / 'aardwamte.nif'

    def test_read_madrid(self):
        for file_path in self.madrid_paths:
            with file_path.open():
                try:
                    r = NIFDocument.parse_rdf(file_path.read_text())
                except Exception as e:
                    logger.warning(f'Problem parsing {file_path}.')
                    raise e
                g = rdflib.Graph().parse(data=file_path.read_text(), format='n3')
            assert len(g) <= len(r.rdf), (len(g), len(r.rdf))
            # print(file_path)
            # print(r.serialize(format='n3').decode())

    def test_read_aardwamte(self):
        with self.aardwamte_path.open():
            try:
                r = NIFDocument.parse_rdf(self.aardwamte_path.read_text(),
                                          context_class=rdflib.URIRef('http://lkg.lynx-project.eu/def/LynxDocument'))
            except Exception as e:
                logger.warning(f'Problem parsing {self.aardwamte_path}.')
                raise e
            g = rdflib.Graph().parse(data=self.aardwamte_path.read_text(),
                                     format='n3')
        print(r.serialize(format='turtle').decode())
        assert len(g) <= len(r.rdf), (len(g), len(r.rdf))
        lynx_doc_parts = r.rdf[:rdflib.RDF.type:rdflib.URIRef("http://lkg.lynx-project.eu/def/LynxDocumentPart")]
        for doc_part in lynx_doc_parts:
            assert (doc_part, rdflib.RDF.type, nif_ns.Annotation) not in g, (doc_part, rdflib.RDF.type, nif_ns.Annotation)
            assert (doc_part, rdflib.RDF.type, nif_ns.Annotation) not in r.rdf, (doc_part, rdflib.RDF.type, nif_ns.Annotation)
        # print(self.aardwamte_path)
        # print(r.serialize(format='n3').decode())