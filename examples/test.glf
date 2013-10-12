:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec2 =pos
;

: rot ( vec2 float -> vec2 )
	:m _ c * swap s * ;
	=>vec
	dup sin =>s cos =>c
	[
		vec .y.x _ -
		vec .x.y _ +
	]v
;

:m angle .y.x / atan ;

: frame ( float -> vec4 )
	iGlobalTime + =>time
	pos length =>r

	pos time r + rot angle =>ta
	ta 3.1416 4.0 / mod
	 =>wing

	[
		time 2.7 * cos abs wing +
		time 3.3 * sin 1.0 r - * abs
		time 1.7 * sin r * abs
		1.0
	]v
;

gl_FragCoord .xy iResolution .xy / 0.5 - 2.0 * =pos

[ -0.1 -0.05 0.0 0.05 0.1 ] /frame \+ 5.0 / =gl_FragColor
