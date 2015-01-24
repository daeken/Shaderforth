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

Numbers
-------

By default, all numeric constants in Shaderforth are floats.  If you need an int, you can either cast it (e.g. `5 int`) or use an integer constant (e.g. `#5`).

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

It's possible to forego argument names while still retaining some of the benefits, though, in the case of 1-argument macros.  The sole argument can be referred to using `_` if no other names are provided.  For example, this is equivalent to `test2`:

	:m test3 _ 5 + ;

It is possible to force arguments to be stored in variables prior to use; this can prevent duplication of code due to multiple uses in a macro.  This is done with the `$` sigil:

	:m test4 ( $left ) left 5 + left * ;
	foo 20 * test3 =baz

Compiles to:

	float macro_test4_left = foo * 20.;
	baz = (macro_test4_left + 5.) * macro_test4_left;

Arguments to macros may also deconstruct arrays.  For example:

	:m test5 ( [ a [ b c ] ] ) a b c * + ;
	[ foo [ bar baz ] ] test5

Compiles to:
	foo + bar * baz

The elements of each array are assigned according to their position in the argument spec.


Locals and Macro Locals
-----------------------

Locals are assigned with `=name`.  This is translated directly to GLSL assignment, as you may expect.

Macro locals are assigned with `=>name` and exist only at compile-time.  This allows you to easily give names to your intermediate values, without bloating your compiled shaders.  In addition, you can store blocks, arrays, and other pieces of compile-time data in macro locals.

To assign to a macro local while ensuring that the value is backed by a variable (to prevent pollution of the runtime namespace), you can use the `=$name` operation.

Arrays and Vectors
------------------

Arrays and vectors are equivalent and interchangable at compile-time.  The key difference is that unlike vectors, arrays may contain any values and any number of values; these can be operated upon in various useful ways.

