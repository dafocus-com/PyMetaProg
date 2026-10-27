# Getting started with ADT model

This document shows how to setup a code generator based on ADT (Abstract Data Types).

This kind of generator relies on an abstract, agnostic description of data structures that can produce the same result in multiple languages.

## Import the `metaprog` modules

Import components that are needed for the languages addressed for the code generation:

```py

# Import the ADT modules
from metaprog.adt import *

# In case the target includes Python
from metaprog.py import *
from metaprog.py_gen import *

# In case the target includes C++
from metaprog.cpp import *
from metaprog.cpp_gen import *

# In case the target includes C#
from metaprog.cs import *
from metaprog.cs_gen import *
```

## Define the ADTs

The following step implies defining the ADTs, i.e. what structures and which fields we want in them.

The ADTs are included in a `AdtClassSet` that is to be instanced:

```py
# Create the ADT set that will contain the ADTs we are defining
adtClassSet:AdtClassSet = AdtClassSet()
```

Now define the classes:

```py
# The ADT class is automatically registered to the `adtClassSet`
car:AdtClass = adtClassSet.appendClass(
    AdtClass(
        className="Car",
        brief="Describes one car model",
        fields=[
            AdtField(
                fieldName="brand",
                fieldType=AdtTypeString(),
                brief="The car brand",
            ),
            AdtField(
                fieldName="model",
                fieldType=AdtTypeString(),
                brief="The car model",
            ),
            AdtField(
                fieldType=AdtTypeFloat(),
                fieldName="mpg",
                brief="Average miles per gallon",
            ),
            AdtField(
                fieldType=AdtTypeInteger(bits=32, signed=True),
                fieldName="seats",
                brief="Number of passegers this car can carry",
            ),
        ],
    )
)
```

The `AdtClass` reference can be saved to be used to define a further ADT. In this example we use `car` to define a list of cars:

```py
adtClassSet.appendClass(
    AdtClass(
        className="CarList",
        brief="Contains a list of cars",
        fields=[
            AdtField(
                fieldName="cars",
                # The field type is a "vector", i.e. an array
                fieldType=AdtTypeVector(
                    # The type contained by the vector, i.e. the type of its elements,
                    # is defined as a refernce to an existing class (`AdtTypeClass`) which
                    # ia saved in variable `cars`.
                    containedType=AdtTypeClass(
                        adtClass=cars, 
                        polymorphic=False
                    )
                ),
                brief="List of cars",
            ),
        ]
    )
)
```

## Generate python

```py
# Python generation
pyConfig:PyConfig = PyConfig()
pyPackage:PyPackage = PyPackage(packageName='my_package')

# Create a python module named `my_module` and add it to the package
pyModule:PyModule = PyModule(moduleName='my_module')
pyPackage.addChild(child=pyModule)

# Create a `PyFromAdt` generator instance.
pyFromAdt:PyFromAdt = PyFromAdt(defaultNameScope=pyModule)

# Ask the `PyFromAdt` to generate python classes starting from the ADT definition
pyClasses:list[PyClass] = pyFromAdt.generate(adtClassSet=adtClassSet)

# Now define the additional generators that will add features to the generated
# python code.
pyGeneratorSet:PyGeneratorSet = PyGeneratorSet()
pyGeneratorSet.addGenerator(pyGenerator=PyMarshalGenerator(mode=PyMarshalGeneratorMode.AUTO_INCLUDE))
pyGeneratorSet.addGenerator(pyGenerator=PyPrintGenerator())

# Add the python classes to the generator set; this will tell which python classes need to
# be decorated
pyGeneratorSet.addClasses(pyClasses=pyClasses)

# Run the generator set; here it will actually add methods and attributes to the classes.
pyGeneratorSet.decorateClasses()

# Run the generation of the target files
pyPackage.generate(config=pyConfig, pyFilePath=pythonTargetDir)
```