:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec4 uniform =iDate
;
:m time iGlobalTime ;

:m degmod ( x d ) x d deg->rad mod d deg->rad 2 / - ;

: shape ( p:vec2 -> float )
	p cart->polar =pol

	pol .x time 20 mod 10 - abs .005 * degmod =t
	1 t abs -
;

: texture ( d:float p:vec2 -> vec3 )
	[ d d d ]
;

iResolution frag->position =p
&shape p gradient p texture ->fragcolor
