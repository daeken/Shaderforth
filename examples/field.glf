:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
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

:m intersect { .x } amax ;
:m union { .x } amin ;
:m subtract \{ ( a b ) [ a .x b .x neg max a .y ]v } ;

:m repeat! ( p c ) p c mod .5 c * - ;
:m repeat ( f p c ) p c repeat! dup p swap - *f ;
:m scale ( f p s ) p s / *f [ s 1 ]v * ;

iResolution frag->position .5 / =p

: distance-field ( op:vec2 -> vec2 )
	:m wave ( v ) v 3 * time 2 * + sin .1 * ;
	:m wave-y ( v ) v wave neg .6 + ;
	op .x dup .15 repeat! - =rx
	[
		{ ( p r )
			[
				[ p 0.02 [ .025 .025 ]v roundbox 0 ]v
				[ op .y rx wave-y + 0 ]v
			] intersect
		} op [ 0 rx wave neg ]v + [ .15 .15 ]v repeat
		[
			[ op [ time .3 * sin dup wave-y time 4 * sin .1 * + ]v + .2 circle 1 ]v
			[ op .y op .x wave-y + 0 ]v
		] subtract
	] union [ eps 0 ]v -
;

:m material ( id p d )
	[
		0 [ [ 179 .814 .847 p .y + .3 + time p .x 3. * + cos .05 * + ]v hsv->rgb 1 ]v
		1 [ [ 299 93 255 / .2 d - 5 * dup * .4 * ]v hsv->rgb 1 ]v
		2 [ 0 0 1 1 ]v
		[ 1 0 1 1 ]v
	] id choose
;

: texture ( p:vec2 d:float -> vec4 )
		[ .06 .04 .11 1 ]v
		p distance-field .y p d material
		.01 d - 100 * 0 1 clamp
	mix 
;

	p
	p { distance-field .x } gradient
texture =gl_FragColor
