import os
import uuid
from collections import Counter

from nif.annotation import *

import pytest


class TestAnnotationUnit:
    def setUp(self):
        pass

    def test_annotation_unit(self):
        au = NIFAnnotationUnit()
        assert au, au

    def test_annotation_unit_ne(self):
        schema = calamus.fields.Namespace("http://schema.org/")
        au = NIFAnnotationUnit(confidence=1.0, class_ref=schema.Person)
        au_dump = NIFAnnotationUnitSchema().dump(au)
        assert au_dump['http://www.w3.org/2005/11/its/rdf#taClassRef']['@id'] == schema.Person
        assert au_dump['http://www.w3.org/2005/11/its/rdf#taConfidence'] == 1
        assert nif_ns.AnnotationUnit in au_dump['@type']
        assert au_dump['@id'].startswith('_')


class TestContext:
    def setUp(self):
        pass

    def test_context(self):
        cxt_uri = "http://some.doc/" + str(uuid.uuid4())
        cxt = NIFContext(is_string='some larger context. this is a phrase in this context.',
                         uri=cxt_uri)
        cxt_dump = NIFContextSchema().dump(cxt)
        assert cxt_dump[nif_ns.beginIndex] == 0, cxt_dump
        assert cxt_dump[nif_ns.endIndex] > 0
        assert cxt_dump['@id'] == cxt_uri, cxt_dump
        assert nif_ns.Context in cxt_dump['@type']

#     def test_from_triples(self):
#         triples = rdflib.Graph()
#         triples.parse(data="""
# @prefix dbo:   <http://dbpedia.org/ontology/> .
# @prefix geo:   <http://www.w3.org/2003/01/geo/wgs84_pos/> .
# @prefix dktnif: <http://dkt.dfki.de/ontologies/nif#> .
# @prefix nif-ann: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-annotation#> .
# @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
# @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
# @prefix itsrdf: <http://www.w3.org/2005/11/its/rdf#> .
# @prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
# @prefix nif:   <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#> .
#
# <http://dkt.dfki.de/documents#offset_0_26>
#         a               nif:OffsetBasedString , nif:Context ;
#         nif:beginIndex  "0"^^xsd:nonNegativeInteger ;
#         nif:endIndex    "26"^^xsd:nonNegativeInteger ;
#         nif:isString    "Welcome to Berlin in 2016." .""", format='turtle')
#         na, other = NIFContext.from_triples(triples, context_uri=rdflib.URIRef('http://dkt.dfki.de/documents#offset_0_26'))
#         assert len(na.rdf) == 4, (len(na.rdf), list(na.rdf))


class TestWord:
    def setup(self):
        cxt_uri = "http://some.doc/" + str(uuid.uuid4())
        cxt = NIFContext(is_string='some context.',
                         uri=cxt_uri)
        self.cxt = cxt

    def test_word(self):
        anchor = 'some'
        begin = 0
        end = 4
        pt = 'ADV'
        nw = NIFWord(
            reference_context_uri=self.cxt.uri,
            begin_index=begin,
            end_index=end,
            anchor_of=anchor,
            pos_tag=pt)
        nw_dump = NIFWordSchema(lazy=True).dump(nw)
        assert nw_dump[nif_ns.posTag] == pt, f'pos tag in NIFWord = {nw_dump[nif_ns.posTag]} != assined pos tag = {pt}'
        nw_uri = nw_dump['@id']
        assert 'offset' in nw_uri, f'URI = {nw_uri} is not an OffsetBasedString'
        ref_cxt = nw_dump[nif_ns.referenceContext]
        assert ref_cxt["@id"] == self.cxt.uri, ref_cxt

    def test_next_previous_words(self):
        prev_word = NIFWord(reference_context_uri=self.cxt.uri,
                            begin_index=0,
                            end_index=4,
                            anchor_of='some',)
        next_word = NIFWord(begin_index=5,
                            end_index=len(self.cxt.is_string)-1,
                            reference_context_uri=self.cxt.uri,
                            anchor_of='context',
                            previous_word_uri=prev_word.uri)
        next_word_dump = NIFWordSchema().dump(next_word)
        assert next_word_dump[nif_ns.previousWord]['@id'] == prev_word.uri, next_word_dump
        prev_word.next_word_uri = next_word.uri
        assert NIFWordSchema().dump(prev_word)[nif_ns.nextWord]['@id'] == next_word.uri

    def test_prev_word_after_this_word(self):
        prev_word = NIFWord(reference_context_uri=self.cxt.uri,
                            begin_index=0,
                            end_index=5,
                            )
        # with pytest.raises(NIFError):
        #     next_word = NIFWord(begin_index=4,
        #                         end_index=len(self.cxt.is_string)-1,
        #                         reference_context_uri=self.cxt.uri,
        #                         previous_word_uri=prev_word.uri)

    def test_incorrect_anchor_len(self):
         with pytest.raises(NIFError):
             word = NIFWord(reference_context_uri=self.cxt.uri,
                            begin_index=0,
                            end_index=5,
                            anchor_of='some')

    def test_next_word_before_this_word(self):
        next_word = NIFWord(begin_index=4,
                            end_index=len(self.cxt.is_string)-1,
                            reference_context_uri=self.cxt.uri,
                            )
        # with pytest.raises(NIFError):
        #     prev_word = NIFWord(reference_context_uri=self.cxt.uri,
        #                         begin_index=0,
        #                         end_index=5,
        #                         next_word_uri=next_word.uri)

    def test_word_outside_of_sentence(self):
        begin_end_inds = (1, 15)
        ns = NIFSentence(
            reference_context_uri=self.cxt.uri,
            begin_index=1,
            end_index=15)
        begin_end_inds = (0, 4)
        # with pytest.raises(NIFError):
        #     nw = NIFWord(
        #         reference_context_uri=self.cxt.uri,
        #         begin_index=0,
        #         end_index=4,
        #         sentence_uri=ns.uri)


