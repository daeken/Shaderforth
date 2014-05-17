:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
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

:m circle ( c ) p c p-circle ;

:m intersect max ;
:m subtract neg max ;
:m union min ;
:m shape call ;

iResolution frag->position [ 1.2 -1.2 ]v * =p

: distance-field ( p:vec2 -> float )
	{
		[ 0. 0. 0.6 ]v circle
		{
			{
				[ 0. 0. 0.4 ]v circle
				{
					float 120. * =>a
					{
						[ 0.13625 -0.04 0.52221283975 ]v a rotate-deg circle
						[ -0.25375 0.135 0.464630229322 ]v a rotate-deg circle intersect
						[ -0.2925 -0.10125 0.46492270863 ]v a rotate-deg circle subtract
					} shape subtract
				} 3 mtimes
			} shape 

			{
				[ 0.0 0.18375 0.29504766564065543 ]v circle
				[ 0.0 0.18375 0.29504766564065543 ]v 120. rotate-deg circle intersect
				[ 0.0 0.18375 0.29504766564065543 ]v 240. rotate-deg circle intersect
				[ 0.0 0.0 0.0434 ]v circle subtract
			} shape subtract
		} shape subtract
	} shape ( 0. max )
;

p &distance-field gradient 100. * 0. 1. clamp =d
[ d d d 1. ]v =gl_FragColor
