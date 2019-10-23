import os
from collections import Counter

import nose
from nose.tools import assert_raises

from nif.annotation import *


class TestNIFString:
    def setUp(self):
        self.text = 'some larger context. this is a phrase in this context.'

    def test_setattr(self):
        nif_str = NIFContext(is_string=self.text,
                             uri_prefix='http://example.com')
        end_index = len(self.text)
        assert str(nif_str.uri) == f'http://example.com#offset_0_{end_index}', \
            nif_str.uri
        title_str = 'prefLabel'
        nif_str.rdfs__label = title_str
        rdf_title = nif_str.value(predicate=rdflib.RDFS.label,
                                  subject=nif_str.uri)
        assert str(rdf_title) == title_str
        nif_str.rdfs__label = [title_str, title_str+'a']
        with assert_raises(rdflib.exceptions.UniquenessError):
            rs = nif_str.value(predicate=rdflib.RDFS.label,
                               subject=nif_str.uri,
                               any=False)
        objs = nif_str.objects(predicate=rdflib.RDFS.label,
                               subject=nif_str.uri)
        assert len(list(objs)) == 2
        nif_str.rdfs__label = []
        rdf_title = nif_str.value(predicate=rdflib.RDFS.label,
                                  subject=nif_str.uri)
        assert rdf_title is None

    def test_addattr(self):
        nif_str = NIFContext(is_string=self.text,
                             uri_prefix='http://example.com')
        end_index = len(self.text)
        assert str(nif_str.uri) == f'http://example.com#offset_0_{end_index}', \
            nif_str.uri
        title_str = 'prefLabel'
        nif_str.addattr('rdfs__label', title_str)
        rdf_title = nif_str.value(predicate=rdflib.RDFS.label,
                                  subject=nif_str.uri)
        assert str(rdf_title) == title_str
        nif_str.addattr('rdfs__label', title_str+'a')
        with assert_raises(rdflib.exceptions.UniquenessError):
            rs = nif_str.value(predicate=rdflib.RDFS.label,
                               subject=nif_str.uri,
                               any=False)
        objs = nif_str.objects(predicate=rdflib.RDFS.label,
                               subject=nif_str.uri)
        assert len(list(objs)) == 2
        nif_str.addattr('rdfs__label', [title_str + 'b', title_str + 'c'])
        objs = nif_str.objects(predicate=rdflib.RDFS.label,
                               subject=nif_str.uri)
        assert len(list(objs)) == 4
        nif_str.addattr('rdfs__label', [])
        rdf_title = nif_str.value(predicate=rdflib.RDFS.label,
                                  subject=nif_str.uri)
        assert rdf_title is not None, rdf_title

    def test_delattr(self):
        nif_str = NIFContext(is_string=self.text,
                             uri_prefix='http://example.com')
        end_index = len(self.text)
        assert str(nif_str.uri) == f'http://example.com#offset_0_{end_index}', \
            nif_str.uri
        title_str = 'prefLabel'
        nif_str.addattr('rdfs__label', title_str)
        nif_str.delattr('rdfs__label', title_str)
        assert nif_str.rdfs__label is None

        nif_str.addattr('rdfs__label',
                        [title_str+'a', title_str + 'b', title_str + 'c'])
        nif_str.delattr('rdfs__label', [title_str + 'a', title_str + 'b'])
        assert str(nif_str.rdfs__label) == title_str+'c', nif_str.rdfs__label


class TestAnnotation:
    def setUp(self):
        self.text = 'Vodka and a Martini go to a bar and this is English and Alex is a name and sepsis is a disease.'
        self.cxt = NIFContext(
            is_string=self.text,
            uri_prefix="http://some.doc/"+str(uuid.uuid4())
        )

    def test_context_created(self):
        text = 'some string. some other string.'
        cxt = NIFContext(
            is_string=text,
            uri_prefix="http://some.doc/" + str(uuid.uuid4())
        )
        subject_uri = cxt.value(predicate=nif_ns.isString,
                                object=rdflib.Literal(text))
        assert subject_uri, cxt.serialize(format='n3')
        assert subject_uri == cxt.uri

    def test_context_additional_attributes(self):
        text = 'some string. some other string.'
        cxt = NIFContext(
            is_string=text,
            uri_prefix="http://some.doc/" + str(uuid.uuid4())
        )
        ann = NIFAnnotation(
            begin_end_index=(0, len(text)), is_string=text,
            ta_ident_ref=None, reference_context=cxt,
            anchor_of=text, nif__keyword='keyword')
        kw = ann.value(predicate=nif_ns.keyword, subject=ann.uri)
        assert kw, kw
        assert kw.toPython() == 'keyword', kw

    def test_wrong_anchor(self):
        text = 'this is a phrase'
        with nose.tools.assert_raises(ValueError):
            NIFAnnotation(
                begin_end_index=(0, 4),
                reference_context=self.cxt,
                anchor_of=text)

    def test_annotation_unit(self):
        au1_dict = {
            "nif__confidence": 1.0,
            "itsrdf__ta_class_ref": "schema:Person",
            "rdf__type": "nif:EntityOccurrence"
        }
        au1 = NIFAnnotationUnit()
        for p, o in au1_dict.items():
            au1.__setattr__(p, o)
        au2_dict = {
            "nif__confidence": 0.2,
            "rdf__type": "nif:TermOccurrence"
        }
        au2 = NIFAnnotationUnit()
        for p, o in au2_dict.items():
            au2.__setattr__(p, o)
        ann_alex = NIFAnnotation(
            begin_end_index=(56, 60),
            reference_context=self.cxt,
            anchor_of="Alex",
            annotation_units=[au1, au2]
        )
        assert len(ann_alex.annotation_units) == 2
        assert float(ann_alex.annotation_units[au1.uri].nif__confidence) == 1.0, ann_alex.annotation_units[au1.uri].nif__confidence
        ann_alex.remove_annotation_unit(au1.uri)
        assert len(ann_alex.annotation_units) == 1


