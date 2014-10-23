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
	p abs d - 0 max length
;

:m intersect \max ;
:m union \min ;
:m subtract \{ neg max } ;

:m repeat! ( p c ) p c mod .5 c * - ;
:m repeat ( f p c ) p c repeat! *f ;
:m scale ( f p s ) p s / *f s length * ;
:m rotate-cart ( f p a ) p a rotate-2d *f ;
:m rotate ( f p a ) p [ a 0 ] + polar-norm *f ;
:m translate ( f p t ) p t + *f ;
:m symmetry ( f p c ) [ p cart->polar .y.x tau c float / mod tau c float / 2 / - abs swap ] polar->cart *f ;

: distance-field ( p:vec2 -> vec4 )
	{ ( sp )
		[ sp .4 - .3 box 1 1 1 ]
	} p 6 ( mtime 10 * cos abs 99 * 1 + int ) symmetry
;

:m texture ( d p )
	p distance-field .yzw =>mat
		[ 0 0 0 ]v
		mat
		.001 d - 1000 * 0 1 clamp
	mix
;

iResolution frag->position =p
[ p { distance-field .x } gradient p texture 1 ] =gl_FragColor
