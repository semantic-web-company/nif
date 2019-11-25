import re
import uuid
from typing import List

import rdflib

nif_ns = rdflib.namespace.ClosedNamespace(
    uri='http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#',
    terms=[
        # Classes
        "Phrase", "NormalizedContextOccurrence", "Structure",
        "CollectionOccurrence", "NormalizedCollectionOccurrence",
        "CStringInst", "OffsetBasedString", "Word", "Annotation", "Title",
        "ContextCollection", "URIScheme", "ContextOccurrence",
        "ContextHashBasedString", "RFC5147String", "Paragraph", "Sentence",
        "String", "CString", "Context", "AnnotationUnit", "TextSpanAnnotation"

        # ObjectProperties
        "superStringTrans", "lang", "previousWordTrans", "broaderContext",
        "opinion", "firstWord", "inter", "previousWord",
        "previousSentenceTrans", "sentence", "word", "hasContext", "sourceUrl",
        "referenceContext", "previousSentence", "nextSentenceTrans",
        "wasConvertedFrom", "lastWord", "oliaLink", "dependency",
        "nextSentence", "subString", "predLang", "subStringTrans",
        "narrowerContext", "dependencyTrans", "superString", "annotation",
        "nextWord", "nextWordTrans", "oliaProv", "annotationUnit",

        # Datatype Properties
        "anchorOf", "stem", "after", "dependencyRelationType", "oliaConf",
        "head", "isString", "lemma", "literalAnnotation", "confidence",
        "keyword", "topic", "endIndex", "before", "posTag", "beginIndex",
        "sentimentValue",

        #new ObjectProperty
        "summary"
    ]
)
itsrdf_ns = rdflib.Namespace(
    'https://www.w3.org/2005/11/its/rdf-content/its-rdf.html#')
ns_dict = {'nif': nif_ns,
           'itsrdf': itsrdf_ns,
           'rdf': rdflib.RDF,
           'rdfs': rdflib.RDFS,
           'owl': rdflib.OWL}


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


def to_rdf_literal(value, datatype=None):
    if isinstance(value, (rdflib.URIRef, rdflib.Literal,
                          rdflib.BNode, rdflib.Variable)):
        return value
    elif datatype is not None:
        return rdflib.Literal(value, datatype=datatype)
    else:
        return rdflib.Literal(value)


class RDFGetSetMixin(rdflib.Graph):
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
            if isinstance(value, (list, tuple)):
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

    def add_nif_classes(self):
        for cls in self.nif_classes:
            self.add((self.uri, rdflib.RDF.type, cls))
        return self

    def validate(self):
        raise NotImplementedError


class NIFAnnotationUnit(RDFGetSetMixin):
    nif_classes = [nif_ns.AnnotationUnit]

    def __init__(self, uri: str = None, **kwargs):
        """
        :param str uri: URI of this AU
        :param dict po_dict: predict to object dict. predicates are URIRefs
        """
        super().__init__()
        if uri is None:
            self.uri = rdflib.BNode()
        else:
            self.uri = uri
        for p, o in kwargs.items():
            if '__' in p:
                p_uri = _parse_attr_name(p)
            else:
                p_uri = p
                assert isinstance(p_uri, rdflib.URIRef), '{} is not a URIRef'.format(p)
            self.add((self.uri, p_uri, to_rdf_literal(o)))
        self.add((self.uri, rdflib.RDF.type, nif_ns.AnnotationUnit))

    def validate(self):
        return True


