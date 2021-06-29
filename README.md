# NIF annotation package

A package to help using [NIF](https://github.com/NLP2RDF/ontologies/blob/master/nif-core/nif-core.ttl) in Python.


## Example

### Create a `NIFDocument`.

```python
from nif.annotation import NIFDocument, SWCNIFNamedEntityOccurrence, SWCNIFChunk

cxt_str = "Christian mentioned tiger shark hunting"
i = 0
words_data = []
for w_str in cxt_str.split(' '):
    be = (i, i+len(w_str))
    words_data.append(be)
    i += len(w_str) + 1
sents_data = [(0, len(words_data)-1)]
nif_doc = NIFDocument.from_data(cxt_str=cxt_str,
                                words_data=words_data,
                                sents_data=sents_data)
# Named Entity
christian = SWCNIFNamedEntityOccurrence(
    begin_end_index=(0, 9),
    anchor_of='Christian',
    reference_context=nif_doc.context,
    class_uri="http://dbpedia.org/resource/classes#Person"
)
nif_doc.phrases += christian
# Noun Phrase
np = SWCNIFChunk(
    begin_end_index=(20, 39),
    reference_context=nif_doc.context,
    chunk_type='NP',
    anchor_of='tiger shark hunting',
)
nif_doc.phrases += np
```

### Create from triples.

```python
from pathlib import Path
from nif.annotation import NIFDocument, SWCNIFNamedEntityOccurrence, SWCNIFChunk

file_path = Path('./nif/example/words.ttl')
nif_doc = NIFDocument.parse_rdf(file_path.read_text())
```

## Tests

To run tests do:
``` bash
> cd nif
> nosetests tests/
```
