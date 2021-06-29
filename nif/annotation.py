import uuid
from enum import Enum
from typing import List, Tuple

import rdflib

from nif.namespace import ns_dict

nif_ns = ns_dict['nif']
swcnif_ns = rdflib.Namespace('https://semantic-web.com/research/nif#')


class NIFError(Exception):
    pass


class URIScheme(Enum):
    nif_ns.ContextHashBasedString = nif_ns.ContextHashBasedString
    nif_ns.RFC5147String = nif_ns.RFC5147String
    nif_ns.CStringInst = nif_ns.CStringInst
    nif_ns.OffsetBasedString = nif_ns.OffsetBasedString


def do_suffix_offset(uri, begin_index, end_index):
    # TODO: add uri_scheme and add support for RFC5147String
    uri_str = uri.toPython() if hasattr(uri, 'toPython') else str(uri)
    uri_str = uri_str.rstrip('/')
    chars_indicator = '#offset_'
    if chars_indicator in uri_str:
        splitted = uri_str.split(chars_indicator)
        splitted[-1] = '{}_{}'.format(begin_index, end_index)
        out = chars_indicator.join(splitted)
    else:
        out = uri_str + chars_indicator + '{}_{}'.format(begin_index,
                                                         end_index)
    return rdflib.URIRef(out)


def apply_uri_scheme(nif_resource,
                     uri_prefix: str,
                     uri_scheme: URIScheme,
                     begin_end_index: Tuple[int, int]):
    # assert uri_scheme in [nif_ns.ContextHashBasedString,
    #                       nif_ns.RFC5147String, nif_ns.CStringInst,
    #                       nif_ns.OffsetBasedString]
    if uri_scheme == nif_ns.OffsetBasedString:
        nif_classes = list(nif_resource.rdf_classes)
        nif_classes.append(uri_scheme)
        nif_resource.rdf_classes = tuple(nif_classes)
        return do_suffix_offset(uri_prefix, *begin_end_index)
    else:
        raise NotImplementedError(f'The URI scheme {uri_scheme} is not implemented yet.')



def _parse_attr_name(name):
    try:
        prefix, suffix = name.split('__')
    except Exception:
        raise ValueError('Not able to parse {}: no "__" found'.format(name))
    try:
        ns = ns_dict[prefix.lower()]
    except KeyError:
        raise AttributeError(
            'Namespace with the key "{}" not found'.format(prefix))
    splitted = suffix.split('_')
    for i in range(len(splitted)):
        if i > 0:
            x = splitted[i]
            x = x[0].upper() + x[1:]
            splitted[i] = x
    rdf_suffix = ''.join(splitted)
    predicate = ns[rdf_suffix]
    return predicate


def register_ns(key, ns):
    assert isinstance(ns, rdflib.Namespace)
    ns_dict[key] = ns

register_ns('swcnif', swcnif_ns)


def to_rdf_literal(value, datatype=None):
    if isinstance(value, (rdflib.URIRef, rdflib.Literal,
                          rdflib.BNode, rdflib.Variable)):
        return value
    elif datatype is not None:
        return rdflib.Literal(value, datatype=datatype)
    else:
        return rdflib.Literal(value)


