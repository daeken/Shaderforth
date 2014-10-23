:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec4 uniform =iDate
;
:m time iDate .w ;
:m mtime iGlobalTime 10 / ;

:m circle ( p r )
	p length r -
;
:m box ( p d )
	( p abs d - 0 max length )
	p abs d - =t
		t \max 0 min
		t 0 max length
	+
;
:m roundbox ( p r d )
	 p d box r -
;

:m intersect \max ;
:m union \min ;
:m subtract \{ neg max } ;

:m repeat! ( p c ) p c mod .5 c * - ;
:m repeat ( f p c ) p c repeat! *f ;
:m scale ( f p s ) p s / *f s length * ;
:m rotate-cart ( f p a ) p a rotate-2d *f ;
:m rotate ( f p a ) p [ a 0 ] + polar-norm *f ;

: distance-field ( p:vec2 -> vec4 )
	p .y mtime 10 / p .y mtime + + sin 2 * * mtime 3 * sin 1 + / =a
	{ ( tp )
		{ ( rp )
			p [ a 0 ] + rp - logpolar->cart =xp
			[
						rp
						tau 40 /
					box
						rp
						tau 40 /
					circle
					xp .y 10 * sin abs
				mix
				( [
					xp .y xp .x + 2.5 * sin ( 360 * ) abs
					xp .x 17 * sin abs
					xp .y 5.5 * sin abs
				] hsv->rgb )

					[ .92 .45 .48 ]
					( [ .62 .94 .84 ] )
					[ .83 .96 .13 ]
					xp .y 10 * sin abs
				mix
			]
		} tp tau 20 / repeat
	} p mtime - a rotate
;

:m texture ( d p )
	p distance-field .yzw =mat
	[ d neg 20 * 0 1 clamp mat * ] =c
	{ [ .24 .3 .76 ] [ 0 0 0 ] mtime 3 * sin abs mix =c } c length 0 == when
	c
;

iResolution frag->position =p
[
	p [ 0 p .x 10 * mtime 17 * cos * mtime + sin 10 / ] +
	( mtime 10 * sin 2 * abs .1 + )
] \* cart->logpolar =p
[ p { distance-field .x } gradient p texture 1 ] =gl_FragColor