class NIFString(RDFGetSetMixin):
    nif_classes = []

    def __init__(self,
                 begin_end_index,
                 uri_prefix,
                 uri_scheme=nif_ns.OffsetBasedString,
                 **kwargs):
        """
        The base abstract class.

        :param begin_end_index: tuple (begin_index, end_index). If `None` then
            begin_index = 0. see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e436
        :param uri_prefix: the prefix of the resulting URI. For example,
            `http://example.doc` would produce a URI of the form
            `http://example.doc#char=0,100`.
        :param **kwargs: any additional (predicate, object) pairs
        """
        super().__init__()
        assert uri_scheme in [nif_ns.ContextHashBasedString,
                              nif_ns.RFC5147String, nif_ns.CStringInst,
                              nif_ns.OffsetBasedString]
        self.nif_classes.append(uri_scheme)
        try:
            begin_end_index = tuple(map(int, begin_end_index))
        except ValueError:
            raise ValueError(
                'begin_end_index should be convertible to integers, '
                '{} provided'.format(begin_end_index))
        self.reference_context = None  # this holds a separate graph
        self.uri = do_suffix_offset(uri_prefix, *begin_end_index)
        # URI obtained, set the predicate, object pairs
        self.__setattr__('nif__begin_index', begin_end_index[0], validate=False,
                         datatype=rdflib.XSD.nonNegativeInteger)
        self.__setattr__('nif__end_index', begin_end_index[1], validate=False,
                         datatype=rdflib.XSD.nonNegativeInteger)
        self.add_nif_classes()
        for key, val in kwargs.items():
            self.__setattr__(key, val)


