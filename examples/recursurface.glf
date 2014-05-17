:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec2 =op
;

:m pi 3.14159 ;
:m tau pi 2.0 * ;

:m amin ( arr f )
	arr \{ ( $a $b )
		a *f b *f min =m
		a b a *f m == select
	}
;

:m p+ ( p v ) p cart-polar v + polar-cart ;

:m minmax ( $a $b ) [ a b min a b max ] ;

: cart-polar ( p:vec2 -> vec2 ) [ p .y.x atan2 p length ]v ;
: polar-cart ( p:vec2 -> vec2 ) [ p .x cos p .x sin ]v p .y * ;

: point-distance-line ( a:vec2 b:vec2 point:vec2 -> float )
	point a - =>pa
	b a - =>ba
	pa ba dot ba ba dot / 0.0 1.0 clamp =h
	pa ba h * - length
;

:m grad ( p f )
	[ 0.001 0.0 ]v =h
	p *f =>v
	[
		p h + *f p h - *f -
		p h .yx + *f p h .yx - *f -
	]v 2.0 h .x * / length =>g
	v abs g /
;

: warp ( p:vec2 -> vec2 )
	p 10.0 * sin iGlobalTime sin 4.0 + 2.0 * *
;

:m pwarp ( p )
	p cart-polar [ iGlobalTime sin pi * 0.0 ]v + polar-cart iGlobalTime 5.0 / sin *
;

: surface ( p:vec2 -> float )
	p cart-polar cos polar-cart dup pwarp op point-distance-line
;

gl_FragCoord .xy iResolution .xy / 2.0 * 1.0 - [ pi 4.0 iGlobalTime 237.0 / cos * / iGlobalTime sin 0.03 * ]v p+ =op

op warp surface 2.0 / =v
op warp pwarp &surface grad 2.0 / =gv
v gv minmax \/ =r

[
	gv v r mix
	v gv r mix 0.8 *
	1.0
	1.0
]v =gl_FragColor
