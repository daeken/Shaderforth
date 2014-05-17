:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;

:m grad ( p f )
	[ 0.0001 0.0 ]v =h
	p *f =>v
	[
		p h + *f p h - *f -
		p h .yx + *f p h .yx - *f -
	]v 2.0 h .x * / length =>g
	v abs g /
;

:m pi 3.14159 ;
:m deg-rad pi 180. / * ;

: cart-polar ( p:vec2 -> vec2 ) [ p .y.x atan2 p length ]v ;
: polar-cart ( p:vec2 -> vec2 ) [ p .x cos p .x sin ]v p .y * ;
:m p+ ( p v ) p cart-polar v + polar-cart ;

: rotate ( c:vec3 a:float -> vec3 )
	a deg-rad =a
	a cos =ca
	a sin =sa

	[
		c .x ca * c .y sa * -
		c .y ca * c .x sa * +
		c .z
	]v
;

:m anim
	1.0 iGlobalTime 8. mod 4.0 - abs 1. - 1.5 / 0.0 1.0 clamp 3. pow -
;

: cwarp ( c:vec3 -> vec3 )
	anim =t
	[
			c .xy 1. t - *
			[ t pi * -1. * 0. ]v
		p+
		c .z t 2.5 * 1.0 + *
	]v
;

: p-circle ( p:vec2 c:vec3 -> float )
	c cwarp =c
	c .xy p - length c .z -
;

:m circle ( c )
	p c p-circle
;

:m intersect
	max
;

:m subtract
	neg max
;

:m union
	min
;

:m shape ( f )
	*f
;

gl_FragCoord .xy iResolution .xy / 2.0 * 1.0 - [ 1.0 iResolution .y.x / neg ]v * 1.2 * =p

: frame ( p:vec2 -> float )
	{
		[ 0. 0. 0.6 ]v circle
		{
			{
				[ 0. 0. 0.4 ]v circle
				{
					float 120. * =>a
					{
						[ 0.13625 -0.04 0.52221283975 ]v a rotate circle
						[ -0.25375 0.135 0.464630229322 ]v a rotate circle intersect
						[ -0.2925 -0.10125 0.46492270863 ]v a rotate circle subtract
					} shape subtract
				} 3 mtimes
			} shape 

			{
				[ 0.0 0.18375 0.29504766564065543 ]v circle
				[ 0.0 0.18375 0.29504766564065543 ]v 120. rotate circle intersect
				[ 0.0 0.18375 0.29504766564065543 ]v 240. rotate circle intersect
				[ 0.0 0.0 0.0434 ]v circle subtract
			} shape subtract
		} shape subtract
	} shape ( 0. max )
;

p &frame grad 100. * 0. 1. clamp =d

[ d d d 1. ]v =gl_FragColor
