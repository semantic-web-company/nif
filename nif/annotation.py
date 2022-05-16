from enum import Enum
from typing import List, Tuple

import calamus.schema, calamus.fields
from marshmallow import post_dump
from pyld import jsonld


swcnif_ns = calamus.fields.Namespace('https://semantic-web.com/research/nif#')
nif_ns = calamus.fields.Namespace('http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#')
itsrdf_ns = calamus.fields.Namespace('http://www.w3.org/2005/11/its/rdf#')
rdf_ns = calamus.fields.Namespace('http://www.w3.org/1999/02/22-rdf-syntax-ns#')


class NIFError(Exception):
    pass


class URIScheme(Enum):
    nif_ns.ContextHashBasedString = nif_ns.ContextHashBasedString
    nif_ns.RFC5147String = nif_ns.RFC5147String
    nif_ns.CStringInst = nif_ns.CStringInst
    nif_ns.OffsetBasedString = nif_ns.OffsetBasedString


def do_suffix_offset(uri, begin_index, end_index):
    # TODO: add uri_scheme and add support for RFC5147String
    uri_str = uri.rstrip('/')
    chars_indicator = '#offset_'
    if chars_indicator in uri_str:
        splitted = uri_str.split(chars_indicator)
        splitted[-1] = '{}_{}'.format(begin_index, end_index)
        out = chars_indicator.join(splitted)
    else:
        out = ''.join((uri_str, chars_indicator, f'{begin_index}_{end_index}'))
    return out


def apply_uri_scheme(uri_prefix: str,
                     begin_end_index: Tuple[int, int]):
    return do_suffix_offset(uri_prefix, *begin_end_index)


################################################
class NIFBase:
    def __init__(self, uri=None, **kwargs):
        self.uri = uri
        for k, v in kwargs.items():
            setattr(self, k, v)
        self.validate()

    def validate(self):
        raise NotImplementedError


class NIFBaseSchema(calamus.schema.JsonLDSchema):
    uri = calamus.fields.Id()

    class Meta:
        rdf_type = None
        model = NIFBase

    @post_dump
    def remove_nones(self, data, **kwargs):
        return {
            key: value for key, value in data.items()
            if value is not None
        }


class NIFAnnotation(NIFBase):
    def validate(self):
        return True


class NIFAnnotationSchema(NIFBaseSchema):
    class Meta:
        rdf_type = nif_ns.Annotation
        model = NIFAnnotation


class NIFAnnotationUnit(NIFAnnotation):
    def __init__(self, uri=None, confidence: float = None, class_ref=None, ident_ref=None, annotator_ref=None, prop_ref=None):
        self.confidence = confidence
        self.class_ref = class_ref
        self.ident_ref = ident_ref
        self.annotator_ref = annotator_ref
        self.prop_ref = prop_ref
        super(NIFAnnotationUnit, self).__init__(uri=uri)


class NIFAnnotationUnitSchema(NIFAnnotationSchema):
    confidence = calamus.fields.Float(itsrdf_ns.taConfidence, required=False)
    class_ref = calamus.fields.IRI(itsrdf_ns.taClassRef, required=False)
    ident_ref = calamus.fields.IRI(itsrdf_ns.taIdentRef, required=False)
    annotator_ref = calamus.fields.IRI(itsrdf_ns.taAnnotatorRef, required=False)
    prop_ref = calamus.fields.IRI(itsrdf_ns.taPropRef, required=False)

    class Meta:
        rdf_type = [nif_ns.AnnotationUnit]
        model = NIFAnnotationUnit


class NIFContext(NIFBase):
    def __init__(self, uri: str, is_string: str):
        self.begin_index = 0
        self.end_index = len(is_string)
        self.is_string = is_string
        super(NIFContext, self).__init__(uri=uri)

    def validate(self):
        if not self.begin_index == 0 or len(self.is_string) != self.end_index:
            raise NIFError(f'Incorrect begin {self.begin_index} or end {self.end_index} indices. '
                           f'Text length = {len(self.is_string)}.')
        return True

    def __str__(self):
        s = f'nif:Context: "{self.is_string}", length {self.end_index}.'
        return s


class NIFContextSchema(NIFBaseSchema):
    begin_index = calamus.fields.Integer(nif_ns.beginIndex)
    end_index = calamus.fields.Integer(nif_ns.endIndex)
    is_string = calamus.fields.String(nif_ns.isString)

    class Meta:
        rdf_type = nif_ns.Context
        model = NIFContext


class NIFString(NIFBase):
    def __init__(self,
                 reference_context_uri: str,
                 begin_index: int,
                 end_index: int,
                 anchor_of: str = None,
                 annotation_units: List[NIFAnnotationUnit] = None):
        self.begin_index, self.end_index = begin_index, end_index
        self.reference_context_uri = reference_context_uri
        uri = apply_uri_scheme(uri_prefix=reference_context_uri,
                               begin_end_index=(begin_index, end_index))
        super(NIFString, self).__init__(uri=uri)
        self.anchor_of = anchor_of
        self.annotation_units = annotation_units

    def validate(self):
        return True


