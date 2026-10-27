# Code generation concepts

A _code generator_, simply speaking, is a computer program that produces as output, the source code for another program.

For example, this simple Python script writes a file named `test.c` which contains a C program that prints "Hello world" on the screen. The generated C program will have to be compiled with a C compiler in order to run.

```(python)
with open("test.c", "w") as fp:
    fp.write('''\
        #include <stdio.h>

        int main() {
            printf("Hello world\\n");
            return 0;
        }
    ''')
```

But why would we ever want to write a program that writes another program? And why would we need a library to do it?

## Why a code generator

When programming, we use code generators every day. Feastures like templates and C macros are code generators. They allow us defining coding patterns that are configured by parameters. 

For example, let's write the following C++ code:

```C++
template<class TYPE>
TYPE sum(TYPE a, TYPE b)
{
	return a+b;
}

auto a = sum<string>("foo", "bar"); // a = "foobar"
auto b = sum<int>(100, 200); // b = 300
```

We have used the `sum` function twice, one time configured with `TYPE=string` and the other with `TYPE=int`. The compiler generated **two versions** of the `sum` function that do different things: the first concatenates a string, the second one will execute a arithmetic sum. In other words, with templates we define parametric "meta-code" that becomes real code once we have filled in the parameters. If a function is code that takes data as a parameter and produces other data, a template is meta-code that takes code as a parameter and produces other code.

Many languages do support templates or macros: C, C++, Rust, Java, Swift, C# and many others.

Templates are indeed very powerful, but they can easily become useless when we exit from their declarative model capabilities. Let's take this example: we want to define a structure and we want a command that prints all the structure fields:

```C++
struct MyData {
	int x;
	int y;

	// Print the contents of this structure
	void print() const {
		cout << "x=" << x << endl;
		cout << "y=" << y << endl;
	}
};
```

If we add another field `z`, we have to go to the `print()` method and manually add a line to print `z` as well. Although the commands that print each field in the `print()` method are clearly created following the pattern `cout << "NAME=" << NAME << endl;` where `NAME` is the name of the field, there is no way for the template system to do this automatically.

A code generator is a program that writes the code. So we can write a code generator that takes as input the list of fields and their types (`int x` and `int y`) and writes the structure and the related `print()` method. We can now define tens of structures with hundred of fields and have the code generator taking care of the additional code.

This approach has several advantages:

* we don't have to update the repetitive code every time a field is changed, added or removed
* we can change our mind on how the repetitive code is written; for example, we might later discover that the way we are printing the data is not very readable and we want to try different layouts: just change the code generator and run it;
* we can add other repetitive code; for example, we might later discover that we would like to have a "verbose" and a "compact" print function: the code generator will massively implement them on all the structures;
* no one will ever forget to add a field to the `print()` function since the code generator is doing

## Why a code generator library?

Generating code is a matter of opening an ASCII file and writing the code in it, nothing less, nothing more.
However, whoever attempted to develop a code generator, soon discovered that the code that implements the code generator becomes quickly unmanageable. The code that implements the code generator and the code in the "print" calls that writes the generated code soon mix in a mess that makes very hard to understand what is what.

Things apparently very simple like write the correct indentation in the generated code can quickly become a real headache. Furthermore, when looking at the generated code, it can be very hard to trace back to the code in the code generator that generated each part of it to make changes, fixes or enhacements.

The PyMeatProg library works by "concepts". Instead of directly writing the generated code, we can compose conceptual structures and the library will take care of writing the code. We can say something like *I want a class containing these attributes and methods* and the library will actually write the the code with all the correct syntax and indents.

<!-- HIDDEN COMMENT EXAMPLE -->
```py
# This is code
```

```py
# This is code
<mark>This line is new</mark>
```