class TestContext:
    def setUp(self):
        pass

    def test_context_created(self):
        cxt = NIFContext(
            is_string='some larger context. this is a phrase in this context.',
            uri_prefix="http://some.doc/"+str(uuid.uuid4())
        )

    def test_from_triples(self):
        triples = rdflib.Graph()
        triples.parse(data="""
@prefix dbo:   <http://dbpedia.org/ontology/> .
@prefix geo:   <http://www.w3.org/2003/01/geo/wgs84_pos/> .
@prefix dktnif: <http://dkt.dfki.de/ontologies/nif#> .
@prefix nif-ann: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-annotation#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix itsrdf: <http://www.w3.org/2005/11/its/rdf#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix nif:   <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> .

<http://dkt.dfki.de/documents#offset_0_26>
        a               nif:RFC5147String , nif:String , nif:Context ;
        nif:beginIndex  "0"^^xsd:nonNegativeInteger ;
        nif:endIndex    "26"^^xsd:nonNegativeInteger ;
        nif:isString    "Welcome to Berlin in 2016." .""", format='turtle')
        na = NIFContext.from_triples(triples)
        assert len(na) == 7, (len(na), list(na))


class TestExtractedEntity:
    def setUp(self):
        self.cxt = NIFContext(
            is_string='some larger context. this is a phrase in this context.',
            uri_prefix="http://some.doc/"+str(uuid.uuid4())
        )

    def test_phrase_created(self):
        ex_uri = 'http://example.com/index#some'
        ee = NIFExtractedEntity(
            reference_context=self.cxt,
            begin_end_index=(0, 4),
            anchor_of='some',
            entity_uri=ex_uri
        )
        ta_ident_ref = next(iter(ee.annotation_units.values())).itsrdf__ta_ident_ref
        assert str(ta_ident_ref) == ex_uri, ta_ident_ref

    def test_phrase_mutations_check(self):
        ex_uri = 'http://example.com/index#some'
        ee = NIFExtractedEntity(
            reference_context=self.cxt,
            begin_end_index=(0, 4),
            anchor_of='some',
            entity_uri=ex_uri
        )
        with nose.tools.assert_raises(ValueError):
            ee.nif__begin_index = 1


