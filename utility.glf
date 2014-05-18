( Constants )
:m pi 3.14159 ;
:m tau pi 2.0 * ;

( Comparators )
:m amin ( arr f )
	arr \{ ( $a $b )
		a *f b *f min =m
		a b a *f m == select
	}
;
:m minmax ( $a $b ) [ a b min a b max ] ;

( Maths )
: closest-point-line ( a:vec2 b:vec2 point:vec2 -> vec2 )
	point a - =>pa
	b a - =>ba
	pa ba dot ba ba dot / 0.0 1.0 clamp =h
	ba h * a +
;
: point-distance-line ( a:vec2 b:vec2 point:vec2 -> float )
	point a b point closest-point-line - length
;
:m deg->rad pi 180. / * ;
:m rad->deg pi 180. / / ;
: rotate ( c:vec3 a:float -> vec3 )
	a cos =ca
	a sin =sa

	[
		c .x ca * c .y sa * -
		c .y ca * c .x sa * +
		c .z
	]v
;
:m rotate-deg ( c a ) c a deg->rad rotate ;

( Coordinate System Utilities )

: cart->polar ( p:vec2 -> vec2 ) [ p .y.x atan2 p length ]v ;
: polar->cart ( p:vec2 -> vec2 ) [ p .x cos p .x sin ]v p .y * ;
: polar-norm ( p:vec2 -> vec2 ) [ p .x tau + tau mod p .y ]v ;

:m p+ ( p v ) p cart->polar v + polar->cart ;
:m p* ( p v ) p cart->polar v * polar->cart ;

:m frag->position ( resolution ) gl_FragCoord .xy resolution .xy / 2.0 * 1.0 - [ 1.0 iResolution .y.x / ]v * ;

( Distance Field Utilities )
:m gradient ( p f )
	[ 0.001 0.0 ]v =h
	p *f =>v
	[
		p h + *f  p h - *f -
		p h .yx + *f  p h .yx - *f -
	]v 2.0 h .x * / length =>g
	v abs g /
;

( Color Operations )
: hsv->rgb ( hsv:vec3 -> vec3 )
    hsv .x 60.0 / [ 0. 4. 2. ]v + 6. mod 3. - abs 1. - 0.0 1.0 clamp =>rgb
    [ 1. 1. 1. ]v rgb hsv .y mix hsv .z *
;
