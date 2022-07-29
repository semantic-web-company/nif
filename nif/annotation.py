import warnings
from collections import defaultdict
from enum import Enum
from typing import List, Tuple

import calamus.fields
import calamus.schema
from marshmallow import post_dump, INCLUDE
from pyld import jsonld

from nif import utils

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
        unknown = INCLUDE
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
        unknown = INCLUDE
        rdf_type = nif_ns.Annotation
        model = NIFAnnotation


class NIFAnnotationUnit(NIFAnnotation):
    def __init__(self, uri=None, confidence: float = None, class_ref=None, ident_ref=None, annotator_ref=None,
                 prop_ref=None):
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
        unknown = INCLUDE
        rdf_type = [nif_ns.AnnotationUnit]
        model = NIFAnnotationUnit
        inherit_parent_types = False


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
        unknown = INCLUDE
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
        self.anchor_of = anchor_of
        if anchor_of and len(anchor_of) != end_index-begin_index:
            raise NIFError(f"Annotation indices ({begin_index}, {end_index}) do not match anchor length {anchor_of}")
        self.annotation_units = annotation_units
        uri = apply_uri_scheme(uri_prefix=reference_context_uri,
                               begin_end_index=(begin_index, end_index))
        super(NIFString, self).__init__(uri=uri)

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
        unknown = INCLUDE
        rdf_type = [nif_ns.String, nif_ns.OffsetBasedString]
        model = NIFString


class NIFStructure(NIFString):
    pass


class NIFStructureSchema(NIFStringSchema):
    class Meta:
        unknown = INCLUDE
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
        unknown = INCLUDE
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
        unknown = INCLUDE
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
        unknown = INCLUDE
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
        unknown = INCLUDE
        rdf_type = swcnif_ns.Chunk
        model = SWCNIFChunk


class SWCNIFNamedEntityOccurrence(NIFPhrase):
    rdf_classes = (swcnif_ns.NamedEntityOccurrence, nif_ns.Phrase)

    def __init__(self,
                 begin_index: int,
                 end_index: int,
                 reference_context_uri: str,
                 class_uri: str = None,
                 confidence: float = None,
                 annotator_uri: str = None,
                 property_uri: str = None,
                 anchor_of: str = None,
                 sentence_uri: str = None,
                 words_uris: List[str] = None,
                 annotation_units: List[NIFAnnotationUnit] = None):
        super(SWCNIFNamedEntityOccurrence, self).__init__(reference_context_uri=reference_context_uri,
                                                          begin_index=begin_index, end_index=end_index,
                                                          anchor_of=anchor_of,
                                                          sentence_uri=sentence_uri,
                                                          words_uris=words_uris)

        self.annotation_units = []
        annotation_units = annotation_units if annotation_units is not None else []
        annotation_units.append(NIFAnnotationUnit(class_ref=class_uri,
                                               confidence=confidence,
                                               annotator_ref=annotator_uri,
                                               prop_ref=property_uri))
        for au in annotation_units:
            if au.class_ref is not None:
                self.annotation_units.append(au)


class SWCNIFNamedEntityOccurrenceSchema(NIFPhraseSchema):
    class Meta:
        unknown = INCLUDE
        rdf_type = swcnif_ns.NamedEntityOccurrence
        model = SWCNIFNamedEntityOccurrence
        inherit_parent_types = False


class SWCNIFMatchedResourceOccurrence(NIFPhrase):
    def __init__(self,
                 begin_index: int,
                 end_index: int,
                 reference_context_uri: str,
                 entity_uri: str = None,
                 confidence: float = None,
                 annotator_uri: str = None,
                 entity_class = None,
                 anchor_of: str = None,
                 sentence_uri: str = None,
                 words_uris: List[str] = None,
                 annotation_units: List[NIFAnnotationUnit] = None):
        super(SWCNIFMatchedResourceOccurrence, self).__init__(reference_context_uri=reference_context_uri,
                                                              begin_index=begin_index, end_index=end_index,
                                                              anchor_of=anchor_of,
                                                              sentence_uri=sentence_uri,
                                                              words_uris=words_uris)

        self.annotation_units = []
        annotation_units = annotation_units if annotation_units is not None else []
        annotation_units.append(NIFAnnotationUnit(ident_ref=entity_uri,
                                                  confidence=confidence,
                                                  annotator_ref=annotator_uri,
                                                  class_ref=entity_class))
        for au in annotation_units:
            if au.ident_ref is not None:
                self.annotation_units.append(au)


class SWCNIFMatchedResourceOccurrenceSchema(NIFPhraseSchema):
    class Meta:
        unknown = INCLUDE
        rdf_type = swcnif_ns.MatchedResourceOccurrence
        model = SWCNIFMatchedResourceOccurrence
        inherit_parent_types = False


