import os

import nose

from nif.annotation import *


class TestAnnotation:
    def setUp(self):
        self.cxt = NIFContext(
            is_string='some larger context. this is a phrase in this context.',
            uri_prefix="http://some.doc/"+str(uuid.uuid4())
        )

    def test_context_created(self):
        text = 'some string. some other string.'
        ann = NIFAnnotation(
            begin_end_index=None, is_string=text,
            ta_ident_ref=None, reference_context=None,
            uri_prefix="http://example.doc/"+str(uuid.uuid4()),
            anchor_of=None)
        assert len(ann) > 0
        subject_uri = ann.value(predicate=nif_ns.isString,
                                object=rdflib.Literal(text))
        assert subject_uri, ann.serialize(format='n3')
        assert subject_uri == ann.uri

    def test_context_no_anchor(self):
        text = 'some string. some other string.'
        with nose.tools.assert_raises(ValueError):
            NIFAnnotation(
                begin_end_index=None, is_string=text,
                ta_ident_ref=None, reference_context=None,
                uri_prefix="http://example.doc/" + str(uuid.uuid4()),
                anchor_of=text
            )

    def test_context_additional_attributes(self):
        text = 'some string. some other string.'
        ann = NIFAnnotation(
            begin_end_index=None, is_string=text,
            ta_ident_ref=None, reference_context=None,
            uri_prefix="http://example.doc/" + str(uuid.uuid4()),
            anchor_of=None, nif__keyword='keyword')
        kw = ann.value(predicate=nif_ns.keyword, subject=ann.uri)
        assert kw, kw
        assert kw.toPython() == 'keyword', kw

    def test_phrase(self):
        text = 'this is a phrase'
        ann = NIFAnnotation(
            begin_end_index=(21, 37), is_string=None,
            ta_ident_ref=None, reference_context=self.cxt,
            uri_prefix=None, anchor_of=text)
        assert len(ann) > 0
        assert ann.uri.startswith(self.cxt.uri.toPython()[:10])


class TestContext:
    def setUp(self):
        pass

    def test_context_created(self):
        cxt = NIFContext(
            is_string='some larger context. this is a phrase in this context.',
            uri_prefix="http://some.doc/"+str(uuid.uuid4())
        )


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
        ta_ident_ref = ee.itsrdf__ta_ident_ref[0].toPython()
        assert ta_ident_ref == ex_uri, ta_ident_ref


class TestDocument:
    def setUp(self):
        pass