class NIFGetSetMixin(rdflib.Graph):

    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattribute__(name)
        elif '__' in name:
            predicate = _parse_attr_name(name)
            rs = list(self.objects(subject=self.uri, predicate=predicate))
            if len(rs) == 1:
                return rs.pop()
            elif len(rs) == 0:
                return None
            else:
                return rs
        else:
            return super().__getattribute__(name)

    def __setattr__(self, name, value, validate=True, datatype=None):
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif '__' in name:
            predicate = _parse_attr_name(name)
            self.remove((self.uri, predicate, None))
            if value is None or (hasattr(value, "__len__") and len(value) == 0):
                pass
            elif isinstance(value, (list, tuple)):
                self.remove((self.uri, predicate, None))
                for val_item in value:
                    self.add((self.uri, predicate,
                              to_rdf_literal(val_item, datatype=datatype)))
            else:
                self.set((self.uri, predicate,
                          to_rdf_literal(value, datatype=datatype)))
            if validate:
                self.validate()
        else:
            super().__setattr__(name, value)

    def addattr(self, name, value, validate=True, datatype=None):
        assert '__' in name, name
        predicate = _parse_attr_name(name)
        if isinstance(value, (list, tuple)):
            for val_item in value:
                self.add((self.uri, predicate,
                          to_rdf_literal(val_item, datatype=datatype)))
        else:
            self.add((self.uri, predicate,
                      to_rdf_literal(value, datatype=datatype)))
        if validate:
            self.validate()

    def delattr(self, name, value, validate=True):
        assert '__' in name, name
        predicate = _parse_attr_name(name)
        if isinstance(value, (list, tuple)):
            for val_item in value:
                self.remove((self.uri, predicate, to_rdf_literal(val_item)))
        else:
            self.remove((self.uri, predicate, to_rdf_literal(value)))
        if validate:
            self.validate()

    def add_rdf_classes(self):
        for cls in self.rdf_classes:
            self.add((self.uri, rdflib.RDF.type, cls))
        return self

    def validate(self):
        raise NotImplementedError


class NIFAnnotation(NIFGetSetMixin):
    rdf_classes = (nif_ns.Annotation,)

    def __init__(self,
                 uri: str = None,
                 **kwargs):
        """
        A class to store NIF annotation block for a single entity.

        :param **kwargs: any additional (predicate, object) pairs
        """
        super(NIFAnnotation, self).__init__()
        self.uri = rdflib.URIRef(uri) if uri is not None else rdflib.BNode()
        for key, val in kwargs.items():
            self.__setattr__(key, val)
        self.add_rdf_classes()

    def validate(self):
        return True


class NIFAnnotationUnit(NIFAnnotation):
    rdf_classes = (nif_ns.AnnotationUnit,)

    def __init__(self,
                 uri: str = None,
                 **kwargs):
        """
        :param str uri: URI of this AU
        :param dict po_dict: predict to object dict. predicates are URIRefs
        """
        super(NIFAnnotationUnit, self).__init__(uri=uri, **kwargs)

    @classmethod
    def from_triples(cls, rdf_graph, ref_string_uri):
        au_uris = list(rdf_graph[ref_string_uri:nif_ns.annotationUnit:])
        aus = []
        for au_uri in au_uris:
            au_dict = {p_uri: o_uri for p_uri, o_uri in rdf_graph[au_uri::]}
            au = cls(uri=au_uri, **au_dict)
            aus.append(au)
        return aus


