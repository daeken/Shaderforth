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

:m repeat! ( p c ) p c mod .5 c * - ;
:m repeat ( f p c ) p c repeat! dup p swap - *f ;
:m scale ( f p s ) p s / *f s length * ;
:m rotate ( f p a ) p a rotate-2d *f ;

: bc ( p:vec2 r:float -> float )
		p r box
		p r circle
		time 8 mod 4 - abs 1 2 clamp 1 -
	mix abs .01 - =d

	17 =>fac
	d p .x fac * sin p .y fac * sin * abs .05 * +
;

:m glider ( f p )
	[
		p [   0 .5 ] - *f
		p [ -.5  0 ] + *f
		p [ -.5 .5 ] + *f
		p [  .5 .5 ] + *f
		p [   0 .5 ] + *f
	] union
;

: tbox ( p:vec2 -> float )
	p .2 box
;

: inner ( sp:vec2 -> float )
	&tbox sp glider
;

: subgl ( gp:vec2 -> float )
	&inner gp .325 scale
;

: distance-field ( p:vec2 -> vec4 )
	[
		&subgl p glider
		0 0 0
	]
;

:m bgcolor [ 1 1 1 ] ;

:m texture ( d p )
	p distance-field .yzw =mat
	d neg 1000 * 0 1 clamp =val
	[
			bgcolor
			val mat *
			val
		mix
	]
;

iResolution frag->position =p
[ p { distance-field .x } gradient p texture 1 ] =gl_FragColor
