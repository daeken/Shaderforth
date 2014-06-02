:globals
	@vec3 uniform =iResolution
	@vec4 uniform =iMouse
	@float uniform =iGlobalTime
	@sampler2D uniform =statebuffer
;
:m time iGlobalTime ;

:m circle ( p r )
	p length r -
;
:m box ( p d )
	p abs d - 0 max length
;
:m roundbox ( p r d )
	 p d box r - 0 max
;

:m intersect \max ;
:m union \min ;
:m subtract \{ neg max } ;

:m repeat! ( p c ) p c mod .5 c * - ;
:m repeat ( f p c ) p c repeat! dup p swap - *f ;
:m scale ( f p s ) p s / *f s * ;

:m enemy-position
	[ .85 cur .y ]v
;

:m player-position
	[ -.85 iMouse .y ]v
;

:m paddle-size [ .05 .15 ]v ;
:m ball-size [ .05 .05 ]v ;

: paddle-collide? ( ball:vec2 paddle:vec2 -> bool )
	ball paddle - abs =diff
	paddle-size ball-size + =space
	[
		diff .x space .x <
		diff .y space .y <
		ball .x abs paddle .x abs <
	] \and
;

: logic ( -> sampler2D )
	cur =ball

	{
		cur .zw =dir
		cur .xy dir + =pos
			pos player-position paddle-collide?
			pos enemy-position paddle-collide?
		or =collide
			dir
			[
				-1 1 collide select
				-1 1 1 pos .y abs - .05 <= select
			]v
		* =dir
		[ pos dir ]v
	} {
		[
			0 0
				.02
				time 375 * sin dup abs /
			*
				.01
				time 127 * sin dup abs /
			*
		]v
	} time .1 > cur .x abs 1.5 < and if =gl_FragColor
;

:m cur statebuffer [ 0 0 ]v texture2D ;

gl_FragCoord .xy iResolution .xy / .5 - 2 * =p

: distance-field ( p:vec2 -> float )
	cur =ball
	[
		p [ .01 1 ]v box
		p ball .xy + ball-size box
		p enemy-position + paddle-size box
		p player-position + paddle-size box
	] union
;

:m texture ( d )
		[ 0 0 0 1 ]v
		[ 1 1 1 1 ]v
		.001 d - 1000 * 0 1 clamp
	mix
;

p &distance-field gradient texture =gl_FragColor

:passes
	[ #2 #1 ] &statebuffer set-dimensions
	logic =statebuffer
;
