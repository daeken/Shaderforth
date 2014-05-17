:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;

:m iter 25 ;
:m iter-delta ( )
	( iGlobalTime 60.0 / sin 2.0 / 0.5 + =>v
	333.0 333.33 v mix )
	333.3333
;

:m pi 3.14159 ;
:m tau pi 2.0 * ;

: cart-polar ( p:vec2 -> vec2 ) [ p .y.x atan2 p length ]v ;
: polar-cart ( p:vec2 -> vec2 ) [ p .x cos p .x sin ]v p .y * ;
( : polar-cart ( p:vec2 -> vec2 ) [ &cos &sin ] /{ ( f ) p .x *f } avec p .y * ; )
: polar-norm ( p:vec2 -> vec2 ) [ p .x tau + tau mod p .y ]v ;

:m move ( pos t )
	[
		pos .x t 4.0 * + t sin 0.5 * +
		pos .y t sin 0.1 * +
	]v polar-norm
;

: point-distance-line ( a:vec2 b:vec2 point:vec2 -> float )
	point a - =>pa
	b a - =>ba
	pa ba dot ba length / 0.0 1.0 clamp =h
	pa ba h * - length
;

:m grad ( p f )
	[ 0.01 0.0 ]v =h
	p *f =>v
	[
		p h + *f  p h - *f -
		p h .yx + *f  p h .yx - *f -
	]v 2.0 h .x * / length =>g
	v abs g /
;

gl_FragCoord .xy iResolution .xy / 2.0 * 1.0 - cart-polar =p
iGlobalTime iter-delta * 1000.0 / =t

[ 0.0 0.5 ]v cart-polar =start
start =last

[ 0.0 0.0 0.0 ]v =color

{ ( i )
	i float iter float / =>j
	start t move =cp
		p
		{ ( bp )
				cp last bp point-distance-line
				cp polar-cart last polar-cart bp polar-cart point-distance-line
			min
		}
	grad =dist
	cp =last
	
	0.0 0.001 0.1 dist / smoothstep 10.0 * =hit
	0.0 0.001 0.1 dist / smoothstep 10.0 * =high
	[
		hit
		high t 100.0 / sin abs *
		hit 0.1 1.2 j mix *
	]v color + =color
	t iter-delta + =t
} iter times

[ color 2.0 / 1.0 ]v =gl_FragColor
