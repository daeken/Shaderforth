:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec4 uniform =iDate
	@sampler2D uniform =back
;
:m time iGlobalTime ;

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

: arc ( p:vec2 d:vec3 -> float )
		p [ -1 1 ] * cart->polar [ pi 2 / d .z ] - polar-norm
		[
			d .x dup tau eps - - 0 1 clamp inf * +
			d .y
		]
	box
;

:m intersect \max ;
:m union \min ;
:m matintersect { .x } amax ;
:m matunion { .x } amin ;
:m subtract \{ neg max } ;

:m repeat! ( p c ) p c mod c 2 / * - ;
:m repeat ( f p c ) p c repeat! dup p swap - *f ;
:m scale ( f p s ) p s / *f s length * ;
:m rotate ( f p a ) p a rotate-2d *f ;

: distance-field ( p:vec2 -> float )
	p [ time 230 * sin time 3700 * sin ] .75 * + .1 circle
;

:m orb-color [ 1 1 1 ] ;

:m texture ( d p )
		d neg 100 * 0 1 clamp orb-color *
		( [ 0 0 0 ]
		time 173 * sin .9 >
	select )
;

: back-pixel-off ( off:vec2 -> vec3 )
		back
		gl_FragCoord .xy iResolution .xy / off +
	texture2D .rgb
;
:m back-pixel [ 0 0 ] back-pixel-off ;
:m blur-range $[-.01:+.01:.01] ;

:m persist
	blur-range multi2 /back-pixel-off \+ blur-range size dup * / .99 *
;

: orb ( -> vec3 )
	iResolution frag->position =p
	&distance-field p gradient p texture
;

: render ( -> sampler2D )
	[
		orb
		persist
	] \+ ->fragcolor
;

back-pixel ->fragcolor

:passes
	render =back
;