class NIFString(NIFGetSetMixin):
    rdf_classes = (nif_ns.String, )

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 uri_scheme=nif_ns.OffsetBasedString,
                 annotation_units: List[NIFAnnotationUnit] = None,
                 anchor_of=None,
                 **kwargs):
        """
        A class to store NIF annotation block for a single entity.

        :param List[NIFAnnotationUnit] annotation_units:
        :param begin_end_index: tuple (begin_index, end_index). If `None` then
            begin_index = 0. see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e436
        :param reference_context: see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e1047
        :param uri_prefix: the prefix of the resulting URI. For example,
            `http://example.doc` would produce a URI of the form
            `http://example.doc#char=0,100`.
            :note: Only used if reference context is not given.
        :param anchor_of: see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e395
        :param **kwargs: any additional (predicate, object) pairs
        """
        super(NIFString, self).__init__()
        assert reference_context is not None
        self.reference_context = reference_context

        # uri_prefix = rdflib.URIRef(uri_prefix) or rdflib.BNode()
        if not isinstance(self, NIFContext):
            uri_prefix = reference_context.uri
            self.uri = apply_uri_scheme(self, uri_prefix, uri_scheme, begin_end_index)
            self.__setattr__('nif__reference_context', reference_context.uri,
                             validate=False)

        for key, val in kwargs.items():
            self.__setattr__(key, val)
        try:
            begin_end_index = tuple(map(int, begin_end_index))
        except ValueError:
            raise ValueError(
                'begin_end_index should be convertible to integers, '
                '{} provided'.format(begin_end_index))
        self.__setattr__('nif__begin_index', begin_end_index[0], validate=False,
                         datatype=rdflib.XSD.nonNegativeInteger)
        self.__setattr__('nif__end_index', begin_end_index[1], validate=False,
                         datatype=rdflib.XSD.nonNegativeInteger)
        if anchor_of is not None:
            self.__setattr__('nif__anchor_of', anchor_of, validate=False)
        self.add_rdf_classes()
        self.validate()
        self.annotation_units = annotation_units

    @property
    def annotation_units(self):
        return self.annotation_units_

    @annotation_units.setter
    def annotation_units(self, aus: List[NIFAnnotationUnit]):
        aus_ = aus or []
        if aus_:
            self.nif__annotation_unit = [au.uri for au in aus]
        self.annotation_units_ = aus_

    def validate(self):
        if self.reference_context is not None:
            if not NIFContext.is_context(self.reference_context):
                raise ValueError(
                    'The provided reference context is not compatible with '
                    'nif.Context class.')
        if self.nif__anchor_of is not None:
            ref_substring = self.reference_context.nif__is_string[
                            int(self.nif__begin_index):int(self.nif__end_index)]
            # Extractor returns different capitalization in matches!
            if self.nif__anchor_of.toPython().lower() != ref_substring.lower():
                print(self.reference_context.nif__is_string, int(self.nif__begin_index),
                      int(self.nif__end_index))
                raise ValueError(
                    'Anchor should be equal exactly to the subtring of '
                    'the reference context. You have anchor = "{}", '
                    'substring in ref context = "{}"'.format(
                        self.nif__anchor_of, ref_substring))


class NIFContext(NIFString):
    rdf_classes = (nif_ns.Context, )

    def __init__(self,
                 uri: str,
                 is_string: str,
                 predLang: str = None,
                 **kwargs):
        """
        :param is_string: see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e669
        """
        begin_end_index = (0, len(is_string))
        self.uri = rdflib.URIRef(uri)
        super().__init__(
            begin_end_index=begin_end_index,
            reference_context=self,
            **kwargs
        )
        self.__setattr__('nif__is_string', is_string, False)
        self.__setattr__('nif__pred_lang', predLang, False)

    # def validate(self):
    #     if not isinstance(self.nif__is_string, str):
    #         raise TypeError('is_string value {} should be '
    #                         'a string'.format(self.nif__is_string))
    #     if int(self.nif__begin_index) != 0 or \
    #             int(self.nif__end_index) != len(self.nif__is_string):
    #         raise ValueError(
    #             'Begin and end indices are provided ({}), '
    #             'but do not fit the provided string (length = {})'
    #             '.'.format((self.nif__begin_index, self.nif__end_index),
    #                        len(self.nif__is_string)))

    @staticmethod
    def is_context(cxt):
        return isinstance(cxt, NIFContext)

    @classmethod
    def from_triples(cls, rdf_graph, context_uri):
        is_string = None
        other_triples = rdflib.Graph()
        for s, p, o in rdf_graph:
            if s != context_uri:
                other_triples.add((s, p, o))
            elif p == nif_ns.isString:
                if is_string is not None:
                    raise ValueError('{} found twice.'.format(p))
                is_string = o.toPython()
                uri = s.toPython()
                assert str(uri) == str(context_uri)
            else:
                other_triples.add((s, p, o))

        if is_string is None:
            raise NIFError(f'For a context no nif:is_string predicate was found.')
        out = cls(uri=context_uri, is_string=is_string)
        out += other_triples
        return out


