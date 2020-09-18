# SRUpy: SRU client for Python

!! Note: This package is still under development, so don't expect too much!

SRUpy is designed to be compatible with the [Polymatheia](https://github.com/scmmmh/polymatheia) library.
Polymatheia uses [Sickle](https://github.com/mloesch/sickle) to fetch data from OAI-PMH endpoints - that's
why SRUpy is highly influenced by Sickle.

Another client for SRU requests is [sruthi](https://github.com/metaodi/sruthi).  
 
## Installation

```
pip install srupy
```

## Examples
### Simple SRU request
```python
from srupy import SRUpy

SRU_API = "http://sru.k10plus.de/gvk"
MAXIMUM_RECORDS = 10
QUERY = "dog cat mouse fish horse"
RECORD_SCHEMA = "mods"

# Explain record
explain = SRUpy(SRU_API).explain()
print(explain)
print(explain.echo)

# SRU Request
sru_records = SRUpy(SRU_API).get_records(
                         query=QUERY,
                         maximumRecords=MAXIMUM_RECORDS,
                         recordSchema=RECORD_SCHEMA
                         )

print(sru_records.number_of_records)

for r in sru_records:
    print(r)
```

### Making use of the Polymatheia library
see [Polymatheia on GitHub](https://github.com/scmmmh/polymatheia)
(a dedicated SRURecordReader for Polymatheia is on my todo list ;)
```python
from srupy import SRUpy
from polymatheia.data import NavigableDictIterator, xml_to_navigable_dict
from polymatheia.data.writer import LocalWriter
from lxml import etree

SRU_API = "http://sru.k10plus.de/gvk"
MAXIMUM_RECORDS = 10
QUERY = "dog cat mouse fish horse"
RECORD_SCHEMA = "mods"

OUTPUT_PATH = "/home/andreas/output"

# Explain record
explain = SRUpy(SRU_API).explain()
print(explain)
print(explain.echo)

# SRU Request
sru_records = SRUpy(SRU_API).get_records(
                         query=QUERY,
                         maximumRecords=MAXIMUM_RECORDS,
                         recordSchema=RECORD_SCHEMA
                         )

print(sru_records.number_of_records)

# make records navigable using Polymatheia library
records = NavigableDictIterator(sru_records,
                                mapper=lambda record: xml_to_navigable_dict(
                                    etree.fromstring(
                                        record.raw,
                                        parser=etree.XMLParser(remove_comments=True)
                                    )
                                ))

for r in records:
    try:
        print(r.zs_recordData["{http://www.loc.gov/mods/v3}mods"].titleInfo.title._text)
    except:
        a = 1  # do nothing

# write files to disk using Polymatheia    
w = LocalWriter(OUTPUT_PATH,
                ["zs_recordData", "{http://www.loc.gov/mods/v3}mods", "recordInfo", "recordIdentifier", "_text"])
w.write(records)
```