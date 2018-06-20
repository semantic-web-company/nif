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
            begin_end_index=(0, len(text)), is_string=text,
            ta_ident_ref=None, reference_context=None,
            uri_prefix="http://example.doc/"+str(uuid.uuid4()),
            anchor_of=None)
        assert len(ann) > 0
        subject_uri = ann.value(predicate=nif_ns.isString,
                                object=rdflib.Literal(text))
        assert subject_uri, ann.serialize(format='n3')
        assert subject_uri == ann.uri

    def test_context_additional_attributes(self):
        text = 'some string. some other string.'
        ann = NIFAnnotation(
            begin_end_index=(0, len(text)), is_string=text,
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
        ta_ident_ref = ee.itsrdf__ta_ident_ref
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
        d = NIFDocument(context=self.cxt, structures=[])
        assert d.context == self.cxt

    def test_create_with_struct(self):
        d = NIFDocument(context=self.cxt, structures=[self.ee])
        assert d.structures == [self.ee]

    def test_not_create_with_wrong_ref_cxt(self):
        with nose.tools.assert_raises(ValueError):
            NIFDocument(context=self.cxt, structures=[self.ee2])

    def test_create_from_text(self):
        d = NIFDocument.from_text(self.txt, self.uri_prefix)
        assert d.context.uri.startswith(self.uri_prefix), (d.uri_prefix,
                                                           self.uri_prefix)
        assert d.uri_prefix == self.uri_prefix
        assert d.context.uri.startswith(self.uri_prefix)

    def test_add_struct(self):
        d = NIFDocument(context=self.cxt, structures=[])
        d.add_extracted_entity(self.ee)

    def test_not_add_invalid_struct(self):
        d = NIFDocument(context=self.cxt, structures=[])
        with nose.tools.assert_raises(ValueError):
            d.add_extracted_entity(self.ee2)