class NIFAnnotation(NIFString):
    nif_classes = [nif_ns.Annotation]

    def __init__(self,
                 begin_end_index,
                 reference_context,
                 anchor_of=None,
                 annotation_units: List[NIFAnnotationUnit] = None,
                 uri_scheme=nif_ns.OffsetBasedString,
                 **kwargs):
        """
        A class to store NIF annotation block for a single entity. Hence,
        a single subject URI is used.

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
        uri_prefix = reference_context.uri_prefix
        super().__init__(begin_end_index=begin_end_index,
                         uri_prefix=uri_prefix,
                         uri_scheme=uri_scheme,
                         **kwargs)
        assert reference_context is not None
        self.reference_context = reference_context
        self.__setattr__('nif__reference_context', reference_context.uri,
                         validate=False)
        if anchor_of is not None:
            self.__setattr__('nif__anchor_of', anchor_of, validate=False)

        self.annotation_units = dict()
        if annotation_units is not None:
            for au in annotation_units:
                self.add_annotation_unit(au)
        self.validate()

    @staticmethod
    def is_annotation(cxt):
        return isinstance(cxt, NIFAnnotation)

    def add_annotation_unit(self, au: NIFAnnotationUnit):
        self.addattr('nif__annotation_unit', au.uri)
        self.annotation_units[au.uri] = au

    def remove_annotation_unit(self, au_uri: str):
        self.delattr('nif__annotation_unit', au_uri)
        del self.annotation_units[au_uri]

    def validate(self):
        if self.reference_context is not None:
            if not NIFContext.is_context(self.reference_context):
                raise ValueError(
                    'The provided reference context is not compatible with '
                    'nif.Context class.')
        if self.nif__is_string is not None:
            if not isinstance(self.nif__is_string, str):
                raise TypeError('is_string value {} should be '
                                'a string'.format(self.nif__is_string))
            if int(self.nif__begin_index) != 0 or \
                    int(self.nif__end_index) != len(self.nif__is_string):
                raise ValueError(
                    'Begin and end indices are provided ({}), '
                    'but do not fit the provided string (length = {})'
                    '.'.format((self.nif__begin_index, self.nif__end_index),
                               len(self.nif__is_string)))
        if self.nif__anchor_of is not None:
            ref_substring = self.reference_context.nif__is_string[
                            int(self.nif__begin_index):int(self.nif__end_index)]
            # Extractor returns different capitalization in matches!
            if self.nif__anchor_of.toPython().lower() != ref_substring.lower():
                raise ValueError(
                    'Anchor should be equal exactly to the subtring of '
                    'the reference context. You have anchor = "{}", '
                    'substring in ref context = "{}"'.format(
                        self.nif__anchor_of, ref_substring))

    @classmethod
    def from_triples(cls, rdf_graph, ref_cxt):
        kwargs = dict()
        other_triples = rdflib.Graph()
        for s, p, o in rdf_graph:
            if p == nif_ns.beginIndex:
                kwargs['begin_index'] = int(o.toPython())
            elif p == nif_ns.endIndex:
                kwargs['end_index'] = int(o.toPython())
            elif p == nif_ns.referenceContext:
                ref_cxt_uriref = o
                assert ref_cxt_uriref == ref_cxt.uri, \
                    (ref_cxt_uriref, ref_cxt.uri)
            elif p == nif_ns.anchorOf:
                kwargs['anchor_of'] = o.toPython()
            else:
                other_triples.add((s, p, o))
        # uri_prefix = s.toPython()
        kwargs['begin_end_index'] = kwargs['begin_index'], kwargs['end_index']
        del kwargs['begin_index']
        del kwargs['end_index']
        out = cls(reference_context=ref_cxt, **kwargs)
        out += other_triples
        return out


class NIFContext(NIFString):
    nif_classes = [nif_ns.Context]

    def __init__(self, is_string, uri_prefix,
                 uri_scheme=nif_ns.OffsetBasedString):
        """
        :param is_string: see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e669
        :param uri_prefix: the prefix of the resulting URI. For example,
            `http://example.doc` would produce a URI of the form
            `http://example.doc#char=0,100`.
            :note: Only used if reference context is not given.
        """
        begin_end_index = (0, len(is_string))
        super().__init__(
            begin_end_index=begin_end_index,
            is_string=is_string,
            uri_prefix=uri_prefix,
            uri_scheme=uri_scheme)
        self.uri_prefix = uri_prefix
        self.__setattr__('nif__is_string', is_string, False)

    def validate(self):
        return True

    @staticmethod
    def is_context(cxt):
        return isinstance(cxt, NIFContext)

    @classmethod
    def from_triples(cls, rdf_graph, ref_cxt=None):
        kwargs = dict()
        other_triples = rdflib.Graph()
        for s, p, o in rdf_graph:
            if p == nif_ns.isString:
                if 'is_string' in kwargs:
                    raise ValueError('{} found twice.'.format(p))
                kwargs['is_string'] = o.toPython()
            elif p == nif_ns.beginIndex:
                begin_index = int(o.toPython())
            elif p == nif_ns.endIndex:
                end_index = int(o.toPython())
            else:
                other_triples.add((s, p, o))
        uri_prefix = s.toPython()

        out = cls(uri_prefix=uri_prefix, **kwargs)
        if (int(out.nif__begin_index) != begin_index or
                int(out.nif__end_index) != end_index):
            raise ValueError('Check the provided begin and end indices!')
        out += other_triples
        return out


class NIFExtractedEntity(NIFAnnotation):
    def __init__(self, reference_context, begin_end_index, anchor_of,
                 entity_uri, **kwargs):
        au = NIFAnnotationUnit(itsrdf__ta_ident_ref=rdflib.URIRef(entity_uri))
        super().__init__(
            reference_context=reference_context,
            begin_end_index=begin_end_index, anchor_of=anchor_of,
            annotation_units=[au],
            **kwargs)


class NIFDocument:
    def __init__(self, context, annotations=None):
        if not NIFContext.is_context(context):
            raise TypeError('The provided context {} is not a NIFContext'
                            '.'.format(context))
        # self.rdf = rdflib.Graph()
        self.context = context
        self.uri_prefix = context.uri_prefix
        self.annotations = []
        if annotations is not None:
            for ann in annotations:
                self.add_annotation(ann)
        # self.rdf += self.context
        self.validate()

    def validate(self):
        for ann in self.annotations:
            if not NIFAnnotation.is_annotation(ann):
                raise TypeError('The provided structure {} is not a '
                                'NIFStructure.'.format(ann))
            if ann.nif__reference_context != self.context.uri:
                raise ValueError('The reference context {} for the structure {}'
                                 ' is different from the context {} of the '
                                 'document.'.format(
                                     ann.nif__reference_context,
                                     ann.uri, self.context.uri))

    @classmethod
    def from_text(cls, text, uri="http://example.doc/" + str(uuid.uuid4())):
        cxt = NIFContext(is_string=text, uri_prefix=uri)
        return cls(context=cxt, annotations=[])

    def add_annotation(self, ann: NIFAnnotation):
        self.annotations.append(ann)
        try:
            self.validate()
        except (ValueError, TypeError) as e:
            self.annotations.pop()
            raise e
        # else:
            # self.rdf += ann
        return self

    def add_extracted_entity(self, ee):
        self.add_annotation(ee)

    def add_extracted_cpt(self, cpt_dict):
        """
        :param cpt_dict: expected to have 'uri',
            'matchings'-> [{'text': value,
                            'positions': [(begin, end), ...]},
                           ...]
        :return: self
        """
        cpt_uri = cpt_dict['uri']
        for matches in cpt_dict['matchings']:
            for match in matches['positions']:
                surface_form = self.context.nif__is_string[match[0]:match[1]]
                ee = NIFExtractedEntity(
                    reference_context=self.context,
                    begin_end_index=(match[0], match[1]),
                    anchor_of=surface_form,
                    entity_uri=cpt_uri
                )
                self.add_extracted_entity(ee)
        return self

    @property
    def rdf(self):
        _rdf = self.context
        for ann in self.annotations:
            _rdf += ann
            for au in ann.annotation_units.values():
                _rdf += au
        return _rdf

    def serialize(self, format="xml", uri_format=nif_ns.OffsetBasedString):
        if uri_format not in [nif_ns.OffsetBasedString, nif_ns.RFC5147String]:
            raise ValueError("Only RFC5147 and OffsetBased strings are "
                             "currently soported URI schemes")
        rdf_text = self.rdf.serialize(format=format)

        if uri_format == nif_ns.RFC5147String:
            RFC5147_str = br"#char\=\(\1,\2\)"
            offset_regex = br"#offset_(\d*)_(\d*)"
            rdf_text = re.sub(offset_regex, RFC5147_str, rdf_text)
        return rdf_text

    @classmethod
    def parse_rdf(cls, rdf_text, format="n3"):
        rdf_graph = rdflib.Graph()
        rdf_graph.parse(data=rdf_text, format=format)

        context_uri = rdf_graph.value(predicate=rdflib.RDF.type,
                                      object=nif_ns.Context)
        context_triples = rdf_graph.triples((context_uri, None, None))
        context = NIFContext.from_triples(context_triples)

        annotations = []
        struct_uris = list(rdf_graph[:nif_ns.referenceContext:context.uri])
        for struct_uri in struct_uris:
            struct_triples = rdf_graph.triples((struct_uri, None, None))
            struct = NIFAnnotation.from_triples(struct_triples, ref_cxt=context)
            au_uris = list(rdf_graph[struct_uri:nif_ns.annotationUnit:])
            for au_uri in au_uris:
                au_dict = {p_uri: o_uri for p_uri, o_uri in rdf_graph[au_uri::]}
                au = NIFAnnotationUnit(uri=au_uri, **au_dict)
                struct.add_annotation_unit(au)
            annotations.append(struct)
        out = cls(context=context, annotations=annotations)

        return out

    def __copy__(self):
        return NIFDocument.parse_rdf(self.serialize(format='n3'))

    def __eq__(self, other):
        return isinstance(other, NIFDocument) and \
               self.serialize(format='n3') == other.serialize(format='n3')


if __name__ == '__main__':
    rdf_to_parse = '''
    @prefix dbo:   <http://dbpedia.org/ontology/> .
    @prefix geo:   <http://www.w3.org/2003/01/geo/wgs84_pos/> .
    @prefix dktnif: <http://dkt.dfki.de/ontologies/nif#> .
    @prefix nif-ann: <http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-annotation#> .
    @prefix rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
    @prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
    @prefix itsrdf: <https://www.w3.org/2005/11/its/rdf-content/its-rdf.html#> .
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
    #
    # print(f'Input: {rdf_to_parse}')
    # parsed = NIFDocument.parse_rdf(rdf_to_parse, format='turtle')
    # print(f'Parsed into NIFDocument')
    # context_str = parsed.context.nif__is_string
    # print(f'The nif:isString value: "{context_str}"')
    # structs = parsed.annotations
    # print(f'Number of annotations attached: {len(structs)}')
    # assert len(structs) == 1
    # ann = structs[0]
    # print(f'nif:anchorOf: "{ann.nif__anchor_of}", '
    #       f'itsrdf:taClassRef: "{ann.itsrdf__ta_class_ref}"')

    nifDocument = rdf_to_parse
    d = NIFDocument.parse_rdf(nifDocument, format='turtle')
    ann = NIFAnnotation(begin_end_index=(0, len(d.context.nif__is_string)))
    ann.nif__summary = "<your summary here>"
    d.add_annotation(ann)


