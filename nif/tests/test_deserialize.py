import json

import pytest
from pyld import jsonld

from nif.annotation import SWCNIFMatchedResourceOccurrenceSchema, SWCNIFMatchedResourceOccurrence, NIFAnnotationUnit, \
    NIFDocument, NIFContext, NIFContextSchema, SWCNIFNamedEntityOccurrence, SWCNIFNamedEntityOccurrenceSchema


@pytest.fixture
def flattened_jsonld_data_matched_resource_entity_A():
    return {
        "@context": {
            "nif": "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#"
        },
        "@graph": [

            {
                "@id": "file:///some/file/path#offset_0_91",
                "@type": [
                    "nif:Context"
                ],
                "https://semantic-web.com/research/nif#annotations": [
                    {
                        "@id": "file:///some/file/path#offset_70_78"
                    }
                ],
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "0"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "91"
                },
                "nif:isString": "This is the title of the document\n\nAnd here we have a sentence with Entity A and Entity B"
            },

            {
                "@id": "file:///some/file/path#offset_70_78",
                "@type": [
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#OffsetBasedString",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Phrase",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#String",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Structure",
                    "https://semantic-web.com/research/nif#MatchedResourceOccurrence"
                ],
                "nif:anchorOf": "Entity A",
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "70"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "78"
                },
                "nif:referenceContext": "file:///some/file/path#offset_0_91",
                "nif:annotationUnit": {
                    "@id": "_:N4dd8cfc53f52477fb2d726eda6571a7a"
                }
            },
            {
                "@id": "_:N4dd8cfc53f52477fb2d726eda6571a7a",
                "@type": ["nif:AnnotationUnit", "nif:Annotation"],
                "http://www.w3.org/2005/11/its/rdf#taAnnotatorRef": "http://obaris.org/ns/service/ne-roles-service",
                "http://www.w3.org/2005/11/its/rdf#taClassRef": "https://w3id.org/obaris/ns/permit#ConceptAnnotation",
                "http://www.w3.org/2005/11/its/rdf#taIdentRef": "https://custom-apps.poolparty.biz/OBARIStest/9"
            }

        ]
    }

@pytest.fixture
def mixed_nested_jsonld_data_matched_resource_entity_A():
    return {
        "@context": {
            "nif": "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#"
        },
        "@graph": [

            {
                "@id": "file:///some/file/path#offset_0_91",
                "@type": [
                    "nif:Context"
                ],
                "https://semantic-web.com/research/nif#annotations": [
                    {
                        "@id": "file:///some/file/path#offset_70_78"
                    }
                ],
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "0"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "91"
                },
                "nif:isString": "This is the title of the document\n\nAnd here we have a sentence with Entity A and Entity B"
            },

            {
                "@id": "file:///some/file/path#offset_70_78",
                "@type": [
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#OffsetBasedString",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Phrase",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#String",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Structure",
                    "https://semantic-web.com/research/nif#MatchedResourceOccurrence"
                ],
                "nif:anchorOf": "Entity A",
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "70"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "78"
                },
                "nif:referenceContext": "file:///some/file/path#offset_0_91",
                "nif:annotationUnit": {
                    "@id" : "_:N4dd8cfc53f52477fb2d726eda6571a7a",
                    "@type": ["nif:AnnotationUnit", "nif:Annotation"],
                    "http://www.w3.org/2005/11/its/rdf#taAnnotatorRef": "http://obaris.org/ns/service/ne-roles-service",
                    "http://www.w3.org/2005/11/its/rdf#taClassRef": "https://w3id.org/obaris/ns/permit#ConceptAnnotation",
                    "http://www.w3.org/2005/11/its/rdf#taIdentRef": "https://custom-apps.poolparty.biz/OBARIStest/9"
                }
            }
        ]
    }