class NIFStructure(NIFString):
    rdf_classes = (nif_ns.Structure,)

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 anchor_of=None,
                 **kwargs):
        super().__init__(
            begin_end_index=begin_end_index,
            reference_context=reference_context,
            anchor_of=anchor_of,
            **kwargs)

    # @classmethod
    # def from_triples(cls, rdf_graph, ref_cxt):
    #     begin_index = None
    #     end_index = None
    #     anchor_of = None
    #     other_triples = rdflib.Graph()
    #     for s, p, o in rdf_graph:
    #         if p == nif_ns.beginIndex:
    #             begin_index = int(o.toPython())
    #         elif p == nif_ns.endIndex:
    #             end_index = int(o.toPython())
    #         elif p == nif_ns.referenceContext:
    #             ref_cxt_uriref = o
    #             assert ref_cxt_uriref == ref_cxt.uri, \
    #                 (ref_cxt_uriref, ref_cxt.uri)
    #         elif p == nif_ns.anchorOf:
    #             anchor_of = o.toPython()
    #             # pass
    #         else:
    #             other_triples.add((s, p, o))
    #     if begin_index is None or end_index is None:
    #         raise NIFError(f'Begin or end index was not found for the structure {s}')
    #     begin_end_index = begin_index, end_index
    #     out = cls(reference_context=ref_cxt, begin_end_index=begin_end_index, anchor_of=anchor_of)
    #     out += other_triples
    #     return out


class NIFSentence(NIFStructure):
    rdf_classes = (nif_ns.Sentence,)

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 anchor_of=None,
                 next_sentence_uri: rdflib.URIRef = None,
                 previous_sentence_uri: rdflib.URIRef = None,
                 word_uris: List[rdflib.URIRef] = None,
                 **kwargs):
        super().__init__(
            begin_end_index=begin_end_index,
            reference_context=reference_context,
            anchor_of=anchor_of,
            **kwargs)
        self.nif__previous_sentence = previous_sentence_uri
        self.nif__next_sentence = next_sentence_uri
        self.nif__word = word_uris

    # @property
    # def next_sentence(self):
    #     return self.next_sentence_
    #
    # @next_sentence.setter
    # def next_sentence(self, next_sentence: 'NIFSentence'):
    #     self.next_sentence_ = next_sentence
    #     if next_sentence is not None:
    #         self.nif__next_sentence = next_sentence.uri
    #
    # @property
    # def previous_sentence(self):
    #     return self.previous_sentence_
    #
    # @previous_sentence.setter
    # def previous_sentence(self, previous_sentence: 'NIFSentence'):
    #     self.previous_sentence_ = previous_sentence
    #     if previous_sentence is not None:
    #         self.nif__previous_sentence = previous_sentence.uri
    #
    # @property
    # def words(self):
    #     return self.words_
    #
    # @words.setter
    # def words(self, words: List['NIFWord']):
    #     words_ = words or []
    #     self.words_ = words_
    #     self.nif__word = [w.uri for w in words_]

    @classmethod
    def from_triples(cls, rdf_graph, ref_cxt, self_uri):
        begin_index = None
        end_index = None
        anchor_of = None
        next_sentence_uri = None
        previous_sentence_uri = None
        word_uris = []
        other_triples = rdflib.Graph()
        for p, o in rdf_graph[self_uri::]:
            if p == nif_ns.beginIndex:
                begin_index = int(o.toPython())
            elif p == nif_ns.endIndex:
                end_index = int(o.toPython())
            elif p == nif_ns.referenceContext:
                ref_cxt_uriref = o
                assert ref_cxt_uriref == ref_cxt.uri, \
                    (ref_cxt_uriref, ref_cxt.uri)
            elif p == nif_ns.anchorOf:
                anchor_of = o.toPython()
            elif p == nif_ns.nextSentence:
                next_sentence_uri = o
            elif p == nif_ns.previousSentence:
                previous_sentence_uri = o
            elif p == nif_ns.word:
                word_uris.append(o)
            else:
                other_triples.add((self_uri, p, o))
        if begin_index is None or end_index is None:
            raise NIFError(f'Begin or end index was not found for the sentence {self_uri}')
        begin_end_index = begin_index, end_index
        out = cls(reference_context=ref_cxt,
                  begin_end_index=begin_end_index,
                  anchor_of=anchor_of,
                  next_sentence_uri=next_sentence_uri,
                  previous_sentence_uri=previous_sentence_uri,
                  word_uris=word_uris
                  )
        out += other_triples
        aus = NIFAnnotationUnit.from_triples(rdf_graph=rdf_graph, ref_string_uri=out.uri)
        out.annotation_units = aus
        return out