A simple example of `[ 1 2 3 4 ]` will compile to `vec4(1., 2., 3., 4.)`, as you would expect.  But because of the compile-time nature of these arrays, you can use the map and reduce operators.  The reduce operator, `\`, works like you would expect; it passes the accumulator value and each element of the arrays to the given block.  For instance, `[ 1 2 3 4 ] \+` becomes `1. + 2. + 3. + 4.`; `[ 1 2 3 4 ] \max` would become `max(max(max(1., 2.), 3.), 4.)`.

The map operation, `/`, passes each element into a block to make a new array.  `[ 1 2 3 4 ] /sin` becomes `vec4(sin(1.), sin(2.), sin(3.), sin(4.))`.  This can be combined with the reduce operation: `[ 1 2 3 4 ] /sin \+` becomes `sin(1.) + sin(2.) + sin(3.) + sin(4.)`.

The filter operation, `?`, conditionally includes/excludes elements at compile-time based on a predicate.  For instance, `[ 1 2 3 4 ] ?{ 2 >= }` is equivalent to `[ 2 3 4 ]`, as `1 2 >=` is false.  This must be evaluated at compile-time -- no runtime support is available.

You can turn an array into a matrix using the `amat` word, or by closing your array definition with `]m`.

Swizzling
---------

Like in GLSL, vectors can be swizzled.  `foo .xyz` is equivalent to `foo.xyz`, as you might expect.  However, this has been expanded in Shaderforth.  `foo .xy.z` will push both `foo .xy` and `foo .z` to the stack.  It's important that there is no space between the swizzles, otherwise those operations would be performed in series, not in parallel, ending in invalid results.

Array Assignment
----------------

Arrays can be assigned to locals/macro locals using the `=[ ]` and `=>[ ]` operations.  For instance, `[ 1 2 ] =[ foo bar ]` would assign `1` and `2` to `foo` and `bar`, respectively.

Range Constants
---------------

Range constants allow the easy creation of arrays.  They take the form of `$[start:end:step]`.  Start and step are optional, but start must be present if step is to be used.  This is normally exclusive, so `$[0:5:1]` is `[ 0 1 2 3 4 ]`; however, you can indicate an inclusive range by beginning the end value with `+`.  E.g. `$[0:+5:1]` is `[ 0 1 2 3 4 5 ]`.

Blocks
------

Blocks are anonymous macros.  They can be used with the map/reduce operators or passed to other macros.  A simple example:

	foo { 5 + } call

This gets compiled to:

	foo + 5.

Like macros, you can give names to arguments if you desire:

	foo { ( left ) 5 + }

You can also use the `$` storage sigil on arguments, just like macros.  The use of `_` and deconstructive arguments from macros also applies to blocks.

A simple example of using blocks with map:

	[ 1 2 3 4 ] /{ 5 + }

Compiles to:

	vec4(1. + 5., 2. + 5., 3. + 5., 4. + 5.)

You can also turn any word or macro into a block by use of `&name`; this makes it easy to pass existing words/macros.  Calling that block can be done using the `call` macro, or with `*arg`; this is equivalent to `arg call`.

Conditional Compilation
-----------------------

The `~` operator allows conditional compilation.  When the item on the top of the stack is true (this must be evaluable at compile-time), the referenced item is executed.  For instance:

    5 1 0 > ~{ 5 + }

Would evaluate to `5 5 +` because `1 0 >` evaluates to `true`, and the condition is consumed by `~`.

Variable Literals
-----------------

You can create a literal variable reference by the use of the `$` sigil on a name.  Variable literals can be useful for overloading existing variable names.  For instance:

    :m gl_FragCoord $gl_FragCoord offset + ;
    gl_FragCoord some-word

Would compile to:

    some_word(gl_FragCoord + offset);

Built-ins and Library
=====================

Operators
---------

`+`, `-`, `*`, `/`, `**` (power operator), `and` (equivalent to `&&`), `or` (equivalent to `||`), `neg` (equivalent to unary `-`).

Constant folding takes place automatically and no-op math (e.g. adding, subtracting, or multiplying by 0 or multiplying/dividing by 1) is removed.

Built-ins
---------

- GLSL functions are all there as words (Incomplete)
- `flatten` -- Given an array at the top of the stack, this will turn the elements into native stack elements
- `dup` -- Duplicates the element at the top of the stack
	- `!name` -- Equivalent to `dup name`
- `swap` -- Swaps the top two elements of the stack
- `take ( num )` -- Moves element `num` down from the top of the stack to the top
- `call` -- Invokes a block
	- `*name` -- Equivalent to `name call`
- `int ( val )` and `float ( val )` -- Casts to `int` or `float`, respectively
- `times ( block count )` -- Calls `block` `count` times, passing `0` to `count - 1` to `block`; this is translated to a `for` loop
	- `continue` -- Skips to the next iteration of the loop
	- `break` -- Terminates execution of the loop
- `mtimes ( block count )` -- Just like `times`, except that the loop is unrolled at compile-time
- `when ( block cond )` -- If `cond` is true, call `block`
- `if ( then else cond )` -- If `cond` is true, call `then`, otherwise call `else`
- `select ( a b cond )` -- If `cond` is true, return `a`, otherwise return `b`.  Equivalent to `?:` in GLSL
- `cond ( cases )` and `choose ( cases )` -- See below
- `size ( arr )` -- Returns the length of `arr`
- `upto ( top )` -- Returns an array containing 0-top, exclusive
- `enumerate ( arr )` -- Returns an enumerated array based on `arr`, where each element is turned into `[ index element ]`.  E.g. `[ 4 5 6 ] enumerate` is `[ [ 0 4 ] [ 1 5 ] [ 2 6 ] ]`
- `return ( value )` -- Returns the given value
- `return-nil` -- Returns from word with no value

### `cond` and `choose`

`cond` makes it easy to chain together comparisons.  See this example:

	[
		foo 0 == { 0 =bar }
		foo 1 > { 2 =bar }
		{ 8 =bar }
	] cond

This is compiled to:

	if(foo == 0.) {
		bar = 0.;
	} else if(foo > 1.) {
		bar = 2.;
	} else {
		bar = 8.;
	}

Note that it takes the form of one or more `if` pairs, then an optional `else`.

`choose` is similar.  The differences are that it's turned into a ternary tree, all comparisons must be equality (it's similar to a C switch in that regard), and instead of using blocks, it uses values.  So for instance:

	[
		0 0
		1 2
		8
	] foo choose =bar

Compiles to:

	bar = foo == 0. ? 0. : foo == 1. ? 2. : 8.;

Utility
-------

These are all defined in `utility.sfr` and comprise the "standard library" for Shaderforth.  Most are convenience functions that will simply serve to make your life easier.

- `pi`, `tau`, `eps`, `inf`, `_e` -- Approximate definitions of various constants
- Comparators
	- `amin ( arr f )` -- Finds the minimum value of `f(element)` for each element of `arr`, then returns the corresponding element
	- `amax ( arr f )` -- Equivalent to `amin`, for maximums
	- `minmax ( a b )` -- Returns an array containing first the minimum of `a` and `b`, then the maximum
- Maths
	- `closest-point-line ( a b point )` -- Given line `a-b`, returns the point on the line that is closest to `point` (2D only)
	- `point-distance-line ( a b point )` -- Given line `a-b`, returns the distance from `point` to the closest point on the line
	- `deg->rad ( val )` and `rad->deg ( val )` -- Converts from degrees to radians and vice versa
	- `rotate-2d ( c a )` -- Rotates 2d point `c` around the origin by `a` radians
	- `sq ( val )` -- Squares `val`
- Coordinate system utilities
	- `cart->polar ( p )` and `polar->cart ( p )` -- Converts `p` from cartesian to polar coordinates and vice versa.  Polar vector is of the form `[ angle radius ]`
	- `cart->logpolar ( p )` and `logpolar->cart ( p )` -- Converts `p` from cartesian to logarithmic polar coordinates and vice versa.  This is equivalent to the polar coordinates above, except that the natural logarithm of `radius` is taken
	- `polar-norm ( p )` -- Normalizes polar coordinates by bringing the angle into the range 0 - tau
	- `p+ ( p v )` and `p- ( p v )` -- Convenience functions for adding and subtracting with coordinates.  Converts `p` to polar coordinates, adds/subtracts `v`, then converts back to cartesian
	- `frag->position ( resolution )` -- Converts fragment coordinates to be in the range of -1 to 1 for the height.  The range of the width will depend on the aspect ratio; if it's 1:1, then the range will also be -1 to 1.
- Distance field utilities
	- `gradient ( f p )` -- Finds the gradient of a 2d isosurface, given a definition `f` and point `p`.  See [http://www.iquilezles.org/www/articles/distance/distance.htm](this article) for more information
- Color operations
	- `hsv->rgb ( hsv )` -- Converts a vector of HSV value into RGB.  H should be in the range 0-360, with S and V in the range 0-1.
	- `hsv1->rgb ( hsv )` -- Works like `hsv->rgb`, except that H is in the range 0-1.
	- `->fragcolor ( color )` -- Assigns `color` to `gl_FragColor`, expanding it to RGBA with constant alpha 1
- Array operations
	- `multi2 ( arr )` and `multi3 ( arr )` -- Turns a 1d array into a 2d or 3d array, respectively.
		- For instance, `[ 1 2 3 ] multi2` generates `[ [ 1 1 ] [ 1 2 ] [ 1 3 ] [ 2 1 ] [ 2 2 ] ... ]`
- Image operations
	- `blur ( f )` -- Performs a simple blur operation on a 2d function, `f`, and returns the result
