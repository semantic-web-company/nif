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
itsrdf_ns = rdflib.Namespace('http://www.w3.org/2005/11/its/rdf#')
eli_ns = rdflib.Namespace('http://data.europa.eu/eli/ontology#')
lynx_ns = rdflib.Namespace('http://lkg.lynx-project.eu/def/')
ns_dict = {'nif': nif_ns,
           'itsrdf': itsrdf_ns,
           'rdf': rdflib.RDF,
           'rdfs': rdflib.RDFS,
           'owl': rdflib.OWL,
           'lkg': lynx_ns,
           'skos': rdflib.namespace.SKOS,
           # 'dct': rdflib.namespace.DCTERMS,
           'eli': eli_ns}