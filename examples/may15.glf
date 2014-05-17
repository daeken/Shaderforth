:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec2 =op
	@vec3 =fragcolor
	@float =time
;

:m pi 3.14159 ;
:m tau pi 2.0 * ;

:m ~= - abs 0.01 <= ;
:m !~= - abs 0.01 > ;

:m p+ ( p v ) p cart-polar v + polar-cart ;
:m p* ( p v ) p cart-polar v * polar-cart ;

:m minmax ( $a $b ) [ a b min a b max ] ;

: cart-polar ( p:vec2 -> vec2 ) [ p .y.x atan2 p length ]v ;
: polar-cart ( p:vec2 -> vec2 ) [ p .x cos p .x sin ]v p .y * ;

: closest-point-line ( a:vec2 b:vec2 point:vec2 -> vec2 )
	point a - =>pa
	b a - =>ba
	pa ba dot ba ba dot / 0.0 1.0 clamp =h
	ba h * a +
;

:m closest-point-line-polar ( a b point )
		a cart-polar
		b cart-polar
		point cart-polar
	closest-point-line polar-cart
;

: point-distance-line ( a:vec2 b:vec2 point:vec2 -> float )
	point a b point closest-point-line - length
;

: hsv-rgb ( hsv:vec3 -> vec3 )
    hsv .x 60.0 / [ 0. 4. 2. ]v + 6. mod 3. - abs 1. - 0.0 1.0 clamp =>rgb
    [ 1. 1. 1. ]v rgb hsv .y mix hsv .z *
;

: derive-pos ( p:vec2 v:vec2 a:vec2 t:float -> vec2 )
	p v t * +
	a 2. / t t * * +
;

:m gravity [ 0.0 -0.3 ]v ;

:m noise ( s )
	time 100.0 * s 211.0 * + gl_FragCoord .x 1489.0 * cos gl_FragCoord .y 1979.0 * cos + * sin 1.0 + 2.0 /
;

: smoke-trail ( ltime:float duration:float origin:vec2 fp:vec2 )
	[ ltime gl_FragCoord .x + 1187. * sin ltime gl_FragCoord .y + 1447. * sin ]v 10.0 / dup noise * =off
	origin fp op off - closest-point-line =lp
	lp op - length =d
	1.0 lp fp - length origin fp - length / -
	lp fp - length 0.0 0.1 clamp 30.0 * *
		1.0 time ltime - duration / 0.0 1.0 clamp - 3.0 *
		1.0
	duration 0.0 != select * =r

	off length noise 0.3 * 1.0 + =gn
	0.1 d - 0.0 1.0 clamp 5.0 / r * gn * 0.0 1.0 clamp =grey
	[ grey dup dup ]v fragcolor + =fragcolor
;

: spark ( ltime:float origin:vec2 vel:vec2 dur:float color:vec3 dia:float )
	time ltime - =t
	origin vel gravity t derive-pos =fp

	vel origin + length noise =>n

	dia fp op - length - 900. dia * * =d
	{
		d color 2.0 1.5 n - * * *
		dur t - 3.0 * 0.0 1.0 clamp *
		fragcolor + =fragcolor
	} d 0.0 > dur t > and when

		ltime
			10.0
			3.0
		dur 100.0 == select
		origin
		fp
	smoke-trail
;

:m shape ( ltime:float origin:vec2 vel:vec2 spokes:int color:vec3 )
	spokes float =fs
	tau fs / =ai

	{ ( i )
		{ break } i spokes == when
			ltime
			origin
			[
				i float ai * ltime +
				0.4 ltime 2179. * i 1 + float 2287.0 * ltime + sin 100.0 * + sin 0.03 * +
			]v polar-cart
			ltime 571.0 * sin 0.5 * 3.0 +
			color
			0.03
		spark
	} 10 times

	{
		[ ltime gl_FragCoord .x + 1187. * sin ltime gl_FragCoord .y + 1447. * sin ]v 10.0 / dup noise * =off
		1.0 origin op - off - length - 0.0 1.0 clamp 15.0 / 2.0 time ltime - - * off length noise * =grey
		[ grey dup dup ]v fragcolor + =fragcolor
	} time ltime - 2.0 <= when
;

: firework ( ltime:float origin:vec2 xvel:float spokes:int color:vec3 )
	3.0 =fuse
	ltime 389.0 * sin 0.03 * 1.1 + =speed

	[ xvel speed ]v =vel

	time ltime - =>t

		{ ltime origin vel 100.0 color 0.03 spark }
		{
			origin vel gravity fuse t min derive-pos =fp
			ltime 6.0 origin fp smoke-trail
			ltime fuse + fp vel spokes color shape
		}
	t fuse <= if

	{
		fragcolor color 2.0 / 0.2 t fuse - - * + =fragcolor
	} t fuse - 0.2 <= t fuse >= and when 
;

gl_FragCoord .xy iResolution .xy / dup =np 2.0 * 1.0 - 1.5 * [ 1.0 iResolution .y.x / ]v * =op

[ 0. 0. 0. ]v =fragcolor

:m steps 3.0 ;
:m buffertime 10.0 ;

: frame ( to:float )
	iGlobalTime to + =time
	{ ( i )
		i float steps / time floor buffertime - + =it

		{
				it
				[ it 11. * sin 0.25 * -1.5 ]v
				it 19. * sin 0.1 *
				5.0 it 2311. * sin 1.0 + 5.0 2.0 / * + int
				[
					it 197. * 360. mod
					it 2267. * sin abs
					0.8
				]v hsv-rgb
			firework
		} it 1493. * sin 0.95 > it 0.0 >= and when
	} steps buffertime * int times
;

0.0 frame

[
	fragcolor
	[ 29. 255. / 8. 255. / 64. 255. / ]v np .x iGlobalTime 10.0 / + sin 0.1 * 1.0 + *
	[ 0.0 0.0 0.0 ]v
	1.0 np .y dup * - mix +
	1.0
]v
 =gl_FragColor