@pytest.fixture
def nested_jsonld_data_matched_resource_entity_A():
    return {
        "@context": {
            "nif": "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#"
        },
        "@graph": [

            {
                "@id": "file:///some/file/path#offset_0_91",
                "@type": [
                    "nif:Context"
                ],
                "https://semantic-web.com/research/nif#annotations": [
                    {
                        "@id": "file:///some/file/path#offset_70_78",
                        "@type": [
                            "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#OffsetBasedString",
                            "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Phrase",
                            "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#String",
                            "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Structure",
                            "https://semantic-web.com/research/nif#MatchedResourceOccurrence"
                        ],
                        "nif:anchorOf": "Entity A",
                        "nif:beginIndex": {
                            "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                            "@value": "70"
                        },
                        "nif:endIndex": {
                            "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                            "@value": "78"
                        },
                        "nif:referenceContext": "file:///some/file/path#offset_0_91",
                        "nif:annotationUnit": {
                            "@type": ["nif:AnnotationUnit", "nif:Annotation"],
                            "http://www.w3.org/2005/11/its/rdf#taAnnotatorRef": "http://obaris.org/ns/service/ne-roles-service",
                            "http://www.w3.org/2005/11/its/rdf#taClassRef": "https://w3id.org/obaris/ns/permit#ConceptAnnotation",
                            "http://www.w3.org/2005/11/its/rdf#taIdentRef": "https://custom-apps.poolparty.biz/OBARIStest/9"
                        }
                    }
                ],
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "0"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "91"
                },
                "nif:isString": "This is the title of the document\n\nAnd here we have a sentence with Entity A and Entity B"
            }
        ]
    }

@pytest.fixture
def flattened_jsonld_data_ne_and_matched_resource():
    return {
        "@context": {
            "nif": "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#"
        },
        "@graph": [

            {
                "@id": "file:///some/file/path#offset_0_91",
                "@type": [
                    "nif:Context"
                ],
                "https://semantic-web.com/research/nif#annotations": [
                    {
                        "@id": "file:///some/file/path#offset_70_78"
                    }
                ],
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "0"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "91"
                },
                "nif:isString": "This is the title of the document\n\nAnd here we have a sentence with Entity A and Entity B"
            },

            {
                "@id": "file:///some/file/path#offset_70_78",
                "@type": [
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#OffsetBasedString",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Phrase",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#String",
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#Structure",
                    "https://semantic-web.com/research/nif#MatchedResourceOccurrence",
                    "https://semantic-web.com/research/nif#NamedEntityOccurrence"

                ],
                "nif:anchorOf": "Entity A",
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "70"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "78"
                },
                "nif:referenceContext": "file:///some/file/path#offset_0_91",
                "nif:annotationUnit": {
                    "@id": "_:N4dd8cfc53f52477fb2d726eda6571a7a"
                }
            },
            {
                "@id": "_:N4dd8cfc53f52477fb2d726eda6571a7a",
                "@type": ["nif:AnnotationUnit", "nif:Annotation"],
                "http://www.w3.org/2005/11/its/rdf#taAnnotatorRef": "http://obaris.org/ns/service/ne-roles-service",
                "http://www.w3.org/2005/11/its/rdf#taClassRef": "https://w3id.org/obaris/ns/permit#ConceptAnnotation",
                "http://www.w3.org/2005/11/its/rdf#taIdentRef": "https://custom-apps.poolparty.biz/OBARIStest/9"
            }

        ]
    }

