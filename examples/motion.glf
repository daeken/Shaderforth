:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec4 uniform =iDate
;
:m time iGlobalTime ;

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

:m repeat! ( p c ) p c mod c 2 / * - ;
:m repeat ( f p c ) p c repeat! dup p swap - *f ;
: rad-mod ( p:vec2 c:float -> vec2 )
	p cart->polar =p
	[ p .x c mod c 2 / - p .y ] polar->cart
;
:m repeat-rad ( f p c ) p c rad-mod *f ;
:m scale ( f p s ) p s / *f s length * ;
:m rotate ( f p a ) p a rotate-2d *f ;

: calc-motion ( o:vec2 -> vec2 )
	[ time o .x + sin 10 / 0 ]
;

: fluidbox ( p:vec2 -> float )
	$[-1:+1:.4] /{ ( x )
		$[-1:+1:.4] /{ ( y )
				p [ x y ] 20 / +
				[ x y ] calc-motion
			+ .05 circle
		} \min
	} \min
;

:m obj-count 3 ;

: distance-field ( p:vec2 -> vec4 )
	[
		{ ( rp )
			{ ( rdp )
				rdp [ .5 0 ] - fluidbox
			} rp 360 obj-count / deg->rad repeat-rad
		} p 90 obj-count / neg deg->rad rotate
		0 0 0
	]
;

:m bgcolor [ 1 1 1 ] ;

:m texture ( d p )
	p distance-field .yzw =mat
	d neg 100 * 0 1 clamp =val
	 	bgcolor
		val mat *
		val
	mix
;

iResolution frag->position =p
[ p { distance-field .x } gradient p texture 1 ] =gl_FragColor