class TestSentences:
    def setup(self):
        cxt_uri = "http://some.doc/" + str(uuid.uuid4())
        cxt = NIFContext(is_string='first sentence. second sentence.',
                         uri=cxt_uri)
        self.cxt = cxt

    def test_sentence(self):
        anchor = 'first sentence.'
        begin_end_inds = (0, 15)
        ns = NIFSentence(
            reference_context_uri=self.cxt.uri,
            begin_index=begin_end_inds[0],
            end_index=begin_end_inds[1],
            anchor_of=anchor)
        ns_dump = NIFSentenceSchema().dump(ns)
        assert 'offset' in ns_dump['@id'], f'URI = {ns_dump["@id"]} is not an OffsetBasedString'
        ref_cxt = ns_dump[nif_ns.referenceContext]
        assert ref_cxt is not None
        assert ns_dump[nif_ns.anchorOf] == anchor

    def test_next_previous_sents(self):
        prev_sent = NIFSentence(reference_context_uri=self.cxt.uri,
                                begin_index=0,
                                end_index=15)
        begin_end_index = (16, len(self.cxt.is_string))
        next_sent = NIFSentence(
            begin_index=begin_end_index[0],
            end_index=begin_end_index[1],
            reference_context_uri=self.cxt.uri,
            previous_sentence_uri=prev_sent.uri)
        next_sent_dump = NIFSentenceSchema().dump(next_sent)
        assert next_sent_dump[nif_ns.previousSentence]['@id'] == prev_sent.uri, next_sent_dump[nif_ns.previousSentence]
        prev_sent.next_sentence_uri = next_sent.uri
        assert NIFSentenceSchema().dump(prev_sent)[nif_ns.nextSentence]['@id'] == next_sent.uri

    def test_sent_with_words(self):
        sent = NIFSentence(reference_context_uri=self.cxt.uri,
                           begin_index=0,
                           end_index=15)
        word = NIFWord(reference_context_uri=self.cxt.uri,
                       begin_index=0,
                       end_index=5,
                       anchor_of='first',
                       sentence_uri=sent.uri)
        word_dump = NIFWordSchema().dump(word)
        assert word_dump[nif_ns.sentence]['@id'] == sent.uri, word_dump
        sent.words_uris = [word.uri]
        print(sent.words_uris)
        sent_dump = NIFSentenceSchema().dump(sent)
        print(sent_dump)
        assert sent_dump[nif_ns.word][0]['@id'] == word.uri, sent_dump

    def test_next_sent_before_this_sent(self):
        begin_end_index = (15, len(self.cxt.is_string))
        next_sent = NIFSentence(begin_index=begin_end_index[0],
                                end_index=begin_end_index[1],
                                reference_context_uri=self.cxt.uri)
        # with pytest.raises(NIFError):
        #     prev_sent = NIFSentence(reference_context_uri=self.cxt.uri,
        #                             begin_index=begin_end_index[0],
        #                             end_index=begin_end_index[1]+1,
        #                             next_sentence_uri=next_sent.uri)

    def test_prev_sent_after_this_sent(self):
        begin_end_index = (0, 16)
        prev_sent = NIFSentence(reference_context_uri=self.cxt.uri,
                                begin_index=begin_end_index[0],
                                end_index=begin_end_index[1])
        # with pytest.raises(NIFError):
        #     begin_end_index=(15, len(self.cxt.is_string))
        #     next_sent = NIFSentence(begin_index=begin_end_index[0],
        #                             end_index=begin_end_index[1],
        #                             reference_context_uri=self.cxt.uri,
        #                             previous_sentence_uri=prev_sent.uri)

    def test_words_outside_of_sentence(self):
        begin_end_index = (0, 5)
        word = NIFWord(reference_context_uri=self.cxt.uri,
                       begin_index=begin_end_index[0],
                       end_index=begin_end_index[1])
        # with pytest.raises(NIFError):
        #     begin_end_index = (1, 15)
        #     sent = NIFSentence(reference_context_uri=self.cxt.uri,
        #                        begin_index=begin_end_index[0],
        #                        end_index=begin_end_index[1],
        #                        words_uris=[word.uri])