@pytest.fixture
def flattened_jsonld_data_only_child_types_matched_resource_entity_A():
    return {
        "@context": {
            "nif": "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#"
        },
        "@graph": [

            {
                "@id": "file:///some/file/path#offset_0_91",
                "@type": [
                    "nif:Context"
                ],
                "https://semantic-web.com/research/nif#annotations": [
                    {
                        "@id": "file:///some/file/path#offset_70_78"
                    }
                ],
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "0"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "91"
                },
                "nif:isString": "This is the title of the document\n\nAnd here we have a sentence with Entity A and Entity B"
            },

            {
                "@id": "file:///some/file/path#offset_70_78",
                "@type": [
                    "http://persistence.uni-leipzig.org/nlp2rdf/ontologies/nif-core#OffsetBasedString",
                    "https://semantic-web.com/research/nif#MatchedResourceOccurrence"
                    #"https://semantic-web.com/research/nif#NamedEntityOccurrence"

                ],
                "nif:anchorOf": "Entity A",
                "nif:beginIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "70"
                },
                "nif:endIndex": {
                    "@type": "http://www.w3.org/2001/XMLSchema#nonNegativeInteger",
                    "@value": "78"
                },
                "nif:referenceContext": "file:///some/file/path#offset_0_91",
                "nif:annotationUnit": {
                    "@id": "_:N4dd8cfc53f52477fb2d726eda6571a7a"
                }
            },
            {
                "@id": "_:N4dd8cfc53f52477fb2d726eda6571a7a",
                "@type": ["nif:AnnotationUnit"],
                "http://www.w3.org/2005/11/its/rdf#taAnnotatorRef": "http://obaris.org/ns/service/ne-roles-service",
                "http://www.w3.org/2005/11/its/rdf#taClassRef": "https://w3id.org/obaris/ns/permit#ConceptAnnotation",
                "http://www.w3.org/2005/11/its/rdf#taIdentRef": "https://custom-apps.poolparty.biz/OBARIStest/9"
            }

        ]
    }

@pytest.fixture
def matched_resource_A_data():
    au = NIFAnnotationUnit(annotator_ref='http://obaris.org/ns/service/ne-roles-service',
                                class_ref='https://w3id.org/obaris/ns/permit#ConceptAnnotation',
                                confidence=None,
                                ident_ref='https://custom-apps.poolparty.biz/OBARIStest/9',
                                prop_ref=None,
                                uri='_:N4dd8cfc53f52477fb2d726eda6571a7a')
    obj =  SWCNIFMatchedResourceOccurrence(anchor_of="Entity A",
                                               begin_index=70,
                                               end_index=78,
                                               reference_context_uri='file:///some/file/path#offset_0_91',
                                               sentence_uri=None,
                                               words_uris=None,
                                               annotation_units=[au])
    obj.uri = 'file:///some/file/path#offset_70_78'

    return  {SWCNIFMatchedResourceOccurrenceSchema : obj}

@pytest.fixture
def named_entity_A_data():
    au = NIFAnnotationUnit(annotator_ref='http://obaris.org/ns/service/ne-roles-service',
                           class_ref='https://w3id.org/obaris/ns/permit#ConceptAnnotation',
                           confidence=None,
                           ident_ref='https://custom-apps.poolparty.biz/OBARIStest/9',
                           prop_ref=None,
                           uri='_:N4dd8cfc53f52477fb2d726eda6571a7a')
    obj =  SWCNIFNamedEntityOccurrence(anchor_of="Entity A",
                                           begin_index=70,
                                           end_index=78,
                                           reference_context_uri='file:///some/file/path#offset_0_91',
                                           sentence_uri=None,
                                           words_uris=None,
                                           annotation_units=[au])
    obj.uri = 'file:///some/file/path#offset_70_78'
    return {SWCNIFNamedEntityOccurrenceSchema : obj}

@pytest.fixture
def entity_A_all_types_data():
    d = {}
    au = NIFAnnotationUnit(annotator_ref='http://obaris.org/ns/service/ne-roles-service',
                           class_ref='https://w3id.org/obaris/ns/permit#ConceptAnnotation',
                           confidence=None,
                           ident_ref='https://custom-apps.poolparty.biz/OBARIStest/9',
                           prop_ref=None,
                           uri='_:N4dd8cfc53f52477fb2d726eda6571a7a')
    obj =  SWCNIFMatchedResourceOccurrence(anchor_of="Entity A",
                                           begin_index=70,
                                           end_index=78,
                                           reference_context_uri='file:///some/file/path#offset_0_91',
                                           sentence_uri=None,
                                           words_uris=None,
                                           annotation_units=[au])
    obj.uri = 'file:///some/file/path#offset_70_78'
    d[SWCNIFMatchedResourceOccurrenceSchema] =  obj

    au = NIFAnnotationUnit(annotator_ref='http://obaris.org/ns/service/ne-roles-service',
                           class_ref='https://w3id.org/obaris/ns/permit#ConceptAnnotation',
                           confidence=None,
                           ident_ref='https://custom-apps.poolparty.biz/OBARIStest/9',
                           prop_ref=None,
                           uri='_:N4dd8cfc53f52477fb2d726eda6571a7a')
    obj =  SWCNIFNamedEntityOccurrence(anchor_of="Entity A",
                                       begin_index=70,
                                       end_index=78,
                                       reference_context_uri='file:///some/file/path#offset_0_91',
                                       sentence_uri=None,
                                       words_uris=None,
                                       annotation_units=[au])
    obj.uri = 'file:///some/file/path#offset_70_78'
    d[SWCNIFNamedEntityOccurrenceSchema] =  obj

    return d