class NIFStringSchema(NIFBaseSchema):
    begin_index = calamus.fields.Integer(nif_ns.beginIndex)
    end_index = calamus.fields.Integer(nif_ns.endIndex)
    reference_context_uri = calamus.fields.IRI(nif_ns.referenceContext)
    anchor_of = calamus.fields.String(nif_ns.anchorOf, required=False)
    annotation_units = calamus.fields.Nested(nif_ns.annotationUnit, NIFAnnotationUnitSchema,
                                             required=False, many=True)

    class Meta:
        rdf_type = [nif_ns.String, nif_ns.OffsetBasedString]
        model = NIFString


class NIFStructure(NIFString):
    pass


class NIFStructureSchema(NIFStringSchema):
    class Meta:
        rdf_type = nif_ns.Structure
        model = NIFStructure


class NIFWord(NIFStructure):
    def __init__(self,
                 reference_context_uri: str,
                 begin_index: int,
                 end_index: int,
                 anchor_of: str = None,
                 pos_tag: str = None,
                 lemma: str = None,
                 next_word_uri: str = None,
                 previous_word_uri: str = None,
                 sentence_uri: str = None
                 ):
        self.pos_tag = pos_tag
        self.lemma = lemma
        super(NIFWord, self).__init__(reference_context_uri=reference_context_uri,
                                      begin_index=begin_index,
                                      end_index=end_index,
                                      anchor_of=anchor_of)
        self.next_word_uri = next_word_uri
        self.previous_word_uri = previous_word_uri
        self.sentence_uri = sentence_uri


class NIFWordSchema(NIFStructureSchema):
    pos_tag = calamus.fields.String(nif_ns.posTag, required=False)
    lemma = calamus.fields.String(nif_ns.lemma, required=False)
    next_word_uri = calamus.fields.IRI(nif_ns.nextWord, required=False, many=True)
    previous_word_uri = calamus.fields.IRI(nif_ns.previousWord, required=False)
    sentence_uri = calamus.fields.IRI(nif_ns.sentence, required=False)

    class Meta:
        rdf_type = nif_ns.Word
        model = NIFWord


class NIFSentence(NIFStructure):
    def __init__(self,
                 reference_context_uri: str,
                 begin_index: int,
                 end_index: int,
                 anchor_of: str = None,
                 next_sentence_uri: str = None,
                 previous_sentence_uri: str = None,
                 words_uris: List[str] = None
                 ):
        super(NIFSentence, self).__init__(reference_context_uri=reference_context_uri,
                                          begin_index=begin_index, end_index=end_index,
                                          anchor_of=anchor_of)
        self.next_sentence_uri = next_sentence_uri
        self.previous_sentence_uri = previous_sentence_uri
        self.words_uris = words_uris


class NIFSentenceSchema(NIFStructureSchema):
    next_sentence_uri = calamus.fields.IRI(nif_ns.nextSentence, required=False)
    previous_sentence_uri = calamus.fields.IRI(nif_ns.previousSentence, required=False)
    words_uris = calamus.fields.List(nif_ns.word, cls_or_instance=calamus.fields.IRI,
                                     required=False)

    class Meta:
        rdf_type = nif_ns.Sentence
        model = NIFSentence


class NIFPhrase(NIFStructure):
    def __init__(self,
                 reference_context_uri: str,
                 begin_index: int,
                 end_index: int,
                 anchor_of: str = None,
                 sentence_uri: str = None,
                 words_uris: List[str] = None
                 ):
        super(NIFPhrase, self).__init__(reference_context_uri=reference_context_uri,
                                        begin_index=begin_index, end_index=end_index,
                                        anchor_of=anchor_of)
        self.sentence_uri = sentence_uri
        self.words_uris = words_uris


class NIFPhraseSchema(NIFStructureSchema):
    words_uris = calamus.fields.List(nif_ns.word, cls_or_instance=calamus.fields.IRI,
                                     required=False)
    sentence_uri = calamus.fields.IRI(nif_ns.sentence, required=False)

    class Meta:
        rdf_type = nif_ns.Phrase
        model = NIFPhrase


class SWCNIFChunk(NIFPhrase):
    def __init__(self,
                 reference_context_uri: str,
                 begin_index: int,
                 end_index: int,
                 chunk_type: str = None,
                 anchor_of: str = None,
                 sentence_uri: str = None,
                 words_uris: List[str] = None):
        super(SWCNIFChunk, self).__init__(reference_context_uri=reference_context_uri,
                                          begin_index=begin_index, end_index=end_index,
                                          anchor_of=anchor_of,
                                          sentence_uri=sentence_uri,
                                          words_uris=words_uris)
        self.chunk_type = chunk_type