class TestDocument:
    def setUp(self):
        self.txt = 'some larger context. this is a phrase in this context.'
        self.uri_prefix = "http://some.doc/" + str(uuid.uuid4())
        self.cxt = NIFContext(
            is_string=self.txt,
            uri_prefix=self.uri_prefix)
        self.cxt2 = NIFContext(
            is_string=self.txt[:-1],
            uri_prefix="http://some.doc/" + str(uuid.uuid4()))
        ex_uri = 'http://example.com/index#some'
        self.ee = NIFExtractedEntity(
            reference_context=self.cxt,
            begin_end_index=(0, 4),
            anchor_of='some',
            entity_uri=ex_uri)
        self.ee2 = NIFExtractedEntity(
            reference_context=self.cxt2,
            begin_end_index=(0, 4),
            anchor_of='some',
            entity_uri=ex_uri)

    def test_create_doc(self):
        d = NIFDocument(context=self.cxt, annotations=[])
        assert d.context == self.cxt

    def test_create_with_struct(self):
        d = NIFDocument(context=self.cxt, annotations=[self.ee])
        assert d.annotations == [self.ee]

    def test_create_from_ttl(self):
        d = NIFDocument(context=self.cxt, annotations=[self.ee])
        ttl_text = d.serialize("ttl").decode("utf-8")
        d2 = NIFDocument.parse_rdf(ttl_text)
        parsed_triples = set(d2.rdf)
        assert len(parsed_triples) >= len(d.rdf), (len(parsed_triples),
                                                   len(d.rdf))
        for s,p,o in d.rdf:
            if not isinstance(s, rdflib.BNode) and not isinstance(o, rdflib.BNode):
                assert (s,p,o) in parsed_triples, (s,p,o)
        assert d.annotations == [self.ee]

    def test_not_create_with_wrong_ref_cxt(self):
        with nose.tools.assert_raises(ValueError):
            NIFDocument(context=self.cxt, annotations=[self.ee2])

    def test_create_from_text(self):
        d = NIFDocument.from_text(self.txt, self.uri_prefix)
        assert d.context.uri.startswith(self.uri_prefix), (d.uri_prefix,
                                                           self.uri_prefix)
        assert d.uri_prefix == self.uri_prefix
        assert d.context.uri.startswith(self.uri_prefix)

    def test_add_struct(self):
        d = NIFDocument(context=self.cxt, annotations=[])
        d.add_extracted_entity(self.ee)

    def test_not_add_invalid_struct(self):
        d = NIFDocument(context=self.cxt, annotations=[])
        with nose.tools.assert_raises(ValueError):
            d.add_extracted_entity(self.ee2)

    def test_add_cpt(self):
        cpt = {
            'uri': 'http://some.uri',
            'matchings': [
                {'text': 'larger', 'positions': [(5,11)]},
                {'text': 'this', 'positions': [(21, 25), (41, 45)]}
            ]
        }
        d = NIFDocument(context=self.cxt, annotations=[])
        d.add_extracted_cpt(cpt)

    def test_copy(self):
        cpt = {
            'uri': 'http://some.uri',
            'matchings': [
                {'text': 'larger', 'positions': [(5, 11)]},
                {'text': 'this', 'positions': [(21, 25), (41, 45)]}
            ]
        }
        d = NIFDocument(context=self.cxt, annotations=[])
        d.add_extracted_cpt(cpt)
        assert d == d.__copy__()


class TestSuffix:
    def test_suffix(self):
        uri_str = 'http://dkt.dfki.de/documents/'
        r = do_suffix_offset(uri=uri_str,
                             begin_index=0,
                             end_index=26)
        assert str(r) == 'http://dkt.dfki.de/documents#offset_0_26', r


class TestParsing:
    def setUp(self):
        self.rdf_to_parse = '''
@prefix dbo:   <http://dbpedia.org/ontology/> .
@prefix geo:   <http://www.w3.org/2003/01/geo/wgs84_pos/> .
@prefix dktnif: <http://dkt.dfki.de/ontologies/nif#> .
@prefix nif-ann: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-annotation#> .
@prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
@prefix itsrdf: <http://www.w3.org/2005/11/its/rdf#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix nif:   <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> .

<http://dkt.dfki.de/documents#offset_11_17>
        a                     nif:RFC5147String , nif:String , nif:Structure ;
        nif:anchorOf          "Berlin" ;
        nif:beginIndex        "11"^^xsd:nonNegativeInteger ;
        nif:endIndex          "17"^^xsd:nonNegativeInteger ;
        nif:referenceContext  <http://dkt.dfki.de/documents#offset_0_26> ;
        itsrdf:taClassRef     dbo:Location ;
        itsrdf:taIdentRef     <http://www.wikidata.org/entity/Q64> ;
        itsrdf:taIdentRef     []  .

<http://dkt.dfki.de/documents#offset_0_26>
        a               nif:RFC5147String , nif:String , nif:Context ;
        nif:beginIndex  "0"^^xsd:nonNegativeInteger ;
        nif:endIndex    "26"^^xsd:nonNegativeInteger ;
        nif:isString    "Welcome to Berlin in 2016." .
'''

    def test_parse_correct(self):
        parsed = NIFDocument.parse_rdf(self.rdf_to_parse, format='turtle')
        serialized = parsed.serialize(format='turtle')
        g_original = rdflib.Graph()
        g_original.parse(data=self.rdf_to_parse, format='turtle')
        g_processed = rdflib.Graph()
        g_processed.parse(data=serialized, format='turtle')

        sp_pairs_original = [(s, p) for s, p, o in g_original]
        sp_orig_counter = Counter(sp_pairs_original)
        sp_pairs_processed = [(s, p) for s, p, o in g_processed]
        sp_processed_counter = Counter(sp_pairs_processed)
        for k, v in (sp_orig_counter - sp_processed_counter).items():
            assert v <= 0, (k,v)
