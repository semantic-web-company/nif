import re
import uuid
from typing import List

import rdflib

from nif.namespace import ns_dict

nif_ns = ns_dict['nif']


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
    nif_classes = (nif_ns.AnnotationUnit,)

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
    nif_classes = tuple()

    def __init__(self,
                 begin_end_index,
                 **kwargs):
        """
        The base abstract class.

        :param begin_end_index: tuple (begin_index, end_index). If `None` then
            begin_index = 0. see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e436
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
        self.__setattr__('nif__begin_index', begin_end_index[0], validate=False,
                         datatype=rdflib.XSD.nonNegativeInteger)
        self.__setattr__('nif__end_index', begin_end_index[1], validate=False,
                         datatype=rdflib.XSD.nonNegativeInteger)
        for key, val in kwargs.items():
            self.__setattr__(key, val)
        self.add_nif_classes()


class NIFOffsetBasedString(NIFString):
    nif_classes = tuple()

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
        assert uri_scheme in [nif_ns.ContextHashBasedString,
                              nif_ns.RFC5147String, nif_ns.CStringInst,
                              nif_ns.OffsetBasedString]
        self.nif_classes = list(self.nif_classes)
        self.nif_classes.append(uri_scheme)
        self.nif_classes = tuple(self.nif_classes)
        self.uri = do_suffix_offset(uri_prefix, *begin_end_index)
        super().__init__(begin_end_index, **kwargs)


class NIFAnnotation(NIFOffsetBasedString):
    nif_classes = (nif_ns.Annotation,)

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
        uri_prefix = reference_context.uri
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
    def from_triples(cls, rdf_graph, ref_cxt,
                     uri_scheme=nif_ns.OffsetBasedString):
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
                # pass
            else:
                other_triples.add((s, p, o))
        # kwargs['anchor_of'] = ref_cxt.nif__is_string[kwargs['begin_index']:kwargs['end_index']]
        kwargs['begin_end_index'] = kwargs['begin_index'], kwargs['end_index']
        del kwargs['begin_index']
        del kwargs['end_index']
        out = cls(reference_context=ref_cxt, **kwargs)
        out += other_triples
        return out


class NIFContext(NIFString):
    nif_classes = (nif_ns.Context, )

    def __init__(self, uri, is_string):
        """
        :param is_string: see http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core/nif-core.html#d4e669
        :param uri: the URI.
            :note: Only used if reference context is not given.
        """
        self.uri = rdflib.URIRef(uri)
        begin_end_index = (0, len(is_string))
        super().__init__(
            begin_end_index=begin_end_index)
        self.__setattr__('nif__is_string', is_string, False)

    def validate(self):
        return True

    @staticmethod
    def is_context(cxt):
        return isinstance(cxt, NIFContext)

    @classmethod
    def from_triples(cls, rdf_graph, context_uri,
                     ref_cxt=None,
                     uri_scheme=nif_ns.OffsetBasedString):
        kwargs = dict()
        other_triples = rdflib.Graph()
        for s, p, o in rdf_graph:
            if s != context_uri:
                other_triples.add((s, p, o))
            elif p == nif_ns.isString:
                if 'is_string' in kwargs:
                    raise ValueError('{} found twice. {}, {}'.format(p, kwargs, o.toPython()))
                kwargs['is_string'] = o.toPython()
                uri = s.toPython()
                assert str(uri) == str(context_uri)
            else:
                other_triples.add((s, p, o))

        out = cls(uri=context_uri, **kwargs)
        out += other_triples
        return out


class NIFExtractedEntity(NIFAnnotation):
    def __init__(self, reference_context, begin_end_index, anchor_of,
                 entity_uri, au_kwargs=None, **kwargs):
        if au_kwargs is not None:
            au = NIFAnnotationUnit(
                itsrdf__ta_ident_ref=rdflib.URIRef(entity_uri), **au_kwargs)
        else:
            au = NIFAnnotationUnit(
                itsrdf__ta_ident_ref=rdflib.URIRef(entity_uri))
        super().__init__(
            reference_context=reference_context,
            begin_end_index=begin_end_index, anchor_of=anchor_of,
            annotation_units=[au],
            **kwargs)


class NIFDocument:
    def __init__(self, context: NIFContext, annotations: List[NIFAnnotation] = None):
        if not NIFContext.is_context(context):
            raise TypeError('The provided context {} is not a NIFContext'
                            '.'.format(context))
        self.context = context
        self.uri_prefix = str(context.uri)
        self.annotations = []
        if annotations is not None:
            for ann in annotations:
                self.add_annotations([ann])
        self.validate()
        # self._rdf = None

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
        cxt = NIFContext(is_string=text, uri=uri)
        return cls(context=cxt, annotations=[])

    def add_annotations(self, anns: List[NIFAnnotation]):
        for ann in anns:
            self.annotations.append(ann)
        try:
            self.validate()
        except (ValueError, TypeError) as e:
            for _ in range(len(anns)):
                self.annotations.pop()
            raise e
        # else:
            # self.rdf += ann
        return self

    def add_extracted_entities(self, ees):
        self.add_annotations(ees)

    def add_extracted_cpts(self, cpt_dicts, au_kwargs=None, **kwargs):
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
                    ee = NIFExtractedEntity(
                        reference_context=self.context,
                        begin_end_index=(match[0], match[1]),
                        anchor_of=surface_form,
                        entity_uri=cpt_uri,
                        au_kwargs=au_kwargs,
                        **kwargs
                    )
                    ees.append(ee)
        self.add_extracted_entities(ees)
        return self

    @property
    def rdf(self):
        # if self._rdf is None:
        _rdf = self.context
        for ann in self.annotations:
            _rdf += ann
            for au in ann.annotation_units.values():
                _rdf += au
        # self._rdf = _rdf
        return _rdf

    def serialize(self, format="xml",
                  # uri_format=nif_ns.OffsetBasedString
                  **kwargs
                  ):
        rdf_text = self.rdf.serialize(format=format, **kwargs)
        return rdf_text

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

        annotations = []
        # struct_uris = list(rdf_graph[:nif_ns.referenceContext:context.uri])
        struct_uris = (set(rdf_graph[:nif_ns.referenceContext:context.uri]) &
                       set(rdf_graph[:rdflib.RDF.type:nif_ns.Annotation]))
        for i, struct_uri in enumerate(struct_uris):
            struct_triples = rdf_graph.triples((struct_uri, None, None))
            struct = NIFAnnotation.from_triples(struct_triples, ref_cxt=context)
            au_uris = list(rdf_graph[struct_uri:nif_ns.annotationUnit:])
            for au_uri in au_uris:
                au_dict = {p_uri: o_uri for p_uri, o_uri in rdf_graph[au_uri::]}
                au = NIFAnnotationUnit(uri=au_uri, **au_dict)
                struct.add_annotation_unit(au)
            annotations.append(struct)
        out = cls(context=context, annotations=annotations)

        for t in rdf_graph - out.rdf:
            # if t not in out.rdf:
            out.context.add(t)

        return out

    def __copy__(self):
        return NIFDocument.parse_rdf(self.serialize(format='n3'))

    def __eq__(self, other):
        return isinstance(other, NIFDocument) and \
               self.serialize(format='n3') == other.serialize(format='n3')


if __name__ == '__main__':
    import rdflib

    rdf_to_parse = '''
{
    "@context": "http://lynx-project.eu/doc/jsonld/lynxdocument.json",
    "@id": "d39a661a-9a9f-45a9-b651-c7d62b314714",
    "@type": [
        "nif:Context",
        "lkg:LynxDocument",
        "lkg:CaseLaw"
    ],
    "metadata": {
        "type_document": "Decision",
        "language": "de",
        "jurisdiction": "AT",
        "title": {
            "de": "Nichtigkeitsbeschwerde zur Wahrung des Gesetzes iSd § 23 StPO iZm vom Schöffengericht abweichende Verkündung des Urteils"
        },
        "hasAuthority": "OGH",
        "id_local": "JJT_20160314_OGH0002_0150OS00182_15A0000_000",
        "version_date": "2016-03-14",
        "url_consolidated": "http://www.ris.bka.gv.at/JustizEntscheidung.wxe?Abfrage=Justiz&Dokumentnummer=JJT_20160314_OGH0002_0150OS00182_15A0000_000&IncludeSelf=True",
        "sameAs": [
            {
                "@id": "https://lawthek.eu/detail/d39a661a-9a9f-45a9-b651-c7d62b314714/de/MULTI"
            }
        ]
    },
    "text": "Kopf Der Oberste Gerichtshof hat am 14. März 2016 durch den Senatspräsidenten des Obersten Gerichtshofs Prof. Dr. Danek als Vorsitzenden, den Hofrat des Obersten Gerichtshofs Mag. Lendl sowie die Hofrätinnen des Obersten Gerichtshofs Dr. Michel-Kwapinski, Mag. Fürnkranz und Dr. Mann als weitere Richter in Gegenwart der Rechtspraktikantin Mag. Fritsche als Schriftführerin in der Strafsache gegen Ersin C***** und andere Angeklagte wegen des Verbrechens des Suchtgifthandels nach § 28a Abs 1 fünfter Fall, Abs 4 Z 3 SMG und weiterer strafbarer Handlungen, AZ 44 Hv 190/14b des Landesgerichts für Strafsachen Wien, über die Nichtigkeitsbeschwerde der Staatsanwaltschaft gegen das Urteil dieses Gerichts vom 25. September 2015 (ON 190) und die von der Generalprokuratur gegen einen Vorgang in diesem Verfahren erhobene Nichtigkeitsbeschwerde zur Wahrung des Gesetzes nach öffentlicher Verhandlung in Anwesenheit des Vertreters der Generalprokuratur, Generalanwalt Dr. Eisenmenger, des Angeklagten und seines Verteidigers Mag. Vural zu Recht erkannt: Spruch Im Verfahren AZ 44 Hv 190/14b des Landesgerichts für Strafsachen Wien verletzt der Vorgang, dass der Vorsitzende bei der Verkündung des Urteils am 25. September 2015 dem Schuldspruch A./I./ einen Reinheitsgehalt des urteilsgegenständlichen Suchtgifts Heroin von 15,59 % (§ 28a Abs 4 Z 3 SMG) zugrunde legte (§ 260 Abs 1 Z 1 StPO), obwohl nach dem Beschluss des Schöffensenats ein geringerer, (bloß) die Qualifikation des § 28a Abs 2 Z 3 SMG begründender Reinheitsgehalt angenommen worden war, § 268 erster Satz StPO. Dieses Urteil, das im Übrigen unberührt bleibt, wird in der Unterstellung des Schuldspruchs A./I./ auch unter Abs 2 Z 3 und Abs 3 zweiter Fall des § 28a SMG, demzufolge auch in dem den Angeklagten Ersin C***** betreffenden Strafausspruch (einschließlich der Vorhaftanrechnung) aufgehoben und es wird die Sache im Umfang der Aufhebung zu neuer Verhandlung und Entscheidung an das Landesgericht für Strafsachen Wien verwiesen. Die Staatsanwaltschaft wird mit ihrer Nichtigkeitsbeschwerde auf diese Entscheidung verwiesen. Text Gründe: Im Verfahren AZ 44 Hv 190/14b des Landesgerichts für Strafsachen Wien legte die Staatsanwaltschaft Wien mit Anklageschrift vom 21. Dezember 2014 (ON 138) Ersin C***** als Verbrechen des Suchtgifthandels nach § 28a Abs 1 fünfter Fall, Abs 4 Z 3 SMG (A./I./) und Vergehen des unerlaubten Umgangs mit Suchtgiften nach § 27 Abs 1 Z 1 erster und zweiter Fall, Abs 2 SMG (D./) sowie Vladimir D***** (zu A.II./, B./) und Martin T***** (zu A.III./, B./) als Verbrechen des Suchtgifthandels nach § 28a Abs 1 fünfter Fall, Abs 2 Z 2, Abs 4 Z 3 SMG und der Vorbereitung von Suchtgifthandel nach § 28 Abs 1 zweiter Fall, Abs 3 SMG, D***** überdies als Vergehen des unerlaubten Umgangs mit Suchtgiften nach § 27 Abs 1 Z 1 zweiter Fall SMG (C./) beurteiltes Verhalten zur Last. Zufolge des Anklagevorwurfs zu A./I./ hat Ersin C***** von Mitte August 2013 bis 13. Oktober 2014 in W***** in zahlreichen Angriffen Mustafa G***** und Liliane M***** vorschriftswidrig Suchtgift in einer das Fünfundzwanzigfache der Grenzmenge (§ 28b SMG) übersteigenden Menge überlassen, und zwar 1.300 Gramm Heroin in einer Reinsubstanz von zumindest 15,59 % (ON 138). In der Hauptverhandlung am 25. September 2015 wurde der „wesentliche Akteninhalt“ (vgl aber RIS-Justiz RS0110681), „insbesondere das Untersuchungsergebnis des Bundeskriminalamts“ betreffend das beim Zeugen Richard K***** sichergestellte Heroin, wonach das Suchtgift einen Reinheitsgehalt von 10,44 % aufwies, gemäß § 252 Abs 2a StPO einverständlich vorgetragen (ON 189 S 12). Nach dem Schluss der Verhandlung zog sich der Schöffensenat zur Urteilsberatung zurück. Nach dem Wiedererscheinen des Senats verkündete der Vorsitzende das Urteil, wonach - soweit hier von Interesse - Ersin C***** (zu A./I./) im Zeitraum Mitte August 2013 bis 23. Oktober 2014 in W***** in zahlreichen Angriffen Mustafa G***** und Liliane M***** vorschriftswidrig Suchtgift in einer das 15-fache der Grenzmenge (§ 28b SMG) übersteigenden Menge, und zwar 600 Gramm Heroin in einer Reinsubstanz von zumindest 15,59 %, durch gewinnbringenden Verkauf überlassen habe (ON 189 S 13; § 260 Abs 1 Z 1 StPO). Er habe hiedurch zu A./I./ das Verbrechen des Suchtgifthandels nach § 28a Abs 1 fünfter Fall, Abs 2 Z 3 (gemeint auch: Abs 3 zweiter Fall) SMG begangen (§ 260 Abs 1 Z 2 StPO) und wurde hiefür zu einer (unbedingten) Freiheitsstrafe verurteilt (ON 189 S 15). Während der Angeklagte C***** - ebenso wie die beiden Mitangeklagten - Rechtsmittelverzicht erklärte, meldete die Staatsanwaltschaft (nur) zu diesem Angeklagten Nichtigkeitsbeschwerde an. In der schriftlichen Ausfertigung des Urteils (ON 190) stimmen Spruch und Gründe zu A./I./ (US 3 ff und 9) in den wesentlichen Punkten mit dem verkündeten Urteil überein. In der rechtlichen Beurteilung weist das Erstgericht darauf hin, dass auch beim Angeklagten Ersin C***** das 25-fache der Grenzmenge an Suchtgift überschritten und demnach die Privilegierung nach § 28a Abs 3 zweiter Fall SMG rechtsirrig angenommen worden sei (US 13 erster Absatz). In ihrer lediglich gegen den Schuldspruch A./I./ erhobenen, auf § 281 Abs 1 Z 10 StPO gestützten Nichtigkeitsbeschwerde (ON 205) führt die Anklagebehörde aus, dass bei der im Urteil festgestellten Suchtgiftmenge von 600 Gramm Heroin mit einem Reinheitsgehalt von 15,59 % die Grenzmenge um mehr als das 25-fache überschritten werde, sodass das inkriminierte Verbrechen richtigerweise nach § 28a Abs 4 Z 3 SMG zu qualifizieren und eine Privilegierung nach § 28a Abs 3 SMG daher ausgeschlossen sei. Am 6. November 2015 legte der Vorsitzende einen Amtsvermerk folgenden Inhalts an (bei ON 1): „Da das gegenständliche Urteil mündlich so verkündet wurde, wie nunmehr die schriftliche Urteilsausfertigung lautet, konnten keine Änderungen mehr vorgenommen werden - es blieb daher in allen Punkten beim ursprünglich angeklagten Reinheitsgrad von 15,59 %. In der Beratung mit den Schöffen ist natürlich von 'einem nicht mehr feststellbaren' Reinheitsgehalt ausgegangen worden. Alleine, wenn man die rund zehn Prozent (gemeint: Reinheitsgehalt) betrachtet, die beim Zeugen K***** sichergestellt wurden, kommt man bereits beim Faktum A./I./ bei 600 Gramm Suchtgift auf die 15-fache Menge. Zudem kommt, dass auch immer wieder die Rede von gestrecktem Suchtgift war, wenn dies auch einige Zeugen nicht bestätigten. Somit ergab sich für den Schöffensenat in der Beratung bloß die 15-fache Menge und zusätzlich auch die Privilegierung. In der mündlichen Urteilsverkündung wurde jedoch darauf vergessen, das Urteil konnte schriftlich nicht mehr anders ausgefertigt werden.“ Der Vorsitzende des aus einem Berufsrichter und zwei Schöffen zusammengesetzten Schöffensenats (§ 32 Abs 1 letzter Satz StPO) ist mit 31. Dezember 2015 in den Ruhestand getreten. Rechtliche Beurteilung Die Urteilsverkündung vom 25. September 2015 steht - wie die Generalprokuratur in ihrer zur Wahrung des Gesetzes erhobenen Nichtigkeitsbeschwerde zutreffend ausführt - hinsichtlich des Schuldspruchs A./I./ mit dem Gesetz nicht im Einklang. Gemäß § 257 erster Satz StPO hat sich das Schöffengericht nach Schluss der Verhandlung zur Urteilsfällung in das Beratungszimmer zurückzuziehen. Dort erfolgen demzufolge Beratung und Abstimmung (Lendl, WK-StPO § 257 Rz 4). Zu verkünden ist dann das in der Beratung beschlossene Urteil mit allen in § 260 Abs 1 Z 1 bis 5 und Abs 2 StPO genannten Punkten (Danek, WK-StPO § 268 Rz 1 und 7). Vorliegend gelangten die Tatrichter nach der Beratung - wovon der an den gegenteiligen Inhalt des Beratungsprotokolls nicht gebundene (vgl Ratz, WK-StPO § 281 Rz 312 und § 292 Rz 6) Oberste Gerichtshof aufgrund des Aktenvermerks des Vorsitzenden ausgeht - zum Ergebnis, der Reinheitsgehalt des zu A./I./ angenommenen Suchtgiftquantums von 600 Gramm Heroin betrage nicht 15,59 %, sondern nur etwa 10 %. Demnach wurde lediglich das Verbrechen des Suchtgifthandels nach § 28a Abs 1 fünfter Fall, Abs 2 Z 3 SMG als verwirklicht angesehen und dem Angeklagten die Privilegierung nach § 28a Abs 3 zweiter Fall SMG zugebilligt. Bei dem vom Vorsitzenden in der Verkündung (§ 260 Abs 1 Z 1 StPO) angenommenen Reinheitsgehalt von (zumindest) 15,59 % würden 600 Gramm Heroin allerdings eine Suchtgiftmenge darstellen, die das 25-fache der Grenzmenge (§ 28b SMG) überschreitet und daher die Qualifikation des § 28a Abs 4 Z 3 SMG begründet. Da im Schöffenverfahren jenes Urteil zu verkünden ist, welches nach Beratung vom Schöffensenat beschlossen wurde, bewirkte der bezeichnete Vorgang einen Verstoß gegen § 268 erster Satz StPO. Der Vorsitzende hat durch die Verkündung einer vom gefällten Urteil abweichenden Variante des Tatgeschehens eine ihm nicht zustehende Kompetenz in Anspruch genommen (vgl RIS-Justiz RS0116267). Die Gesetzesverletzung war festzustellen. Es ist nicht auszuschließen, dass der Vorgang der verfehlten Verkündung eines die rechtliche Unterstellung der Taten (auch) nach Abs 2 Z 3 Abs 3 zweiter Fall des § 28a SMG nicht tragenden Reinheitsgehalts von 15,59 % dem Angeklagten zum Nachteil gereicht, weil die Staatsanwaltschaft das Urteil angefochten und auf Basis der vom Vorsitzenden aus seinem Fehler abgeleiteten (demnach ebenso nicht der Beschlussfassung des Schöffengerichts entsprechenden) Urteilsfeststellungen die Bestrafung des Angeklagten nach § 28a Abs 4 Z 3 SMG begehrt hat. Der Oberste Gerichtshof sah sich zur Anordnung konkreter Wirkung veranlasst (§ 292 letzter Satz StPO). In einem solchen Fall wäre es grundsätzlich ausreichend, das verkündete Urteil (im entsprechenden Umfang) zur Klarstellung zu beseitigen und - ohne Anordnung einer neuen Hauptverhandlung - dem Erstgericht aufzutragen, das tatsächlich beschlossene Urteil neu zu verkünden (vgl Danek, WK-StPO § 268 Rz 10). Bei dieser neuen Urteilsverkündung müssten alle Mitglieder des - (zumal ein Fall des § 43 Abs 2 letzter Satzteil StPO nicht vorliegt:) seinerzeitigen - Schöffensenats anwesend sein (Danek, WK-StPO § 268 Rz 3). Diesem Erfordernis steht jedoch der inzwischen angetretene Ruhestand des Vorsitzenden entgegen. Die Kaiserliche Verordnung vom 14. Dezember 1915, RGBl 1915/372, eignet sich nicht zur Behebung der vorliegenden Problemstellung, weil sie nicht die Verkündung, sondern nur die schriftliche Ausfertigung des Urteils betrifft (vgl Danek, WK-StPO § 270 Rz 3). Demgemäß waren die Unterstellung der dem Schuldspruch A./I./ zugrunde liegenden Taten auch unter Abs 2 Z 3 und Abs 3 zweiter Fall des § 28a SMG und der Strafausspruch über den Angeklagten C***** aufzuheben und es war in diesem Umfang die neue Verhandlung (vor einem neuen Spruchkörper) und Entscheidung anzuordnen. Bleibt anzumerken, dass sich selbst unter der Prämisse, die Divergenz zwischen beschlossenem und verkündetem Urteil beziehe sich auch auf den Zweit- und den Drittangeklagten (vgl Amtsvermerk erster Absatz: „in allen Punkten“), hinsichtlich dieser kein Bedarf für eine Maßnahme gemäß § 290 Abs 1 StPO ergibt, weil auch bei Annahme eines Reinheitsgehalts von etwa 10 % des von ihnen verhandelten Suchtgifts die Qualifikation des § 28a Abs 4 Z 3 SMG erfüllt wäre und sich sohin am Schuldspruch nichts ändern würde. Die Staatsanwaltschaft war mit ihrer Nichtigkeitsbeschwerde auf diese Entscheidung zu verweisen.",
    "offset_ini": 0,
    "offset_end": 11291
}
    '''

    g = rdflib.Graph().parse(data=rdf_to_parse, format='json-ld')
    n = NIFDocument.parse_rdf(g.serialize(format='n3'), format='n3')
    print(n)
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

    # nifDocument = rdf_to_parse
    # d = NIFDocument.parse_rdf(nifDocument, format='turtle')
    # ann = NIFAnnotation(begin_end_index=(0, len(d.context.nif__is_string)))
    # ann.nif__summary = "<your summary here>"
    # d.add_annotations([ann])


