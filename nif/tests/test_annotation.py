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
                             uri='http://example.com')
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
                             uri='http://example.com')
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
                             uri='http://example.com')
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
            uri="http://some.doc/" + str(uuid.uuid4())
        )

    def test_context_created(self):
        text = 'some string. some other string.'
        cxt = NIFContext(
            is_string=text,
            uri="http://some.doc/" + str(uuid.uuid4())
        )
        subject_uri = cxt.value(predicate=nif_ns.isString,
                                object=rdflib.Literal(text))
        assert subject_uri, cxt.serialize(format='n3')
        assert subject_uri == cxt.uri

    def test_context_additional_attributes(self):
        text = 'some string. some other string.'
        cxt = NIFContext(
            is_string=text,
            uri="http://some.doc/" + str(uuid.uuid4())
        )
        ann = NIFString(
            begin_end_index=(0, len(text)), reference_context=cxt,
            anchor_of=text, nif__keyword='keyword')
        kw = ann.value(predicate=nif_ns.keyword, subject=ann.uri)
        assert kw, kw
        assert kw.toPython() == 'keyword', kw

    def test_wrong_anchor(self):
        text = 'this is a phrase'
        with nose.tools.assert_raises(ValueError):
            NIFString(
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
        ann_alex = NIFStructure(
            begin_end_index=(56, 60),
            reference_context=self.cxt,
            anchor_of="Alex",
            annotation_units=[au1, au2]
        )
        assert len(ann_alex.annotation_units) == 2
        assert float(ann_alex.annotation_units[0].nif__confidence) == 1.0, ann_alex.annotation_units[0].nif__confidence
        ann_alex.annotation_units = [au2]
        assert len(ann_alex.annotation_units) == 1


class TestContext:
    def setUp(self):
        pass

    def test_context_created(self):
        cxt = NIFContext(
            is_string='some larger context. this is a phrase in this context.',
            uri="http://some.doc/" + str(uuid.uuid4())
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
        a               nif:OffsetBasedString , nif:Context ;
        nif:beginIndex  "0"^^xsd:nonNegativeInteger ;
        nif:endIndex    "26"^^xsd:nonNegativeInteger ;
        nif:isString    "Welcome to Berlin in 2016." .""", format='turtle')
        na = NIFContext.from_triples(triples, context_uri=rdflib.URIRef('http://dkt.dfki.de/documents#offset_0_26'))
        assert len(na) == 5, (len(na), list(na))


class TestExtractedEntity:
    def setUp(self):
        pass

    def test_phrase_created(self):
        self.cxt = NIFContext(
            is_string='some larger context. this is a phrase in this context.',
            uri="http://some.doc/" + str(uuid.uuid4())
        )
        ex_uri = 'http://example.com/index#some'
        ee = SWCNIFMatchedResourceOccurrence(
            reference_context=self.cxt,
            begin_end_index=(0, 4),
            anchor_of='some',
            entity_uri=ex_uri
        )
        ta_ident_ref = ee.annotation_units[0].itsrdf__ta_ident_ref
        assert str(ta_ident_ref) == ex_uri, ta_ident_ref

    def test_phrase_mutations_check(self):
        self.cxt = NIFContext(
            is_string='some larger context. this is a phrase in this context.',
            uri="http://some.doc/" + str(uuid.uuid4())
        )
        ex_uri = 'http://example.com/index#some'
        ee = SWCNIFMatchedResourceOccurrence(
            reference_context=self.cxt,
            begin_end_index=(0, 4),
            anchor_of='some',
            entity_uri=ex_uri
        )
        with nose.tools.assert_raises(ValueError):
            ee.nif__begin_index = 1

    def test_annotators_ref(self):
        cxt = NIFContext(is_string='I like Madrid. Article 1. Europe is good.',
                         uri='https://lynx.poolparty.biz')
        nif_doc = NIFDocument(context=cxt)
        cpt = {'prefLabel': [], 'frequencyInDocument': 1, 'uri': 'http://vocabulary.semantic-web.at/CBeurovoc/C909', 'score': 100.0, 'transitiveBroaderConcepts': ['http://vocabulary.semantic-web.at/CBeurovoc/MT7206'], 'transitiveBroaderTopConcepts': [], 'relatedConcepts': [], 'matchings': [{'text': 'europe', 'frequency': 1, 'positions': [(26, 32)]}]}
        nif_doc.add_extracted_cpts(
            [cpt],
            confidence=1,
            annotator_uri=ns_dict['lkg']['EL'],
            rdf__type=ns_dict['lkg']['LynxAnnotation'])
        au = nif_doc.phrases[0].annotation_units[0]
        # check itsrdf:taAnnotatorsRef is present
        annotators = list(au[:ns_dict['itsrdf']['taAnnotatorsRef']:])
        print(annotators)
        assert annotators, list(au[:])
        assert len(au) >= 3


class TestDocument:
    def setUp(self):
        self.txt = 'some larger context. this is a phrase in this context.'
        self.uri_prefix = "http://some.doc/" + str(uuid.uuid4())
        self.cxt = NIFContext(
            is_string=self.txt,
            uri=self.uri_prefix)
        self.cxt2 = NIFContext(
            is_string=self.txt[:-1],
            uri="http://some.doc/" + str(uuid.uuid4()))
        ex_uri = 'http://example.com/index#some'
        self.ee = SWCNIFMatchedResourceOccurrence(
            reference_context=self.cxt,
            begin_end_index=(0, 4),
            anchor_of='some',
            entity_uri=ex_uri)
        self.ee2 = SWCNIFMatchedResourceOccurrence(
            reference_context=self.cxt2,
            begin_end_index=(0, 4),
            anchor_of='some',
            entity_uri=ex_uri)

    def test_create_doc(self):
        d = NIFDocument(context=self.cxt)
        assert d.context == self.cxt

    def test_create_from_ttl(self):
        d = NIFDocument(context=self.cxt, phrases=[self.ee])
        ttl_text = d.serialize("ttl").decode("utf-8")
        d2 = NIFDocument.parse_rdf(ttl_text)
        parsed_triples = set(d2.rdf)
        assert len(parsed_triples) >= len(d.rdf), (len(parsed_triples),
                                                   len(d.rdf))
        for s,p,o in d.rdf:
            if not isinstance(s, rdflib.BNode) and not isinstance(o, rdflib.BNode):
                assert (s,p,o) in parsed_triples, (s,p,o)
        assert d.phrases == [self.ee]

    def test_not_create_with_wrong_ref_cxt(self):
        with nose.tools.assert_raises(ValueError):
            NIFDocument(context=self.cxt, phrases=[self.ee2])

    def test_create_from_text(self):
        d = NIFDocument.from_text(self.txt, self.uri_prefix)
        assert d.context.uri.startswith(self.uri_prefix), (d.uri_prefix,
                                                           self.uri_prefix)
        assert d.context.uri.startswith(self.uri_prefix)

    def test_add_struct(self):
        d = NIFDocument(context=self.cxt)
        d.phrases += [self.ee]

    def test_add_cpt(self):
        cpt = {
            'uri': 'http://some.uri',
            'matchings': [
                {'text': 'larger', 'positions': [(5,11)]},
                {'text': 'this', 'positions': [(21, 25), (41, 45)]}
            ]
        }
        d = NIFDocument(context=self.cxt)
        d.add_extracted_cpts([cpt])

    def test_document_with_words_phrases_sents(self):
        cxt_str = "Christian mentioned tiger shark hunting"
        i = 0
        words_data = []
        for w_str in cxt_str.split(' '):
            be = (i, i+len(w_str))
            words_data.append(be)
            i += len(w_str) + 1
        sents_data = [(0, len(words_data)-1)]
        nif_doc = NIFDocument.from_data(cxt_str=cxt_str,
                                        words_data=words_data,
                                        sents_data=sents_data)
        # Named Entity
        christian = SWCNIFNamedEntityOccurrence(
            begin_end_index=(0, 9),
            anchor_of='Christian',
            reference_context=nif_doc.context,
            class_uri="http://dbpedia.org/resource/classes#Person"
        )
        nif_doc.phrases += christian
        # Noun Phrase
        np = SWCNIFChunk(
            begin_end_index=(20, 39),
            reference_context=nif_doc.context,
            chunk_type='NP',
            anchor_of='tiger shark hunting',
        )
        nif_doc.phrases += np
        assert nif_doc



class TestSuffix:
    def test_suffix(self):
        uri_str = 'http://dkt.dfki.de/documents/'
        r = do_suffix_offset(uri=uri_str,
                             begin_index=0,
                             end_index=26)
        assert str(r) == 'http://dkt.dfki.de/documents#offset_0_26', r


class TestSentenceWord:
    def setUp(self):
        self.txt = 'some larger context. this is a phrase in this context.'
        self.sents = [x+'.' for x in self.txt.split('.')]
        self.words1 = self.sents[0].split(' ')
        self.uri_prefix = "http://some.doc/" + str(uuid.uuid4())
        self.cxt = NIFContext(
            is_string=self.txt,
            uri=self.uri_prefix)

    def test_next_and_previous_sentence(self):
        sent1 = NIFSentence(begin_end_index=(0, len(self.sents[0])),
                            reference_context=self.cxt,
                            anchor_of=self.sents[0])
        sent2 = NIFSentence(begin_end_index=(len(self.sents[0]), len(self.sents[0]) + len(self.sents[1])),
                            reference_context=self.cxt,
                            anchor_of=self.sents[1],
                            previous_sentence_uri=sent1.uri)
        sent1.nif__next_sentence = sent2.uri
        assert sent1.nif__next_sentence == sent2.uri
        assert sent2.nif__previous_sentence == sent1.uri, (sent2.nif__previous_sentence, sent1.uri)

    def test_sentence_words(self):
        sent1 = NIFSentence(begin_end_index=(0, len(self.sents[0])),
                            reference_context=self.cxt,
                            anchor_of=self.sents[0])
        nif_words = []
        start = 0
        for word in self.words1:
            end = start + len(word)
            nw = NIFWord(begin_end_index=(start, end),
                         reference_context=self.cxt,
                         anchor_of=word)
            nif_words.append(nw)
            sent1.addattr('nif__word', nw.uri)
            start = end + 1
        assert len(sent1.nif__word) == len(self.words1)

    def test_sentence_words2(self):
        nif_words = []
        start = 0
        for word in self.words1:
            end = start + len(word)
            nw = NIFWord(begin_end_index=(start, end),
                         reference_context=self.cxt,
                         anchor_of=word)
            nif_words.append(nw)
            start = end + 1

        sent1 = NIFSentence(begin_end_index=(0, len(self.sents[0])),
                            reference_context=self.cxt,
                            anchor_of=self.sents[0],
                            word_uris=[w.uri for w in nif_words])
        assert len(sent1.nif__word) == len(self.words1)

    def test_next_previous_words(self):
        nif_words = []
        start = 0
        for word in self.words1:
            end = start + len(word)
            nw = NIFWord(begin_end_index=(start, end),
                         reference_context=self.cxt,
                         anchor_of=word)
            nif_words.append(nw)
            start = end + 1

        nw1 = nif_words[0]
        nw2 = nif_words[1]
        nw1.nif__next_word = nw2
        nw2.nif__previous_word = nw1
