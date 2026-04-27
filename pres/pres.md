---
title: Medication Safety in Anaesthesia
sub_title: Computer Vision and Head-Mounted Displays in Healthcare
author: George L. F. Harris
theme:
    name: terminal-dark
    override:
        execution_output:
            colors:
                background: black
options:
    implicit_slide_ends: true
    incremental_lists: true
---

Problem
===

* Perioperative medication error
    * Self reported incident rate 
        * 0.004% [1]
    * Observer reported incident rate
        * 5.3% [2]
* Solutions?
    * Training
    * Electronic prescribing
    * Barcodes & labelling

<!-- pause -->

<!-- newlines: 5 -->
[1]: _Stipp MM, Deng H, Kong K, Moore S, Ron L Hickman J, Nanji KC. Medication safety in the perioperative setting: A comparison of methods for detecting medication errors and adverse medication events. Medicine. 2022;101(44):e31432. doi:10.1097/MD.0000000000031432_

[2]: _Nanji KC, Patel A, Shaikh S, Seger DL, Bates DW. Evaluation of Perioperative Medication Errors and Adverse Drug Events. Anesthesiology. 2016;124(1):25. doi:10.1097/ALN.0000000000000904_

A very brief introduction to Python
===
<!-- column_layout: [2,2] -->
<!-- column: 0 -->
```python +exec
/// import sys
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pres_helpers import print
/// from time import sleep
a = 5
b = 10
print( a + b )
```
<!--pause-->
```python +exec
/// import sys
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pres_helpers import print
for i in [1,2,3,4]:
    print( "Hello" * i )
```
<!--pause-->
```python +exec
/// import sys
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pres_helpers import print
def square(x):
    return x * x

print( square(2) )
```
<!-- column: 1 -->
<!-- pause -->
```python +exec
/// import sys
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pres_helpers import print
class Foo:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def multiply(self):
        return self.x * self.y
    def diff(self):
        return abs(self.x - self.y)

f = Foo(2,3)
print( f.multiply(), f.diff() )
```
<!-- pause -->
```python +exec
/// import sys
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pres_helpers import print
from time import sleep

for i in [1,2,3,4,5,6]:
    if i % 2 == 0:
        print( i )
        sleep(1)
```

Argus
===

```python +exec +line_numbers {1|3|5,6|8-10|12-15|all}
/// import sys
/// from time import sleep
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pres_helpers import print 
/// from pathlib import Path
from argus.image import Image

image_paths = Path('img/barcodes/').glob('*.jpg')

for path in image_paths:
    image = Image(path=path)

    codes = image.decode()
    for code in codes:
        print(f"Found code: {code}")

    image.show()
    sleep(0.5)
    image.show(kind="marked")
    sleep(0.5)
```

GTIN
====
<!-- column_layout: [2, 2] -->

<!-- column: 0 -->
Global Trade Item Number

Unique numbers for everything corporeal or incorporeal on Earth

![](gtin-fentanyl.jpg)

_Martindale Pharmaceuticals Fentanyl GTIN:_ 5014124170681

GTIN -> DM+D

Dictionary of Medicines and Devices

Information on:
<!-- pause -->
* Concentration
* Preparation
* Route of administration
* BNF & SNOMED codes
* Manufacturer

<!-- column: 1 -->

<!-- pause -->
![](dmd-fentanyl.jpg)

_https://dmd-browser.nhsbsa.nhs.uk_

<!-- end_slide -->
<!-- column_layout: [2,2] -->
<!-- column: 0 -->
```python +exec +line_numbers
/// import sys
/// from time import sleep
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pathlib import Path
/// from pres_helpers import print
from argus.image import Image
from argus.drugs import drug_db

image_paths = Path('img/barcodes/').glob('*.jpg')

for path in image_paths:
    image = Image(path=path)

    codes = image.decode()
    for code in codes:
        try: 
            drug = drug_db[code]
            print(f"Found drug: {drug}")
        except:
            pass
```

<!--pause-->
<!--column: 1-->
![](dmtx.jpg)
_dmtx.jpg_

```python +exec
/// import sys
/// from time import sleep
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pres_helpers import print
from argus.image import Image

image = Image(path='pres/dmtx.jpg')
code = image.decode(kind="dmtx",mark=False)[0]
/// code = code.replace("270630", "[red]270630[/red]")
/// code = code.replace("05014124170681", "[red]05014124170681[/red]")
print(code)
```


Carrier Test
===
```python +exec +acquire_terminal
/// import sys
/// sys.path.insert(0,'/home/glfharris/src/argus/')
/// from pres_helpers import carrier
def main():
    import time
    print("Hello")
    time.sleep(1)
/// carrier(main)
```

Local Scripts
===

```bash +exec +acquire_terminal
uv run python test.py
```
