import uuid
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
        "String", "CString", "Context",

        # ObjectProperties
        "superStringTrans", "lang", "previousWordTrans", "broaderContext",
        "opinion", "firstWord", "inter", "previousWord",
        "previousSentenceTrans", "sentence", "word", "hasContext", "sourceUrl",
        "referenceContext", "previousSentence", "nextSentenceTrans",
        "wasConvertedFrom", "lastWord", "oliaLink", "dependency",
        "nextSentence", "subString", "predLang", "subStringTrans",
        "narrowerContext", "dependencyTrans", "superString", "annotation",
        "nextWord", "nextWordTrans", "oliaProv",

        # Datatype Properties
        "anchorOf", "stem", "after", "dependencyRelationType", "oliaConf",
        "head", "isString", "lemma", "literalAnnotation", "confidence",
        "keyword", "topic", "endIndex", "before", "posTag", "beginIndex",
        "sentimentValue",
    ]
)
itsrdf_ns = rdflib.Namespace(
    'https://www.w3.org/2005/11/its/rdf-content/its-rdf.html#')


def do_suffix_rfc5147(uri, begin_index, end_index):
    uri_str = uri.toPython() if hasattr(uri, 'toPython') else str(uri)
    chars_indicator = '#char='
    if chars_indicator in uri_str:
        splitted = uri_str.split(chars_indicator)
        splitted[-1] = '({},{})'.format(begin_index, end_index)
        out = chars_indicator.join(splitted)
    else:
        out = uri_str + chars_indicator + '({},{})'.format(begin_index,
                                                           end_index)
    return rdflib.URIRef(out)


def _parse_attr_name(name):
    prefix, suffix = name.split('__')
    if prefix.lower() == 'nif':
        ns = nif_ns
    elif prefix.lower() == 'itsrdf':
        ns = itsrdf_ns
    elif prefix.lower() == 'rdf':
        ns = rdflib.RDF
    elif prefix.lower() == 'rdfs':
        ns = rdflib.RDFS
    elif prefix.lower() == 'owl':
        ns = rdflib.OWL
    else:
        raise AttributeError(
            'rdf attributes should start either from "nif__" or'
            'from "itsrdf__", you started "{}__"'.format(prefix))
    splitted = suffix.split('_')
    for i in range(len(splitted)):
        if i > 0:
            x = splitted[i]
            x = x[0].upper() + x[1:]
            splitted[i] = x
    rdf_suffix = ''.join(splitted)
    predicate = ns[rdf_suffix]
    return predicate


class NIFAnnotation(rdflib.Graph):
    nif_classes = [nif_ns.String, nif_ns.RFC5147String]

    def __init__(self,
                 begin_end_index=None, is_string=None,
                 ta_ident_ref=None, reference_context=None,
                 uri_prefix=None, anchor_of=None,
                 **kwargs):
        """
        A class to store NIF annotation block for a single entity. Hence,
        a single subject URI is used.

        :param begin_end_index: tuple (begin_index, end_index). If `None` then
            begin_index = 0. see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e436
        :param is_string: see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e669
        :param ta_ident_ref: URI of the extracted entity.
        :param reference_context: see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e1047
        :param uri_prefix: the prefix of the resulting URI. For example,
            `http://example.doc/` would produce a URI of the form
            `http://example.doc/#char=0,100`.
            :note: Only used if reference context is not given.
        :param anchor_of: see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e395
        :param **kwargs: any additional (predicate, object) pairs
        """
        super().__init__()
        # Compute URI of itself
        if begin_end_index is None:
            if is_string is None:
                raise ValueError(
                    'Begin and end indices are not provided, '
                    'hence, is_string should be provided.')
            else:
                begin_end_index = (0, len(is_string))
        else:  # indices provided
            if is_string is not None:
                raise ValueError(
                    'Begin and end indices are provided ({}), '
                    'hence, is_string should be None '
                    '(provided {})'.format(begin_end_index, is_string))
            try:
                begin_end_index = tuple(map(int, begin_end_index))
            except ValueError as e:
                raise ValueError(
                    'begin_end_index should be convertible to integers, '
                    '{} provided'.format(begin_end_index))
        if reference_context is not None:  # this is a not a context
            if not NIFContext.is_context(reference_context):
                raise ValueError(
                    'The provided reference context is not compatible with '
                    'nif.Context class.')
            else:
                uri_prefix = reference_context.uri
        self.uri = do_suffix_rfc5147(uri_prefix, *begin_end_index)
        # URI obtained, set the predicate, object pairs
        self.nif__begin_index, self.nif__end_index = begin_end_index
        if is_string is not None:
            if not isinstance(is_string, str):
                raise TypeError('is_string value {} should be '
                                'a string'.format(is_string))
            if anchor_of is not None or \
                    reference_context is not None or \
                    ta_ident_ref is not None:
                raise ValueError(
                    'If is_string is provided then '
                    'ta_ident_ref, reference_context and anchor are not allowed'
                    '. You have reference context = {}, anchor = {}, '
                    'ta_ident_ref = {}.'.format(reference_context, anchor_of, ta_ident_ref))
            self.nif__is_string = is_string
        if ta_ident_ref is not None:
            if is_string is not None or \
                    reference_context is None or \
                    anchor_of is None:
                raise ValueError(
                    'If identifier ta_iden_ref is provided then '
                    'reference context and anchor are required and'
                    'is_string is not allowed. You have'
                    'reference context = {}, anchor = {}, is_string = {}'
                    '.'.format(reference_context, anchor_of, is_string)
                )
            self.itsrdf__ta_ident_ref = ta_ident_ref
        if reference_context is not None:
            if anchor_of is None:
                raise ValueError('When reference context is provided, '
                                 'anchor_of is required.')
            self.nif__reference_context = reference_context
        if anchor_of is not None:
            begin_index, end_index = begin_end_index
            ref_substring = reference_context.nif__is_string[0][
                            begin_index:end_index]
            assert anchor_of == ref_substring, \
                'Anchor should be equal exactly to the subtring of ' \
                'the reference context. You have anchor = {}, ' \
                'substring in ref context = {}'.format(
                    anchor_of, ref_substring)
            self.nif__anchor_of = anchor_of
        self.add_nif_classes()
        for key, val in kwargs.items():
            self.__setattr__(key, val)

    def __getattr__(self, name):
        if name.startswith("_"):
            return super().__getattr__(name)
        elif '__' in name:
            predicate = _parse_attr_name(name)
            return list(self.objects(subject=self.uri, predicate=predicate))
        else:
            return super().__getattr__(name)

    def __setattr__(self, name, value):
        if name.startswith("_"):
            super().__setattr__(name, value)
        elif '__' in name:
            predicate = _parse_attr_name(name)
            if not isinstance(value, (rdflib.URIRef, rdflib.Literal,
                                      rdflib.BNode, rdflib.Variable)):
                value = rdflib.Literal(value)
            if isinstance(value, (list, tuple)):
                self.remove((self.uri, predicate, None))
                for val_item in value:
                    self.add((self.uri, predicate, val_item))
            else:
                self.set((self.uri, predicate, value))
        else:
            super().__setattr__(name, value)

    def add_nif_classes(self):
        for cls in self.nif_classes:
            self.add((self.uri, rdflib.RDF.type, cls))
        return self