class TestPhrase:
    def setup(self):
        cxt_uri = "http://some.doc/" + str(uuid.uuid4())
        cxt = NIFContext(is_string='phrase inside a sentence.',
                         uri=cxt_uri)
        self.cxt = cxt

    def test_ok_phrase(self):
        anchor = 'phrase'
        begin_end_inds = (0, 6)
        word = NIFWord(reference_context_uri=self.cxt.uri,
                       begin_index=begin_end_inds[0],
                       end_index=begin_end_inds[1], )
        begin_end_index = (0, 15)
        ns = NIFSentence(
            reference_context_uri=self.cxt.uri,
            begin_index=begin_end_index[0],
            end_index=begin_end_index[1])
        nw = NIFPhrase(
            reference_context_uri=self.cxt.uri,
            begin_index=begin_end_inds[0],
            end_index=begin_end_inds[1],
            anchor_of=anchor,
            words_uris=[word.uri],
            sentence_uri=ns.uri)
        nw_dump = NIFPhraseSchema().dump(nw)
        nw_uri = nw_dump['@id']
        assert 'offset' in nw_uri, f'URI = {nw_uri} is not an OffsetBasedString'
        ref_cxt = nw_dump[nif_ns.referenceContext]
        assert ref_cxt is not None

    def test_words_outside_of_phrase(self):
        begin_end_index = (0, 8)
        word = NIFWord(reference_context_uri=self.cxt.uri,
                       begin_index=begin_end_index[0],
                       end_index=begin_end_index[1])
        # with pytest.raises(NIFError):
        #     anchor = 'phrase'
        #     begin_end_index = (0, 6)
        #     nw = NIFPhrase(
        #         reference_context_uri=self.cxt.uri,
        #         begin_index=begin_end_index[0],
        #         end_index=begin_end_index[1],
        #         anchor_of=anchor,
        #         words_uris=[word.uri])

    def test_word_outside_of_sentence(self):
        begin_end_index = (1, 15)
        ns = NIFSentence(
            reference_context_uri=self.cxt.uri,
            begin_index=begin_end_index[0],
            end_index=begin_end_index[1])
        # with pytest.raises(NIFError):
        #     anchor = 'phrase'
        #     begin_end_index = (0, 6)
        #     nw = NIFPhrase(
        #         reference_context_uri=self.cxt.uri,
        #         begin_index=begin_end_index[0],
        #         end_index=begin_end_index[1],
        #         anchor_of=anchor,
        #         sentence_uri=ns.uri)


class TestChunk:
    def setup(self):
        cxt_uri = "http://some.doc/" + str(uuid.uuid4())
        cxt = NIFContext(is_string='noun phrase in sentence.',
                         uri=cxt_uri)
        self.cxt = cxt

    def test_ok_chunk(self):
        anchor = 'noun phrase'
        begin_end_index = (0, 4)
        word1 = NIFWord(reference_context_uri=self.cxt.uri,
                        begin_index=begin_end_index[0],
                        end_index=begin_end_index[1] )
        begin_end_index = (5, 11)
        word2 = NIFWord(reference_context_uri=self.cxt.uri,
                        begin_index=begin_end_index[0],
                        end_index=begin_end_index[1])
        begin_end_index = (0, 11)
        nw = SWCNIFChunk(
            reference_context_uri=self.cxt.uri,
            begin_index=begin_end_index[0],
            end_index=begin_end_index[1],
            anchor_of=anchor,
            words_uris=[word1.uri, word2.uri]
        )
        nw_dump = SWCNIFChunkSchema().dump(nw)
        nw_uri = nw_dump['@id']
        assert 'offset' in nw_uri, f'URI = {nw_uri} is not an OffsetBasedString'
        ref_cxt = nw_dump[nif_ns.referenceContext]
        assert ref_cxt is not None
        words = nw_dump[nif_ns.word]
        print(nw_dump)
        assert len(words) == 2, [str(x) for x in words]


class TestEntityOccurrence:
    def setup(self):
        cxt_uri = "http://some.doc/" + str(uuid.uuid4())
        cxt = NIFContext(is_string='Entity in the sentence.',
                         uri=cxt_uri)
        self.cxt = cxt

    def test_ok_entity(self):
        anchor = 'Entity'
        begin_end_inds = (0, 6)
        nw = SWCNIFMatchedResourceOccurrence(
            reference_context_uri=self.cxt.uri,
            begin_index=begin_end_inds[0],
            end_index=begin_end_inds[1],
            anchor_of=anchor,
            entity_uri='http://example.com/entity',
            confidence=0.2,
            annotator_uri='http://example.com/entity_linking'
        )
        nw_dump = SWCNIFMatchedResourceOccurrenceSchema().dump(nw)
        nw_uri = nw_dump['@id']
        assert 'offset' in nw_uri, f'URI = {nw_uri} is not an OffsetBasedString'
        # begin and end index
        # anchors
        ref_cxt = nw_dump[nif_ns.referenceContext]
        assert ref_cxt is not None
        assert ref_cxt == self.cxt.uri
        aus = nw_dump[nif_ns.annotationUnit]
        assert len(aus) == 1, aus
        au = aus[0]
        assert au[itsrdf_ns.taConfidence] == 0.2
        assert au[itsrdf_ns.taIdentRef]["@id"] == 'http://example.com/entity'