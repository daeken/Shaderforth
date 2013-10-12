:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec2 =pos
;

: frame ( float -> vec4 )
	iGlobalTime + =>time
	pos length =>plen

	[
		time 2.7 * cos abs
		time 3.3 * sin 1.0 plen - * abs
		time 1.7 * sin plen * abs
		1.0
	]v
;

gl_FragCoord .xy iResolution .xy / 0.5 - 2.0 * =pos

[ -0.1 -0.05 0.0 0.05 0.1 ] /frame \+ 5.0 / =gl_FragColor
