:globals
	@vec3 uniform =iResolution
	@vec4 uniform =iMouse
	@float uniform =iGlobalTime
	@sampler2D uniform =grid
	@bool uniform =running
	&running toggle
;
:m time iGlobalTime ;
:m mousepos iMouse .xy [ 1 -1 ]v * 1 + 2 / ;
:m mousedown iMouse .z 1 == ;

:m grid-res [ 160 120 ]v ;
:m get ( off )
	grid p off grid-res * + texture2D .x 1000 * 0 1 clamp
;

: gol ( -> sampler2D )
	{
		[ 0 0 0 0 ]v =gl_FragColor
		return-nil
	} time .1 < when

	gl_FragCoord .xy iResolution .xy / =p
	grid p texture2D =prev
	prev .x =cur

		1 cur -
		cur
		[
			mousedown
			prev .w 1 !=
			[ p mousepos ] /{ grid-res * floor } \- length 1 <
		] \and
	select =cur

	{
		[
			[ 1 0 ] [ -1 0 ] [ 0  1 ] [ 0 -1 ]
			[ 1 1 ] [ -1 1 ] [ 1 -1 ] [ 1 -1 ]
		] /{ avec get } \+ =count
			1 0
			[
				[
					cur 1 ==
					count 2 >=
					count 3 <=
				] \and
					cur 0 ==
					count 3 ==
				and
			] \or
		select =cur
	} running when

	[ cur prev .xy iMouse .z ]v =gl_FragColor
;

[
	grid gl_FragCoord .xy iResolution .xy / texture2D .xyz
	1
]v =gl_FragColor

:passes
	[ 160 120 ] &grid set-dimensions
	gol =grid
;
