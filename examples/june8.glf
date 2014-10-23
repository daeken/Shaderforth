:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec4 uniform =iDate
	@float =timeoff
;
:m time iDate .w timeoff + ;

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

:m intersect \max ;
:m union \min ;
:m subtract \{ neg max } ;

:m repeat! ( p c ) p c mod .5 c * - ;
:m repeat ( f p c ) p c repeat! dup p swap - *f ;
:m scale ( f p s ) p s / *f s length * ;
:m rotate ( f p a ) p a rotate-2d *f ;

:m slitcolor .2 .2 1 ;

: slit ( p:vec2 r:float i:float -> float )
	{ ( rp )
			rp [ r 0 ]v +
			.02
			[ .05 .01 ]v
		roundbox
	} p i .25 + tau * rotate
;

: distance-field ( p:vec2 -> vec4 )
	time 60 / 60 / floor 12 mod 12 / =hourpos
	time 60 / floor 60 mod 60 / =minutepos
		iGlobalTime timeoff + 1 mod iGlobalTime timeoff + 10 * sin abs 2 * 3 + ** 60 * floor 60 /
		time 60 mod floor 60 /
	+ =secondpos

	[
		[ p .45 secondpos slit slitcolor ]v
		[ p .25 minutepos slit slitcolor ]v
		[ p .1 hourpos slit slitcolor ]v
		[ p .015 circle 1 1 1 ]v
	] { .x } amin
;

:m texture ( d p )
	p distance-field .yzw =mat
	[ d neg 30 * 0 1 clamp mat * ]v
;

:m maxtoff .01 ;

: frame ( t:float -> vec3 )
	t =timeoff

	iResolution frag->position =p

		p { distance-field .x } gradient p texture
		t maxtoff + maxtoff /
	*
;

:m backframes 10 ;

[
	[
		{ ( i )
			maxtoff neg i float backframes 1 - / *
		} backframes int mtimes
	] /frame \+ backframes / 1.5 *
	1
]v =gl_FragColor
