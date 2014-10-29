:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec2 =pos
;

: rot ( vec:vec2 a:float -> vec2 )
	:m _ ( a b f ) a c * b s * *f ;
	a sin =>s
	a cos =>c
	[
		vec .x.y &- _
		vec .y.x &+ _
	]v
;

:m angle .y.x / atan ;

: frame ( float -> vec4 )
	iGlobalTime + =>time
	pos length =>r

	pos time r time 3 * sin * + rot =ta
	ta angle 3.1416 4 / mod =wing

	[
		time 2.7 * cos abs wing +
		time 3.3 * sin 1 r - * wing * abs
		time 1.7 * sin r * abs
		1
	]v
;

iResolution frag->position =pos

[ -0.1 -0.05 0 0.05 0.1 ] /frame \+ 5 / =gl_FragColor