class NIFWord(NIFStructure):
    rdf_classes = (nif_ns.Word, )

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 anchor_of=None,
                 pos_tag: str = None,
                 next_word_uri: rdflib.URIRef = None,
                 previous_word_uri: rdflib.URIRef = None,
                 sentence_uri: rdflib.URIRef = None,
                 **kwargs):
        super().__init__(
            begin_end_index=begin_end_index,
            reference_context=reference_context,
            anchor_of=anchor_of,
            **kwargs)
        self.nif__pos_tag = pos_tag
        self.nif__sentence = sentence_uri
        self.nif__next_word = next_word_uri
        self.nif__previous_word = previous_word_uri

    # @property
    # def next_word_uri(self):
    #     return self.nif__next_word
    #
    # @next_word_uri.setter
    # def next_word_uri(self, next_word_uri: rdflib.URIRef):
    #     self.nif__next_word = next_word_uri
    #
    # @property
    # def previous_word(self):
    #     return self.previous_word_
    #
    # @previous_word.setter
    # def previous_word(self, previous_word: 'NIFWord'):
    #     self.previous_word_ = previous_word
    #     if previous_word is not None:
    #         self.nif__previous_word = previous_word.uri
    #
    # @property
    # def sentence(self):
    #     return self.sentence_
    #
    # @sentence.setter
    # def sentence(self, sentence: NIFSentence):
    #     self.sentence_ = sentence
    #     if sentence is not None:
    #         self.nif__sentence = sentence.uri

    @classmethod
    def from_triples(cls, rdf_graph, ref_cxt, self_uri):
        begin_index = None
        end_index = None
        anchor_of = None
        next_word_uri = None
        previous_word_uri = None
        sentence_uri = None
        pos_tag = None
        other_triples = rdflib.Graph()
        for p, o in rdf_graph[self_uri::]:
            if p == nif_ns.beginIndex:
                begin_index = int(o.toPython())
            elif p == nif_ns.endIndex:
                end_index = int(o.toPython())
            elif p == nif_ns.referenceContext:
                ref_cxt_uriref = o
                assert ref_cxt_uriref == ref_cxt.uri, \
                    (ref_cxt_uriref, ref_cxt.uri)
            elif p == nif_ns.anchorOf:
                anchor_of = o.toPython()
            elif p == nif_ns.nextWord:
                next_word_uri = o
            elif p == nif_ns.previousWord:
                previous_word_uri = o
            elif p == nif_ns.sentence:
                sentence_uri = o
            elif p == nif_ns.posTag:
                pos_tag = o.toPython()
            else:
                other_triples.add((self_uri, p, o))
        if begin_index is None or end_index is None:
            raise NIFError(f'Begin or end index was not found for the structure {self_uri}')
        begin_end_index = begin_index, end_index
        out = cls(reference_context=ref_cxt,
                  begin_end_index=begin_end_index,
                  anchor_of=anchor_of,
                  next_word_uri=next_word_uri,
                  previous_word_uri=previous_word_uri,
                  sentence_uri=sentence_uri,
                  pos_tag=pos_tag)
        out += other_triples
        aus = NIFAnnotationUnit.from_triples(rdf_graph=rdf_graph, ref_string_uri=out.uri)
        out.annotation_units = aus
        return out


