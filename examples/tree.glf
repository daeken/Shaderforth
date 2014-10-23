:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec4 uniform =iDate
;
:m time iDate .w ;
:m mtime iGlobalTime ;

:m circle ( p r )
	p length r -
;
:m box ( p d )
	( p abs d - 0 max length )
	p abs d - =t
		t \max 0 min
		t 0 max length
	+
;
:m roundbox ( p r d )
	 p d box r -
;

: arc ( p:vec2 d:vec3 -> float )
		p [ -1 1 ] * cart->polar [ pi 2 / d .z ] - polar-norm
		[
			d .x dup tau eps - - 0 1 clamp inf * +
			d .y
		]
	box
;

:m intersect \max ;
:m union \min ;
:m matintersect { .x } amax ;
:m matunion { .x } amin ;
:m subtract \{ neg max } ;

:m repeat! ( p c ) p c mod .5 c * - ;
:m repeat ( f p c ) p c repeat! dup p swap - *f ;
:m scale ( f p s ) p s / *f s length * ;
:m rotate ( f p a ) p a rotate-2d *f ;

:m fractal ( p )
	[
		p .05 circle
		{
			p [ .3 0 ] + fractal
			p [ .3 0 ] - fractal
			p [ 0 .3 ] + fractal
			p [ 0 .3 ] - fractal
		} { p .05 box } #1 recur
	] union
;

: distance-field ( p:vec2 -> vec4 )
	[ p fractal 1 1 1 ]
;

:m texture ( d p )
	p distance-field .yzw =mat
	[ d neg 200 * 0 1 clamp mat * ]
;

iResolution frag->position =p
[ p { distance-field .x } gradient p texture 1 ] =gl_FragColor
