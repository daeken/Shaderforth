:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec2 =op
;

: warp ( p:vec2 -> vec2 )
	p 10 * sin iGlobalTime sin 4 + 2 * *
;

:m pwarp ( p )
	p cart->polar [ iGlobalTime sin pi * 0 ]v + polar->cart iGlobalTime 5 / sin *
;

: surface ( p:vec2 -> float )
	p cart->polar cos polar->cart dup pwarp op point-distance-line
;

iResolution frag->position 1 - [ pi 4 iGlobalTime 237 / cos * / iGlobalTime sin 0.03 * ]v p+ =op

op warp surface 2 / =v
op warp pwarp &surface gradient 2 / =gv
v gv minmax \/ =r

[
	gv v r mix
	v gv r mix 0.8 *
	1
	1
]v =gl_FragColor