class NIFPhrase(NIFStructure):
    rdf_classes = (nif_ns.Phrase, )

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 anchor_of: str = None,
                 sentence_uri: rdflib.URIRef = None,
                 word_uris: List[rdflib.URIRef] = None,
                 **kwargs):
        super().__init__(
            begin_end_index=begin_end_index,
            reference_context=reference_context,
            anchor_of=anchor_of,
            **kwargs)
        self.swcnif__sentence = sentence_uri
        self.swcnif__word = word_uris

    # @property
    # def words(self):
    #     return self.words_
    #
    # @words.setter
    # def words(self, words: List['NIFWord']):
    #     words_ = words or []
    #     self.words_ = words_
    #     self.swcnif__word = [w.uri for w in words_]
    #
    # @property
    # def sentence(self):
    #     return self.sentence_
    #
    # @sentence.setter
    # def sentence(self, sentence: NIFSentence):
    #     self.sentence_ = sentence
    #     if sentence is not None:
    #         self.swcnif__sentence = sentence.uri

    @classmethod
    def from_triples(cls, rdf_graph, ref_cxt, self_uri):
        begin_index = None
        end_index = None
        anchor_of = None
        word_uris = []
        sentence_uri = None
        other_triples = rdflib.Graph()
        for p, o in rdf_graph[self_uri::]:
            if p == nif_ns.beginIndex:
                begin_index = int(o.toPython())
            elif p == nif_ns.endIndex:
                end_index = int(o.toPython())
            elif p == nif_ns.referenceContext:
                ref_cxt_uriref = o
                assert ref_cxt_uriref == ref_cxt.uri, \
                    (ref_cxt_uriref, ref_cxt.uri)
            elif p == nif_ns.anchorOf:
                anchor_of = o.toPython()
            elif p == swcnif_ns.word:
                word_uris.append(o)
            elif p == nif_ns.sentence:
                sentence_uri = o
            else:
                other_triples.add((self_uri, p, o))
        if begin_index is None or end_index is None:
            raise NIFError(f'Begin or end index was not found for the phrase {self_uri}')
        begin_end_index = begin_index, end_index
        out = cls(reference_context=ref_cxt,
                  begin_end_index=begin_end_index,
                  anchor_of=anchor_of,
                  word_uris=word_uris,
                  sentence_uri=sentence_uri
                  )
        out += other_triples
        aus = NIFAnnotationUnit.from_triples(rdf_graph=rdf_graph, ref_string_uri=out.uri)
        out.annotation_units = aus
        return out


class SWCNIFChunk(NIFPhrase):
    rdf_classes = (swcnif_ns.Chunk,)

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 chunk_type: str,
                 anchor_of=None,
                 **kwargs):
        super().__init__(
            begin_end_index=begin_end_index,
            reference_context=reference_context,
            anchor_of=anchor_of,
            **kwargs)
        self.swcnif__chunk_type = chunk_type


class SWCNIFNamedEntityOccurrence(NIFPhrase):
    rdf_classes = (swcnif_ns.NamedEntity,)

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 class_uri: str,
                 confidence: float = None,
                 annotator_uri: str = None,
                 anchor_of=None,
                 **kwargs):
        if annotator_uri is not None:
            annotator_uri = rdflib.URIRef(annotator_uri)
        if class_uri is not None:
            class_uri = rdflib.URIRef(class_uri)
        au = NIFAnnotationUnit(itsrdf__ta_class_ref=class_uri,
                               itsrdf__ta_confidence=confidence,
                               itsrdf__ta_annotator_ref=annotator_uri)
        super().__init__(
            reference_context=reference_context,
            begin_end_index=begin_end_index,
            anchor_of=anchor_of,
            **kwargs)
        self.annotation_units = [au]