class NIFContext(NIFAnnotation):
    nif_classes = [nif_ns.Context, nif_ns.RFC5147String]

    def __init__(self, is_string, uri_prefix):
        super().__init__(is_string=is_string,
                         uri_prefix=uri_prefix)

    @staticmethod
    def is_context(cxt):
        classes = list(cxt.rdf__type)
        return nif_ns.Context in classes


class NIFStructure(NIFAnnotation):
    nif_classes = [nif_ns.Structure, nif_ns.RFC5147String]

    def __init__(self, reference_context, begin_end_index, anchor_of, **kwargs):
        super().__init__(
            reference_context=reference_context,
            begin_end_index=begin_end_index, anchor_of=anchor_of, **kwargs)


class NIFPhrase(NIFStructure):
    nif_classes = [nif_ns.Phrase, nif_ns.RFC5147String]

    def __init__(self, reference_context, begin_end_index, anchor_of, **kwargs):
        super().__init__(reference_context, begin_end_index, anchor_of,
                         **kwargs)


class NIFExtractedEntity(NIFPhrase):
    def __init__(self, reference_context, begin_end_index, anchor_of,
                 entity_uri, **kwargs):
        super().__init__(
            reference_context=reference_context,
            begin_end_index=begin_end_index, anchor_of=anchor_of,
            ta_ident_ref=rdflib.URIRef(entity_uri), **kwargs)


class NIFDocument:
    def __init__(self, text, uri="http://example.doc/"+str(uuid.uuid4())):
        self.uri_prefix = uri
        self.context = NIFContext(is_string=text,
                                  uri_prefix=uri)
        self.structures = []
        self.rdf = rdflib.Graph()
        self.rdf += self.context
        # super().__init__()

    def add_structure(self):
        # struct = NIFStructure()
        # self.structures.append(struct)
        # self.rdf += struct
        pass

    def add_phrase(self):
        pass

    def add_extracted_entity(self):
        self.add_phrase()

    def serialize(self, format="xml"):
        return self.rdf.serialize(format=format)

    @classmethod
    def parse(cls, rdf):
        out = cls('bla')
        out.rdf.parse(rdf)
        out.structures = []
        return out

    def extract_phrases(self, rdf):
        rdf_graph = rdflib.Graph.parse(rdf)
        for triple in rdf_graph[:rdflib.RDFS.type:nif_ns.Phrase]:
            phrase_uri = triple[0]
            phrase_triples = rdf_graph[phrase_uri::]

# a = NIFContext('bla')
# print(type(a))
# p = NIFPhrase()
# p.begin_index = 56