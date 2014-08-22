( Constants )
:m pi 3.14159 ;
:m tau pi 2 * ;
:m eps 0.00001 ;
:m inf 10000000 ;
:m _e 2.71828 ;

( Comparators )
:m amin ( arr f )
	arr \{ ( $a $b )
		a *f b *f min =m
		a b a *f m == select
	}
;
:m amax ( arr f )
	arr \{ ( $a $b )
		a *f b *f max =m
		a b a *f m == select
	}
;
:m minmax ( $a $b ) [ a b min a b max ] ;
: smin-power ( a:float b:float k:float -> float )
	a k ** =a
    b k ** =b

    	a b * a b + /
    	1 k /
    **
;
: smin-poly ( a:float b:float k:float -> float )
	.5 .5 b a - * / + 0 1 clamp =h
		b a h mix
		[ k h 1 h - ] \*
	-
;

( Maths )
: closest-point-line ( a:vec2 b:vec2 point:vec2 -> vec2 )
	point a - =>pa
	b a - =>ba
	pa ba dot ba ba dot / 0 1 clamp =h
	ba h * a +
;
: point-distance-line ( a:vec2 b:vec2 point:vec2 -> float )
	point a b point closest-point-line - length
;
:m deg->rad pi 180 / * ;
:m rad->deg pi 180 / / ;
: rotate-2d ( c:vec2 a:float -> vec2 )
	a cos =ca
	a sin =sa

	[
		c .x ca * c .y sa * -
		c .y ca * c .x sa * +
	]
;
:m rotate-deg ( c a ) c a deg->rad rotate ;
:m ** pow ;

( Coordinate System Utilities )

: cart->polar ( p:vec2 -> vec2 ) [ p .y.x atan2 p length ] ;
: cart->logpolar ( p:vec2 -> vec2 ) [ p .y.x atan2 p length log ] ;
: polar->cart ( p:vec2 -> vec2 ) [ p .x cos p .x sin ] p .y * ;
: logpolar->cart ( p:vec2 -> vec2 ) [ p .x cos p .x sin ] _e p .y ** * ;
: polar-norm ( p:vec2 -> vec2 ) [ p .x tau + tau mod p .y ] ;

:m p+ ( p v ) p cart->polar v + polar->cart ;
:m p* ( p v ) p cart->polar v * polar->cart ;

:m frag->position ( resolution ) gl_FragCoord .xy resolution .xy / 2 * 1 - [ iResolution .x.y / 1 ] * ;

( Distance Field Utilities )
:m gradient ( p f )
	[ 0.001 0 ] =h
	p *f =>v
	[
		p h + *f  p h - *f -
		p h .yx + *f  p h .yx - *f -
	] 2 h .x * / length =>g
	v g abs /
;

( Color Operations )
: hsv->rgb ( hsv:vec3 -> vec3 )
    hsv .x 60 / [ 0 4 2 ] + 6 mod 3 - abs 1 - 0 1 clamp =>rgb
    [ 1 1 1 ] rgb hsv .y mix hsv .z *
;