@pytest.fixture
def context_data():
    obj = NIFContext(uri="file:///some/file/path#offset_0_91",
               is_string="This is the title of the document\n\nAnd here we have a sentence with Entity A and Entity B")
    return obj


@pytest.mark.parametrize("input_jsonld, true_obj, true_context",
                         [("flattened_jsonld_data_matched_resource_entity_A", "matched_resource_A_data", "context_data"),
                          ("flattened_jsonld_data_only_child_types_matched_resource_entity_A", "matched_resource_A_data", "context_data"),
                          ("mixed_nested_jsonld_data_matched_resource_entity_A", "matched_resource_A_data", "context_data"),
                          #("nested_jsonld_data_matched_resource_entity_A", "entity_A_data", "context_data") --> not supported yet,
                          # would require the modelling of "annotations" containing elements from different schemas
                          ]
                         )
def test_deserialize_flatted_and_nested_format(input_jsonld, true_obj, true_context, request):
    true_obj = request.getfixturevalue(true_obj)
    d = {}
    d.update(named_entity_A_data())
    d.update(matched_resource_A_data())
    true_context = request.getfixturevalue(true_context)
    true_nif_doc = NIFDocument()
    for schema, obj in true_obj.items():
        true_nif_doc.append_element("phrases", obj, schema)
    true_nif_doc.append_element("context", true_context, NIFContextSchema )

    input_jsonld = request.getfixturevalue(input_jsonld)
    nif_doc = NIFDocument.from_json(input_jsonld)

    assert (nif_doc == true_nif_doc)

@pytest.mark.parametrize("input_jsonld, true_context",
                         [("flattened_jsonld_data_matched_resource_entity_A", "context_data")])
def test_deserialize_unknown_data(input_jsonld, true_context, request):
    true_context = request.getfixturevalue(true_context)
    true_nif_doc = NIFDocument()
    true_nif_doc.append_element("context", true_context, NIFContextSchema)

    input_jsonld = request.getfixturevalue(input_jsonld)
    nif_doc = NIFDocument.from_json(input_jsonld)

    #"annotation" are not yet modelled in ContextScheme, therefore it is considered unknown data
    assert(hasattr(nif_doc.elements._context[true_context.uri][0], "https://semantic-web"))
    assert("com/research/nif#annotations" in getattr(nif_doc.elements._context[true_context.uri][0],"https://semantic-web"))


@pytest.mark.parametrize("input_jsonld, true_annotations, true_context",
                         [("flattened_jsonld_data_ne_and_matched_resource", "entity_A_all_types_data", "context_data")])
def test_deserialize_overlapping_aus(input_jsonld, true_annotations, true_context, request):
    true_annotations = request.getfixturevalue(true_annotations)
    true_context = request.getfixturevalue(true_context)
    true_nif_doc = NIFDocument()
    true_nif_doc.append_element("context", true_context, NIFContextSchema)
    for schema, obj in true_annotations.items():
        true_nif_doc.append_element("phrases", obj, schema)

    input_jsonld = request.getfixturevalue(input_jsonld)
    nif_doc = NIFDocument.from_json(input_jsonld)

    assert (nif_doc == true_nif_doc)