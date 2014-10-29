:globals
	@vec3 uniform =iResolution
	@vec4 uniform =iMouse
	@float uniform =iGlobalTime
	@sampler2D uniform =grid
;
:m time iGlobalTime ;
:m mousepos iMouse .xy [ 1 -1 ]v * 1 + 2 / ;

:m wavespeed .8 ;
:m wavelife .4 ;
:m gridsize .2 ;
:m timedelta .1 ;

:m sq dup * ;
:m calc1
		4 8 wavespeed sq * timedelta sq * gridsize sq / -
		wavelife timedelta * 2 +
	/
;
:m calc2
	wavelife timedelta * =>t
	t 2 - t 2 + /
;
:m calc3
		2 wavespeed sq * timedelta sq * gridsize sq /
		wavelife timedelta * 2. +
	/
;

: val1 ( p:vec2 o:vec2 -> float )
		grid
		p o iResolution .xy / + 1 + 1 mod
	texture2D .x
;

: wave ( -> void )
	gl_FragCoord .xy iResolution .xy / =p
	grid p texture2D =prev

			prev .zw
			mousepos
			p
		point-distance-line .02 swap - 0 1 clamp 2 /
		0
		[
			mousepos .5 - length 0 >
			prev .zw length 0 >
			mousepos prev .zw - length 0 >
		] \and
	select =>add

	[
		calc1 prev .x *
		calc2 prev .y *
		calc3 [
			[ 1 0 ]v [ -1 0 ]v [ 0 1 ]v [ 0 -1 ]v
			[ 1 1 ]v [ -1 1 ]v [ 1 -1 ]v [ -1 -1 ]v
		] /{ p swap val1 } \+ 2 / *
		add
	] \+ 1 .0001 - * =>val

	[ val prev .x mousepos ]v =gl_FragColor
;

[
	grid gl_FragCoord .xy iResolution .xy / texture2D 3 * .r.g
	dup
	1
]v =gl_FragColor

:passes
	wave =grid
;
