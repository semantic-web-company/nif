# NIF annotation package

A package to help using [NIF](https://github.com/NLP2RDF/ontologies/blob/master/nif-core/nif-core.ttl) in Python.


## Example

### Create a `NIFDocument`.

```python
import json, time

from pyld import jsonld

from nif.annotation import NIFDocument


tic = time.time()
jsonld_path = 'examples/large.json'
with open(jsonld_path) as f:
    j = json.load(f)
tac = time.time()
print(f'loaded, {tac - tic}')

tic = time.time()
nd = NIFDocument.from_json(j)
tac = time.time()
print(tac - tic)
print(len(nd))
```

## Tests

To run tests do:
``` bash
> cd nif
> pytest
```
