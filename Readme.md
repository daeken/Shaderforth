Shaderforth
===========

Shaderforth is a shader language inspired by Forth and APL that compiles to GLSL.  It also contains a live development environment supporting multiple passes as well as user interface elements.

Getting Started
===============

You can compile shaders by running `python compiler.py [filename.srf] > output.glsl`.  To run the live development environment, simply run `python live/serve.py [filename.srf]` and then browse to http://localhost:5000/.

First Shader
------------

To start your first shader, let's break down a simple example:

	:globals
		@vec3 uniform =iResolution
		@float uniform =iGlobalTime
	;

	iResolution frag->position =p

	[
		p sin abs
		iGlobalTime sin abs
	] ->fragcolor

This compiles to:

	uniform vec3 iResolution;
	uniform float iGlobalTime;
	void main() {
		vec2 p = (gl_FragCoord.xy / iResolution.xy * 2. - 1.) * vec2(iResolution.x / iResolution.y, 1.);
		gl_FragColor = vec4(vec3(abs(sin(p)), abs(sin(iGlobalTime))), 1.);
	}

Each part is discussed in more detail below, but here's a quick overview of what this code is and what it compiles to.

The globals block defines each of your `uniform`, `varying`, and general global variables.  Everything following that is the `main` function; there's no need to explicitly define this function.

Shaderforth is stack-based, so the code is read left-to-right and top-to-bottom.  To call a function (a word, in Shaderforth terminology), simply push the arguments to the stack, then type the name of the function.  Its return value(s), if any, will be pushed onto the stack in turn.  So `iResolution frag->position` pushes the value `iResolution` to the stack, then invokes `frag->position`.  That's actually a macro, so the content is inlined, as you can see in the compiled code.  Following this invocation, the return value is assigned to the variable `p`, by `=p`.

Now that we have the position on the screen, we can generate our fragment color.  We create a vector using `[` and `]`.  These tokens are special, in that `[` creates a new context for the stack.  Once `]` is hit, everything in that new stack context is made into a vector.  In this case, we put three things into a vector: `p sin abs`, which translates to `abs(sin(p))`, and `iGlobal sin abs`, which translates to `abs(sin(iGlobalTime))`.  So the screen x and y coordinates give us the red and green components of the fragcolor, and the blue component oscillates based on the current time.

The `->fragcolor` macro turns the RGB vector into an RGBA vector (with alpha constant at `1`) and assigns it to `gl_FragColor`.

Language Features
=================

Words
-----

Words are the Shaderforth analogue to GLSL's functions.  They may take in arguments and return one or no value.  A simple example:

	: test ( float -> float ) 5 + ;

This compiles to:

	float test(float arg_0) {
		return arg_0 + 5.;
	}

You notice that there was no need to give arguments a name; arguments are on the stack in a left-to-right order.  That is, the topmost element of the stack is the rightmost argument.

However, it is possible to give arguments names as well, for simplicity's sake:

	: test2 ( left:float -> float ) left 5 + ;

Which compiles to:

	float test2(float left) {
		return left + 5.;
	}

Macros
------

Macros are much like words, but they are not translated into functions; instead, they are inlined into the context in which they are used.  This has several nice properties:

- They can use locals from the context they're invoked from
- They can return multiple values
- They can take blocks or compile-time arrays as arguments

The format to define a macro is almost exactly like a word:

	:m test 5 + ;

Here you can see an invocation:

	foo test =bar

And its compiled equivalent:

	float bar = foo + 5.;

Argument types and names are unnecessary -- you can leave off the whole signature, as you can see.  However, you can give names to arguments, which can often simplify code:

	:m test2 ( left ) left 5 + ;

This compiles to the same code as before; the only thing that has changed is the way in which you can access arguments.

It is possible to force arguments to be stored in variables prior to use; this can prevent duplication of code due to multiple uses in a macro.  This is done with the `$` sigil:

	:m test3 ( $left ) left 5 + left * ;
	foo 20 * test3 =baz

Compiles to:

	float macro_test3_left = foo * 20.;
	baz = (macro_test3_left + 5.) * macro_test3_left;

