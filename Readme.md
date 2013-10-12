Shaderforth
===========

Shaderforth is a horrendously ugly experiment in making GLSL shaders using a Forth- and APL-inspired language.

Structure
---------

The structure of Shaderforth files is a top-level `main` word, one or more `globals` words, any number of normal words, and macro words.

Here's a simple GLSL fragment shader:

	uniform vec3 iResolution;
	uniform float iGlobalTime;

	void main() {
		vec2 pos = (gl_FragCoord.xy / iResolution.xy - 0.5) * 2.0;
		float temp = abs(sin(length(pos) * cos(iGlobalTime)));
		gl_FragColor = vec4(temp, temp, temp, 1.0);
	}

And here's one terse ShaderForth equivalent:

	:globals
		@vec3 uniform =iResolution
		@float uniform =iGlobalTime
	;

	gl_FragCoord .xy iResolution .xy / 0.5 - 2.0 *
	length iGlobalTime cos * sin abs
	dup dup 1.0 vec4 =gl_FragColor

Which compiles to:

	uniform vec3 iResolution;
	uniform float iGlobalTime;
	void main() {
		float var_0 = abs(sin((length(((((gl_FragCoord).xy) / ((iResolution).xy)) - (0.5)) * (2.0))) * (cos(iGlobalTime))));
		gl_FragColor = vec4(var_0, var_0, var_0, 1.0);
	}

And another:

	:globals
		@vec3 uniform =iResolution
		@float uniform =iGlobalTime
	;

	gl_FragCoord .xy iResolution .xy / 0.5 - 2.0 * length =distance
	distance iGlobalTime cos * sin abs =>color
	color color color 1.0 vec4 =gl_FragColor

Which compiles to:

	uniform vec3 iResolution;
	uniform float iGlobalTime;
	void main() {
		float distance = length(((((gl_FragCoord).xy) / ((iResolution).xy)) - (0.5)) * (2.0));
		gl_FragColor = vec4(abs(sin((distance) * (cos(iGlobalTime)))), abs(sin((distance) * (cos(iGlobalTime)))), abs(sin((distance) * (cos(iGlobalTime)))), 1.0);
	}

Words
--------

- GLSL functions are all there as words (This isn't complete, but it's pretty straightforward to see how they are added)
- `=name` -- Assigns to a GLSL variable named `name`
- `=>name` -- Creates a local macro variable, whose value will be embedded literally wherever it's used
- `: name ( argtype argtype argtype -> returntype ) atom atom atom ;` -- Defines a word that will be created as a GLSL function
- `:m name atom atom atom ;` -- Defines a macro word whose contents will be inlined upon use
- `( )` -- Everything between parentheses (make sure you include spaces around them -- these are both words) will be ignored as a comment, with the exception of type specifiers on words
- `[ atom atom atom ]` -- Defines an array
- `/word` -- For each element of the array at the top of the stack, map against `word` -- this can take a macro word
- `\word` -- Performs a reduce operation with `word` against the array at the top of the stack -- this can take a macro word
- `flatten` -- Given an array at the top of the stack, this will turn the elements into native stack elements
- `avec` -- Takes an array from the top of the stack and generates a vector of the requisite size
- `dup` -- Duplicates the element at the top of the stack
- `swap` -- Swaps the top two elements of the stack
- Binary math operators -- They're used as expected
- Unary math operator `negate` -- Flips the sign on the topmost element