class SWCNIFMatchedResourceOccurrence(NIFPhrase):
    rdf_classes = (swcnif_ns.ExtractedEntity,)

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 entity_uri: str,
                 confidence: float = None,
                 annotator_uri: str = None,
                 anchor_of=None,
                 **kwargs):
        if annotator_uri is not None:
            annotator_uri = rdflib.URIRef(annotator_uri)
        if entity_uri is not None:
            entity_uri = rdflib.URIRef(entity_uri)
        au = NIFAnnotationUnit(itsrdf__ta_ident_ref=entity_uri,
                               itsrdf__ta_confidence=confidence,
                               itsrdf__ta_annotators_ref=annotator_uri)
        super().__init__(
            reference_context=reference_context,
            begin_end_index=begin_end_index, anchor_of=anchor_of,
            **kwargs)
        self.annotation_units = [au]


class NIFDocument:
    def __init__(self,
                 context: NIFContext,
                 words: List[NIFWord] = None,
                 sentences: List[NIFSentence] = None,
                 phrases: List[NIFPhrase] = None,
                 ):
        if not NIFContext.is_context(context):
            raise TypeError('The provided context {} is not a NIFContext'
                            '.'.format(context))
        self.context = context
        self.words = words
        self.sentences = sentences
        self.phrases = phrases
        self.validate()

    @property
    def words(self):
        return self.words_

    @words.setter
    def words(self, words: List['NIFWord']):
        words_ = words or []
        self.words_ = words_

    @property
    def sentences(self):
        return self.sentences_

    @sentences.setter
    def sentences(self, sentences: List['NIFSentence']):
        sentences_ = sentences or []
        self.sentences_ = sentences_

    @property
    def phrases(self):
        return self.phrases_

    @phrases.setter
    def phrases(self, phrases: List['NIFPhrase']):
        phrases_ = phrases or []
        self.phrases_ = phrases_

    def validate(self):
        for nif_res in self.words + self.sentences + self.phrases:
            if nif_res.reference_context.uri != self.context.uri:
                raise ValueError('The reference context {} for the structure {}'
                                 ' is different from the context {} of the '
                                 'document.'.format(
                                     nif_res.reference_context.uri,
                                     nif_res.uri, self.context.uri))

    @property
    def rdf(self):
        _rdf = self.context
        for nif_res in self.words + self.sentences + self.phrases:
            _rdf += nif_res
            for au in nif_res.annotation_units:
                _rdf += au
        return _rdf

    def serialize(self, format="xml", **kwargs):
        rdf_text = self.rdf.serialize(format=format, **kwargs)
        return rdf_text

    @classmethod
    def from_data(cls,
                  cxt_str: str,
                  words_data: List[Tuple[int, int]],
                  sents_data: List[Tuple[int, int]],
                  uri_prefix: str = None):
        """
        :param cxt_str: A string containing the context
        :param words_data: list of start and end offsets of words in the context
        :param sents_data: list of start and end words of each sentence
        """
        uri_prefix = rdflib.URIRef(uri_prefix) if uri_prefix is not None else rdflib.BNode()
        ref_cxt = NIFContext(
            uri=uri_prefix,
            is_string=cxt_str
        )
        words = [
            NIFWord(begin_end_index=be,
                    reference_context=ref_cxt)
            for be in words_data
        ]
        sents = []
        for sent_data in sents_data:
            word_start = words[sent_data[0]]
            word_end = words[sent_data[1]]
            word_uris = [word.uri for word in words[sent_data[0]:sent_data[1]]]
            be = (word_start.nif__begin_index, word_end.nif__end_index)
            sent = NIFSentence(begin_end_index=be,
                               reference_context=ref_cxt,
                               word_uris=word_uris)
            sents.append(sent)
            for word in words[sent_data[0]:sent_data[-1]]:
                word.nif__sentence = sent.uri
        for i, word in enumerate(words):
            if i > 0:
                prev_word_uri = words[i-1].uri
                word.nif__previous_word = prev_word_uri
            if i+1 < len(words):
                next_word_uri = words[i+1].uri
                word.nif__next_word = next_word_uri
        out = cls(context=ref_cxt,
                  words=words,
                  sentences=sents)
        return out


    @classmethod
    def parse_rdf(cls, rdf_text, format="n3", context_class=nif_ns.Context):
        rdf_graph = rdflib.Graph()
        rdf_graph.parse(data=rdf_text, format=format)

        context_uri = rdf_graph.value(predicate=rdflib.RDF.type,
                                      object=context_class)
        if context_uri is None:
            raise ValueError(f'Provided RDF: \n{rdf_graph[:]}\n does not contain a context of class {context_class}.')
        context_triples = list(rdf_graph.triples((context_uri, None, None)))
        for t in context_triples:
            if isinstance(t[2], rdflib.BNode):
                context_triples += list(rdf_graph.triples((t[2], None, None)))
        context = NIFContext.from_triples(context_triples,
                                          context_uri=context_uri)

        struct_uris = set(rdf_graph[:nif_ns.referenceContext:context.uri])
        uri2struct = dict()

        words = []
        word_uris = [u for u in struct_uris if rdf_graph[u:rdflib.RDF.type:nif_ns.Word]]
        for word_uri in word_uris:
            word = NIFWord.from_triples(rdf_graph=rdf_graph, ref_cxt=context, self_uri=word_uri)
            words.append(word)
            uri2struct[word.uri] = word

        sentences = []
        sent_uris = [u for u in struct_uris if rdf_graph[u:rdflib.RDF.type:nif_ns.Sentence]]
        for word_uri in sent_uris:
            sentence = NIFSentence.from_triples(rdf_graph=rdf_graph, ref_cxt=context, self_uri=word_uri)
            sentences.append(sentence)
            uri2struct[sentence.uri] = sentence

        phrases = []
        phrase_uris = [u for u in struct_uris if rdf_graph[u:rdflib.RDF.type:nif_ns.Phrase]]
        for phrase_uri in phrase_uris:
            phrase = NIFPhrase.from_triples(rdf_graph=rdf_graph, ref_cxt=context, self_uri=phrase_uri)
            phrases.append(phrase)
            uri2struct[phrase.uri] = phrase

        out = cls(context=context,
                  words=words,
                  sentences=sentences,
                  phrases=phrases)

        for t in rdf_graph - out.rdf:
            # if t not in out.rdf:
            out.context.add(t)
        return out

    @classmethod
    def from_text(cls, text, uri="http://example.doc/" + str(uuid.uuid4())):
        cxt = NIFContext(is_string=text, uri=uri)
        return cls(context=cxt)

    def add_extracted_cpts(self, cpt_dicts,
                           confidence=1,
                           annotator_uri=ns_dict['lkg']['EL'],
                           **kwargs):
        """
        :param cpt_dict: expected to have 'uri',
            'matchings'-> [{'text': value,
                            'positions': [(begin, end), ...]},
                           ...]
        :return: self
        """
        ees = []
        for i, cpt_dict in enumerate(cpt_dicts):
            cpt_uri = cpt_dict['uri']
            for matches in cpt_dict['matchings']:
                for match in matches['positions']:
                    surface_form = self.context.nif__is_string[match[0]:match[1]]
                    ee = SWCNIFMatchedResourceOccurrence(
                        reference_context=self.context,
                        begin_end_index=(match[0], match[1]),
                        anchor_of=surface_form,
                        entity_uri=cpt_uri,
                        annotator_uri=annotator_uri,
                        confidence=confidence,
                        **kwargs
                    )
                    ees.append(ee)
        self.phrases += ees
        return self

    def __copy__(self):
        return NIFDocument.parse_rdf(self.serialize(format='n3'))

    def __eq__(self, other):
        return isinstance(other, NIFDocument) and \
               self.serialize(format='n3') == other.serialize(format='n3')


if __name__ == '__main__':
    pass