class NIFDocument:
    class NifDocElements():
        """
        - attributes should be dictionaries in the format uri: [object]
        - lists should be used for non-object triples
        - attributes should be altered via dedicated functions (set_element, append_element)
        not directly (e.g., element.attribute[id]=value)
        """

        def __init__(self, context=None, words=None, sentences=None, phrases=None, other=None, ):
            self._context = defaultdict(list) if context is None else defaultdict(list, context)
            self._words = defaultdict(list) if words is None else defaultdict(list, words)
            self._sentences = defaultdict(list) if sentences is None else defaultdict(list, sentences)
            self._phrases = defaultdict(list) if phrases is None else defaultdict(list, phrases)
            self._other = [] if other is None else other

    def __init__(self, context=None, words=None, sentences=None, phrases=None, other=None, schema_dict=None):
        self.elements = self.NifDocElements(context=context, words=words, sentences=sentences, phrases=phrases,
                                            other=other)
        self._schema_dict = defaultdict(list) if schema_dict is None else defaultdict(list, schema_dict)


    def set_element(self, attribute, values, schemas_dict=None):
        if attribute in ["context", "words", "sentences", "phrases"]:
            self.elements.__setattr__(attribute, values)
            self._schema_dict.update(schemas_dict)
        elif attribute == "other":
            self.elements._other = values
        else:
            raise NotImplementedError(f"Attribute {attribute} not in {self.elements.__dict__.items()}")


    def append_element(self, attribute, value, schema=None):
        if attribute in ["context", "words", "sentences", "phrases"]:
            if schema is None:
                raise ValueError("You must provide a schema for the value to be appended.")
            _id = value.uri
            self.elements.__getattribute__("_" + attribute)[_id].append(value)
            self._schema_dict[_id].append(schema)
        elif attribute == "other":
            self.elements._other.append(value)
        else:
            raise NotImplementedError(f"Attribute {attribute} not in {self.elements.__dict__.items()}")

    #todo remove_element

    def serialize(self):
        json_objs = []
        attributes = self.elements.__dict__
        for k, v in attributes.items():
            # elements in the schema
            if isinstance(v, dict):
                for uri, objs in v.items():
                    merged_json_obj = None
                    for i, obj in enumerate(objs):
                        json_obj = self._schema_dict[uri][i]().dump(obj)
                        if merged_json_obj is None:
                            merged_json_obj = json_obj
                        else:
                            merged_json_obj = utils._merge_dicts(merged_json_obj, json_obj)
                    json_objs.append(merged_json_obj)
            # other elements
            elif isinstance(v, list):
                json_objs += v
        return json_objs


    @staticmethod
    def _parse_obj(json_obj, all_objs=None):
        """
        provides all schemas and associated json-objects to a given object
        an associated json-object is e.g., an object, which is referenced by @id in json-object in a
        flattened file format
        :param json_obj: focus json object
        :param all_objs: all json objects of the json-ld doc
        :return: relevant json_objs associated with json_obj, schemas associated with json_obj
        """
        obj_types = json_obj["@type"]
        schemas = []
        json_objs = []
        check_for_flattened = False
        if swcnif_ns.NamedEntityOccurrence in obj_types or swcnif_ns.NamedEntity in obj_types:
            schemas.append(SWCNIFNamedEntityOccurrenceSchema)
            check_for_flattened = True
        if swcnif_ns.MatchedResourceOccurrence in obj_types or swcnif_ns.ExtractedEntity in obj_types:
            schemas.append(SWCNIFMatchedResourceOccurrenceSchema)
            check_for_flattened = True
        if not schemas:
            if swcnif_ns.Chunk in obj_types:
                schemas.append(SWCNIFChunkSchema)
            elif nif_ns.Sentence in obj_types:
                schemas.append(NIFSentenceSchema)
            elif nif_ns.Word in obj_types:
                schemas.append(NIFWordSchema)
            elif nif_ns.Phrase in obj_types:
                schemas.append(NIFPhraseSchema)
            elif nif_ns.Context in obj_types:
                schemas.append(NIFContextSchema)
            elif nif_ns.AnnotationUnit in obj_types:
                pass  # this should  be handled by the specific annotations
            elif nif_ns.Annotation in obj_types:
                pass  # this should  be handled by the specific annotations
            else:
                schemas.append(None)
        if check_for_flattened:
            json_obj, all_objs, ids = utils._flatten_references_to_external_resources(json_obj, all_objs)
            json_obj = [all_objs[i] for i in ids]

        for schema in schemas:
            if schema is not None:
                json_objs.append(schema(flattened=True).load(json_obj))
            else:
                json_objs.append(json_obj)
        return json_objs, schemas

    @classmethod
    def from_json(cls, json_data):
        # todo schema_dict should be more secure to keep in sync
        schema_dict = defaultdict(list)
        phrases = defaultdict(list)
        sentences = defaultdict(list)
        words = defaultdict(list)
        context = defaultdict(list)
        others = []

        if "@context" in json_data:
            json_data = jsonld.expand(json_data)
        obj_dict = {o["@id"]: o for o in json_data}
        for obj in json_data:
            nif_objs, schemas = cls._parse_obj(obj, obj_dict)
            for nif_obj, schema in zip(nif_objs, schemas):
                if nif_obj is not None:
                    if isinstance(nif_obj, NIFContext):
                        context[nif_obj.uri].append(nif_obj)
                    elif isinstance(nif_obj, NIFPhrase):
                        phrases[nif_obj.uri].append(nif_obj)
                    elif isinstance(nif_obj, NIFSentence):
                        sentences[nif_obj.uri].append(nif_obj)
                    elif isinstance(nif_obj, NIFWord):
                        words[nif_obj.uri].append(nif_obj)
                    elif isinstance(nif_obj, dict):
                        others.append(nif_obj)
                    else:
                        raise NotImplementedError
                    if schema is not None:
                        schema_dict[nif_obj.uri].append(schema)
        return cls(context=context, words=words, sentences=sentences, phrases=phrases, other=others,
                   schema_dict=schema_dict)


    def __eq__(self, other):
        if isinstance(other, self.__class__):
            self.serialize()
            other.serialize()
            return self.serialize() == other.serialize()
        else:
            return False


if __name__ == '__main__':
    pass