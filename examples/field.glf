:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;
:m time iGlobalTime ;

: circle ( p:vec2 r:float -> float )
	p length r -
;
: box ( p:vec2 d:vec2 -> float )
	p abs d - =d
		d \max 0 min
		d 0 max length
	+
;

:m intersect max ;
:m subtract neg max ;
:m union min ;
:m shape call ;

iResolution frag->position .5 / =p

: distance-field ( p:vec2 -> vec2 )
	[
		[ p [ time sin 0.3 time * sin ]v + [ 0.3 0.3 ]v box 0 ]v
		[ p [ 0.2 time * sin 0.7 time * sin ]v + [ 0.37 time * cos abs 0.1 + 0.3 * 0.4 ]v box 1 ]v
		[ p [ 0.7 time * sin 0.13 time * sin ]v + 0.5 circle 2 ]v
	] { .x } amin
;

: material ( id:float -> vec4 )
	[
		0 id == { [ 1 0 0 1 ]v }
		1 id == { [ 0 1 0 1 ]v }
		2 id == { [ 0 0 1 1 ]v }
		{ [ 1 0 1 1 ]v }
	] cond
;

: texture ( p:vec2 d:float -> vec4 )
	p distance-field .y material =mat
	d neg mat 100 * *
;

	p
	p { distance-field .x } gradient
texture =gl_FragColor