class SWCNIFChunkSchema(NIFPhraseSchema):
    chunk_type = calamus.fields.String(swcnif_ns.chunkType, required=False)

    class Meta:
        rdf_type = swcnif_ns.Chunk
        model = SWCNIFChunk


class SWCNIFNamedEntityOccurrence(NIFPhrase):
    rdf_classes = (swcnif_ns.NamedEntity, nif_ns.Phrase)

    def __init__(self,
                 begin_index: int,
                 end_index: int,
                 reference_context_uri: str,
                 class_uri: str,
                 confidence: float = None,
                 annotator_uri: str = None,
                 property_uri: str = None,
                 anchor_of: str = None,
                 sentence_uri: str = None,
                 words_uris: List[str] = None):
        super(SWCNIFNamedEntityOccurrence, self).__init__(reference_context_uri=reference_context_uri,
                                                          begin_index=begin_index, end_index=end_index,
                                                          anchor_of=anchor_of,
                                                          sentence_uri=sentence_uri,
                                                          words_uris=words_uris)
        au = NIFAnnotationUnit(class_ref=class_uri,
                               confidence=confidence,
                               annotator_ref=annotator_uri,
                               prop_ref=property_uri)
        self.annotation_units = [au]


class SWCNIFNamedEntityOccurrenceSchema(NIFPhraseSchema):
    class Meta:
        rdf_type = swcnif_ns.NamedEntityOccurrence
        model = SWCNIFNamedEntityOccurrence


class SWCNIFMatchedResourceOccurrence(NIFPhrase):
    def __init__(self,
                 begin_index: int,
                 end_index: int,
                 reference_context_uri: str,
                 entity_uri: str,
                 confidence: float = None,
                 annotator_uri: str = None,
                 entity_class = None,
                 anchor_of: str = None,
                 sentence_uri: str = None,
                 words_uris: List[str] = None):
        super(SWCNIFMatchedResourceOccurrence, self).__init__(reference_context_uri=reference_context_uri,
                                                              begin_index=begin_index, end_index=end_index,
                                                              anchor_of=anchor_of,
                                                              sentence_uri=sentence_uri,
                                                              words_uris=words_uris)
        au = NIFAnnotationUnit(ident_ref=entity_uri,
                               confidence=confidence,
                               annotator_ref=annotator_uri,
                               class_ref=entity_class)
        self.annotation_units = [au]


class SWCNIFMatchedResourceOccurrenceSchema(NIFPhraseSchema):
    class Meta:
        rdf_type = swcnif_ns.MatchedResourceOccurrence
        model = SWCNIFMatchedResourceOccurrence


class NIFDocument:
    def __init__(self):
        self.words = []
        self.sentences = []
        self.phrases = []

    @staticmethod
    def _parse_obj(json_obj):
        obj_types = json_obj["@type"]
        if swcnif_ns.NamedEntityOccurrence in obj_types or swcnif_ns.NamedEntity in obj_types:
            r = SWCNIFNamedEntityOccurrenceSchema().load(json_obj, unknown='INCLUDE')
        elif swcnif_ns.MatchedResourceOccurrence in obj_types or swcnif_ns.ExtractedEntity in obj_types:
            r = SWCNIFMatchedResourceOccurrenceSchema().load(json_obj, unknown='INCLUDE')
        elif swcnif_ns.Chunk in obj_types:
            r = SWCNIFChunkSchema().load(json_obj, unknown='INCLUDE')
        elif nif_ns.Sentence in obj_types:
            r = NIFSentenceSchema().load(json_obj, unknown='INCLUDE')
        elif nif_ns.Word in obj_types:
            r = NIFWordSchema().load(json_obj, unknown='INCLUDE')
        elif nif_ns.Phrase in obj_types:
            r = NIFPhraseSchema().load(json_obj, unknown='INCLUDE')
        elif nif_ns.Context in obj_types:
            r = NIFContextSchema().load(json_obj, unknown='INCLUDE')
        elif nif_ns.AnnotationUnit in obj_types:
            r = NIFAnnotationUnitSchema().load(json_obj, unknown='INCLUDE')
        elif nif_ns.Annotation in obj_types:
            r = NIFAnnotationSchema().load(json_obj, unknown='INCLUDE')
        else:
            r = None
        return r

    @classmethod
    def from_json(cls, json_data):
        objs = dict()
        if "@context" in json_data:
            json_data = jsonld.expand(json_data)
        for obj in json_data:
            nif_obj = cls._parse_obj(obj)
            if nif_obj is not None:
                objs[nif_obj.uri] = nif_obj
        return objs


if __name__ == '__main__':
    pass