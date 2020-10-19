# NIF annotation package

A package to help using [NIF](https://github.com/NLP2RDF/ontologies/blob/master/nif-core/nif-core.ttl) in Python.


## Example

Read `json-ld` and serialize as turtle.

```python
from pathlib import Path

from nif.annotation import NIFDocument

def read_and_print(file_path: Path):
    with file_path.open() as f:
        s = f.read()
    print(s)
    d = NIFDocument.parse_rdf(s,format='json-ld')
    result = d.serialize(format="ttl").decode()
    print(result)


if __name__ == '__main__':
    doc_path = Path('<PATH TO YOUR JSON-LD FILE HERE>')
    read_and_print(doc_path)
```

### Tests

To run tests do:
``` bash
> cd nif
> nosetests tests/
```

## TODOs

- Add examples of usage
- Add install instructions (`pip install -e <github.com:semantic-web-company/nif.git>`)
- Make nif__anchor_of optional for NIFAnnotation 