Locals and Macro Locals
-----------------------

Locals are assigned with `=name`.  This is translated directly to GLSL assignment, as you may expect.

Macro locals are assigned with `=>name` and exist only at compile-time.  This allows you to easily give names to your intermediate values, without bloating your compiled shaders.  In addition, you can store blocks, arrays, and other pieces of compile-time data in macro locals.

Arrays and Vectors
------------------

Arrays and vectors are equivalent and interchangable at compile-time.  The key difference is that unlike vectors, arrays may contain any values and any number of values; these can be operated upon in various useful ways.

A simple example of `[ 1 2 3 4 ]` will compile to `vec4(1., 2., 3., 4.)`, as you would expect.  But because of the compile-time nature of these arrays, you can use the map and reduce operators.  The reduce operator, `\`, works like you would expect; it passes the accumulator value and each element of the arrays to the given block.  For instance, `[ 1 2 3 4 ] \+` becomes `1. + 2. + 3. + 4.`; `[ 1 2 3 4 ] \max` would become `max(max(max(1., 2.), 3.), 4.)`.

The map operation, `/`, passes each element into a block to make a new array.  `[ 1 2 3 4 ] /sin` becomes `vec4(sin(1.), sin(2.), sin(3.), sin(4.))`.  This can be combined with the reduce operation: `[ 1 2 3 4 ] /sin \+` becomes `sin(1.) + sin(2.) + sin(3.) + sin(4.)`.

Blocks
------

Blocks are anonymous macros.  They can be used with the map/reduce operators or passed to other macros.  A simple example:

	foo { 5 + } call

This gets compiled to:

	foo + 5.

Like macros, you can give names to arguments if you desire:

	foo { ( left ) 5 + }

You can also use the `$` storage sigil on arguments, just like macros.

A simple example of using blocks with map:

	[ 1 2 3 4 ] /{ 5 + }

Compiles to:

	vec4(1. + 5., 2. + 5., 3. + 5., 4. + 5.)

You can also turn any word or macro into a block by use of `&name`; this makes it easy to pass existing words/macros.  Calling that block can be done using the `call` macro, or with `*arg`; this is equivalent to `arg call`.

Built-ins and Library
=====================

Operators
---------

`+`, `-`, `*`, `/`, `**` (power operator), `and` (equivalent to `&&`), `or` (equivalent to `||`)

Words
--------

- GLSL functions are all there as words (This isn't complete, but it's pretty straightforward to see how they are added)
- `=name` -- Assigns to a GLSL variable named `name`
- `=>name` -- Creates a local macro variable, whose value will be embedded literally wherever it's used
- `: name ( argtype argtype argtype -> returntype ) atom atom atom ;` -- Defines a word that will be created as a GLSL function
	- This can optionally take argument names, `argname:argtype`, which will become macro locals.
- `:m name atom atom atom ;` -- Defines a macro word whose contents will be inlined upon use
	- This can optionally take argument names, which will become macro locals.  `:m name ( arg1 arg2 ) atom atom atom ;`
- `( )` -- Everything between parentheses (make sure you include spaces around them -- these are both words) will be ignored as a comment, with the exception of type specifiers on words
- `[ atom atom atom ]` -- Defines an array
- `[ atom atom atom ]v` -- Defines a vector.  Equivalent to the same array followed by `avec`
- `/word` -- For each element of the array at the top of the stack, map against `word` -- this can take a macro word
- `\word` -- Performs a reduce operation with `word` against the array at the top of the stack -- this can take a macro word
- `flatten` -- Given an array at the top of the stack, this will turn the elements into native stack elements
- `avec` -- Takes an array from the top of the stack and generates a vector of the requisite size
- `dup` -- Duplicates the element at the top of the stack
- `swap` -- Swaps the top two elements of the stack
- Binary math operators -- They're used as expected
- Unary math operator `negate` -- Flips the sign on the topmost element
- `&word` -- Pushes a word reference to the stack
- `call` -- Executes a word reference
- `*name` -- Equivalent to `name call`
