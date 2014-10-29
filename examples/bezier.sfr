:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;

:m steps #20 ;
:m step-delta 1 steps #1 - float / ;

: point-in-curve-box ( s:vec2 c1:vec2 c2:vec2 e:vec2 p:vec2 err:float -> bool )
	[ s c1 c2 e ] =>cp
	[
		cp /{ .x } \min err -
		cp /{ .y } \min err -
		cp /{ .x } \max err +
		cp /{ .y } \max err +
	]v =bounds

	[
		bounds .x p .x <=
		bounds .y p .y <=
		p .x bounds .z <
		p .y bounds .w <
	] \and
;

: curve-dist ( s:vec2 c1:vec2 c2:vec2 e:vec2 p:vec2 -> float )
	10000 =dist

	{
		s =prev
		{ ( i )
			i float step-delta * =t

			s c1 t mix =>a1
			c1 c2 t mix =a2
			c2 e t mix =>a3

			a1 a2 t mix =>b1
			a2 a3 t mix =>b2

			b1 b2 t mix =cur

			p { ( gp ) prev cur gp point-distance-line } gradient dist min =dist
			cur =prev

			&break dist 0.005 <= when
		} steps times
	} s c1 c2 e p 0.05 point-in-curve-box when
	dist
;

: warp ( c:vec2 -> vec2 )
	c iGlobalTime 4 * sin 4 + 3 / *
;

iResolution frag->position =p

[
	[ [ [ 0.022188 0.094792 ]v [ 0.015938 0.194792 ]v [ -0.118437 0.290625 ]v [ -0.130937 0.082292 ]v ] [ 1.000000 0.000000 0.000000 ]v ]
	[ [ [ -0.130937 0.082292 ]v [ -0.140312 -0.117708 ]v [ 0.033125 -0.282292 ]v [ 0.022188 -0.261458 ]v ] [ 0.000000 1.000000 0.000000 ]v ]
	[ [ [ 0.022188 0.094792 ]v [ 0.028438 0.194792 ]v [ 0.162813 0.290625 ]v [ 0.175313 0.082292 ]v ] [ 0.000000 0.000000 1.000000 ]v ]
	[ [ [ 0.175313 0.082292 ]v [ 0.184688 -0.117708 ]v [ 0.011250 -0.282292 ]v [ 0.022188 -0.261458 ]v ] [ 1.000000 0.000000 1.000000 ]v ]
] /{ =>[ cp color ] [ color cp /warp flatten p curve-dist ]v } { .w } amin =hit
[ hit .w.xyz ] =>[ dist color ]

dist 0.02 - neg 50 * =>dist

[ color dist * 1 ]v =gl_FragColor
