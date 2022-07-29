import copy
from collections import defaultdict


def _merge_dicts(obj1: dict, obj2 :dict, value_strategy="refuse", list_strategy="merge"):
    """
    merges the content of two dictionaries
    :param obj1: first dictionary to be merged
    :param obj2: second dictionary to be merged
    :param value_strategy: how to deal with values occurring in both dicts, 'refuse' will trow an exception,
    if the values of the same key are different in the two dicts (except for lists), default: 'refuse'
    :param list_strategy: how to deal with list values, 'merge' will only add new entries, default: 'merge'
    :return: the merged dictionary
    """
    merged_obj = copy.deepcopy(obj1)
    for k,v in obj2.items():
        if k in merged_obj.keys():
            if isinstance(v, list) and isinstance(merged_obj[k], list) and list_strategy=="merge":
                merged_obj[k] += [x for x in v if x not in merged_obj[k]]
            elif isinstance(v, list) and list_strategy=="merge":
                if merged_obj[k] not in v:
                    merged_obj[k] = [merged_obj[k]] + v
            elif isinstance(merged_obj[k], list) and list_strategy=="merge":
                if v not in merged_obj[k]:
                    merged_obj[k].append(v)
            elif v == merged_obj[k]:
                pass
            elif value_strategy=="refuse":
                raise ValueError(f"Refused to merge objects, key {k} leads to different values {obj1[k]} and {obj2[k]}")
        else:
            merged_obj[k] = v
        if isinstance(merged_obj[k], list):
            merged_obj[k] = sorted(merged_obj[k])
    return merged_obj

def _find_all_values(d, key, _found_objs=None, _current_key=""):
    """
    in an nested dictionary 'd', find all values with the key 'key'
    :param d: dictionary to search through
    :param key: key for which the values should be found
    :param _found_objs: list of tuples (value, blank_separated_key_path)
    :param _current_key:
    :return: list of tuples (value, blank_separated_key_path)
    """
    if _found_objs is None:
        _found_objs = []
    if key in d:
        _found_objs.append((d[key],_current_key))
    for k, v in d.items():
        if isinstance(v,list):
            for e in v:
                if isinstance(e, dict):
                    _find_all_values(e, key, _found_objs, _current_key+" "+k)
        elif isinstance(v, dict):
            _find_all_values(v, key, _found_objs,_current_key+" "+k)
    return _found_objs

def _get_all_nested_ids(start_obj, all_obj, nested_ids=None, no_obj_ids=None):
    """

    :param start_obj:
    :param all_obj:
    :param nested_ids:
    :param no_obj_ids:
    :return: nested_ids: list of ids that contain nested elements,
    no_obj_ids: dictionary of id_with_nested_elements : (id_of_nested_element, [predicates_of_nested_element])
    """
    if nested_ids is None:
        nested_ids = []
    if no_obj_ids is None:
        no_obj_ids = defaultdict(list)
    ids = _find_all_values(start_obj, '@id')
    nested_ids.append(ids[0][0])
    for i, keys in ids[1:]:
        if i not in all_obj:
            no_obj_ids[ids[0][0]].append((i,keys.split()))
        else:
            _get_all_nested_ids(all_obj[i], all_obj, nested_ids, no_obj_ids)
    return nested_ids, no_obj_ids

def _flatten_references_to_external_resources(json_obj, all_objs):
    nested_obj_ids, nested_objs = _get_all_nested_ids(json_obj, all_objs)
    # attempt to flatten references to external sources,
    # i.e. some:uri : {@id : "external:source"} --> some:uri : "external:source"
    for parent_obj_id, nested_tuple in nested_objs.items():
        parent_obj = all_objs[parent_obj_id]
        for obj_id, predicate_list in nested_tuple:
            potential_external_ref = parent_obj
            obj_w_external_ref = None
            predicate = None
            for predicate in predicate_list:
                obj_w_external_ref = potential_external_ref
                potential_external_ref = potential_external_ref[predicate]
            if predicate is None:
                raise RuntimeError(f"no predicate for potential external predicate {parent_obj_id}, {obj_id}")
            #todo this is not fiexed yet
            if len(potential_external_ref[0]) == 1:
                obj_w_external_ref[predicate] = obj_id
            else:
                pass
    return json_obj, all_objs, nested_obj_ids


def _get_schemas(json_obj, exclude_parents):
    from nif.annotation import swcnif_ns, SWCNIFNamedEntityOccurrenceSchema, SWCNIFChunkSchema, NIFSentenceSchema, \
        NIFWordSchema, NIFPhraseSchema, NIFContextSchema,SWCNIFMatchedResourceOccurrenceSchema, NIFAnnotationUnitSchema, \
        NIFAnnotationSchema, nif_ns
    obj_types = json_obj["@type"]
    schemas = []
    if swcnif_ns.NamedEntityOccurrence in obj_types or swcnif_ns.NamedEntity in obj_types:
        schemas.append(SWCNIFNamedEntityOccurrenceSchema)
    if swcnif_ns.MatchedResourceOccurrence in obj_types or swcnif_ns.ExtractedEntity in obj_types:
        schemas.append(SWCNIFMatchedResourceOccurrenceSchema)
    if swcnif_ns.Chunk in obj_types:
        schemas.append(SWCNIFChunkSchema)
    if nif_ns.Context in obj_types:
        schemas.append(NIFContextSchema)

    if nif_ns.AnnotationUnit in obj_types:
        schemas.append(NIFAnnotationUnitSchema)


    if not schemas or not exclude_parents:
        if nif_ns.Phrase in obj_types:
            schemas.append(NIFPhraseSchema)
        if nif_ns.Sentence in obj_types:
            schemas.append(NIFSentenceSchema)
        if nif_ns.Word in obj_types:
            schemas.append(NIFWordSchema)

        if nif_ns.Annotation in obj_types:
            schemas.append(NIFAnnotationSchema)

    return schemas



