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
                 begin_end_index, is_string=None,
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
        try:
            begin_end_index = tuple(map(int, begin_end_index))
        except ValueError:
            raise ValueError(
                'begin_end_index should be convertible to integers, '
                '{} provided'.format(begin_end_index))
        self.reference_context = None  # this holds a separate graph
        if reference_context is not None:  # this is a not a context
            uri_prefix = reference_context.uri_prefix
            self.reference_context = reference_context
        self.uri = do_suffix_rfc5147(uri_prefix, *begin_end_index)
        # URI obtained, set the predicate, object pairs
        self.__setattr__('nif__begin_index', begin_end_index[0], validate=False)
        self.__setattr__('nif__end_index', begin_end_index[1], validate=False)
        if reference_context is not None:
            self.__setattr__('nif__reference_context', reference_context.uri,
                             False)
        if is_string is not None:
            self.__setattr__('nif__is_string', is_string, False)
        if ta_ident_ref is not None:
            self.__setattr__('itsrdf__ta_ident_ref', ta_ident_ref, False)
        if anchor_of is not None:
            self.__setattr__('nif__anchor_of', anchor_of, False)
        self.add_nif_classes()
        self.validate()
        for key, val in kwargs.items():
            self.__setattr__(key, val)

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
            if self.nif__anchor_of is not None or \
                    self.nif__reference_context is not None or \
                    self.itsrdf__ta_ident_ref is not None:
                raise ValueError(
                    'If is_string is provided then '
                    'ta_ident_ref, reference_context and anchor are not allowed'
                    '. You have reference context = {}, anchor = {}, '
                    'ta_ident_ref = {}.'.format(self.nif__reference_context,
                                                self.nif__anchor_of,
                                                self.itsrdf__ta_ident_ref))
        if self.itsrdf__ta_ident_ref is not None:
            if self.nif__is_string is not None or \
                    self.nif__reference_context is None or \
                    self.nif__anchor_of is None:
                raise ValueError(
                    'If identifier ta_iden_ref is provided then '
                    'reference context and anchor are required and'
                    'is_string is not allowed. You have'
                    'reference context = {}, anchor = {}, is_string = {}'
                    '.'.format(self.nif__reference_context,
                               self.nif__anchor_of, self.nif__is_string))
        if self.nif__reference_context is not None:
            if self.nif__anchor_of is None:
                raise ValueError('When reference context is provided, '
                                 'anchor_of is required.')

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

    def __setattr__(self, name, value, validate=True):
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
            if validate:
                self.validate()
        else:
            super().__setattr__(name, value)

    def add_nif_classes(self):
        for cls in self.nif_classes:
            self.add((self.uri, rdflib.RDF.type, cls))
        return self


class NIFContext(NIFAnnotation):
    nif_classes = [nif_ns.Context, nif_ns.RFC5147String]

    def __init__(self, is_string, uri_prefix):
        begin_end_index = (0, len(is_string))
        super().__init__(
            begin_end_index=begin_end_index,
            is_string=is_string,
            uri_prefix=uri_prefix)
        self.uri_prefix = uri_prefix

    @staticmethod
    def is_context(cxt):
        return isinstance(cxt, NIFContext)


class NIFStructure(NIFAnnotation):
    nif_classes = [nif_ns.Structure, nif_ns.RFC5147String]

    def __init__(self, reference_context, begin_end_index, anchor_of, **kwargs):
        super().__init__(
            reference_context=reference_context,
            begin_end_index=begin_end_index, anchor_of=anchor_of,
            **kwargs)

    def validate(self):
        super().validate()
        if self.nif__anchor_of is not None:
            ref_substring = self.reference_context.nif__is_string[
                            int(self.nif__begin_index):int(self.nif__end_index)]
            if self.nif__anchor_of.toPython() != ref_substring:
                raise ValueError(
                    'Anchor should be equal exactly to the subtring of '
                    'the reference context. You have anchor = "{}", ' \
                    'substring in ref context = "{}"'.format(
                    self.nif__anchor_of, ref_substring))

    @staticmethod
    def is_structure(struct):
        return isinstance(struct, NIFStructure)


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
    def __init__(self, context, structures):
        if not NIFContext.is_context(context):
            raise TypeError('The provided context {} is not a NIFContext'
                            '.'.format(context))
        self.context = context
        self.uri_prefix = context.uri_prefix
        self.structures = structures
        self.rdf = rdflib.Graph()
        self.rdf += self.context
        self.validate()

    def validate(self):
        for struct in self.structures:
            if not NIFStructure.is_structure(struct):
                raise TypeError('The provided structure {} is not a '
                                'NIFStructure.'.format(struct))
            if struct.nif__reference_context != self.context.uri:
                raise ValueError('The reference context {} for the structure {} '
                                 'is different from the context {} of the '
                                 'document.'.format(
                                     struct.nif__reference_context,
                                     struct.uri, self.context.uri))

    @classmethod
    def from_text(cls, text, uri="http://example.doc/"+str(uuid.uuid4())):
        cxt = NIFContext(is_string=text, uri_prefix=uri)
        return cls(context=cxt, structures=[])

    def add_structure(self, struct):
        self.structures.append(struct)
        try:
            self.validate()
        except (ValueError, TypeError) as e:
            self.structures.pop()
            raise e
        else:
            self.rdf += struct
        return self

    def add_phrase(self, phrase):
        self.add_structure(phrase)

    def add_extracted_entity(self, ee):
        self.add_phrase(ee)

    def add_extracted_cpt(self, cpt_dict):
        """
        :param cpt_dict: expected to have 'uri',
            'matchings'-> [{'matchedText': value,
                            'positions': [(begin, end), ...]},
                           ...]
        :return: self
        """
        cpt_uri = cpt_dict['uri']
        for matches in cpt_dict['matchings']:
            surface_form = matches['matchedText']
            for match in matches['positions']:
                ee = NIFExtractedEntity(
                    reference_context=self.context,
                    begin_end_index=match,
                    anchor_of=surface_form,
                    entity_uri=cpt_uri
                )
                self.add_extracted_entity(ee)
        return self

    def serialize(self, format="xml"):
        return self.rdf.serialize(format=format)

    @classmethod
    def parse(cls, rdf):
        # TODO
        context = NIFDocument.extract_context(rdf)
        phrases = NIFDocument.extract_phrases(rdf)
        out = cls(context=context, structures=phrases)
        return out

    @staticmethod
    def extract_phrases(rdf):
        # TODO
        rdf_graph = rdflib.Graph.parse(rdf)
        for phrase_uri in rdf_graph[:rdflib.RDFS.type:nif_ns.Phrase]:
            phrase_triples = rdf_graph[phrase_uri::]

    @staticmethod
    def extract_context(rdf):
        # TODO
        rdf_graph = rdflib.Graph.parse(rdf)
        for context_uri in rdf_graph[:rdflib.RDFS.type:nif_ns.Context]:
            context_triples = rdf_graph[context_uri::]
