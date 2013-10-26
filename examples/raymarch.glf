:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec3 uniform =iMouse
;

: rotationmat ( axis:vec3 angle:float -> mat4 )
	axis normalize =axis
	angle sin =s
	angle cos =c
	1.0 c - =>oc

	[
		oc axis .x * axis .x * c +           , oc axis .x * axis .y * axis .z s * - , oc axis .z * axis .x * axis .y s * + , 0.0
		oc axis .x * axis .y * axis .z s * + , oc axis .y * axis .y * c +           , oc axis .y * axis .z * axis .x s * - , 0.0
		oc axis .z * axis .x * axis .y s * - , oc axis .y * axis .z * axis .x s * + , oc axis .z * axis .z * c +           , 0.0
		0.0                                  , 0.0                                  , 0.0                                  , 1.0
	]m
;

:m res-scale iResolution .xy / 0.5 - 2.0 * [ 1.0 iResolution .y.x / ]v * ;
:m mousepos iMouse .xy res-scale negate ;
:m clickpos iMouse .zw res-scale negate ;

:m rotate ( p axis angle ) [ p 1.0 ]v axis angle rotationmat * .xyz ;

:m sphere ( p s ) p length s - ;
:m torus ( p t ) [ p .xy length t .x - p .z ]v length t .y - ;
: box ( p:vec3 b:vec3 -> float )
	p abs b - =d
	d .x.y.z max max 0.0 min
	d 0.0 max length +
;
:m plane ( p n ) p n .xyz dot n .w + ;

:m union \min ;
:m hitunion \{ ( $a $b ) a b a .distance b .distance < select } ;
:m subtract \{ ( d1 d2 ) d1 negate d2 max } ;
:m intersect \max ;
:m repeat ( block p c ) p c mod 0.5 c * - *block ;

:m time iGlobalTime ;

:m tx ( p t ) p [ t   0.0 0.0 ]v + ;
:m ty ( p t ) p [ 0.0 t   0.0 ]v + ;
:m tz ( p t ) p [ 0.0 0.0 t   ]v + ;

:struct hit
	@float =distance
	@int =material
;

:struct marched
	@float =distance
	@float =obj-distance
	@vec3 =origin
	@vec3 =pos
	@int =material
	@vec3 =color
;

:m clamp-01 0.0 1.0 clamp ;

:m trotate [ 0.4 1.1 1.7 ]v time rotate ;

: scene ( p:vec3 -> hit )
	p 5.0 tz =p

	[
		[ p trotate [ 0.2 0.5 0.6 ]v + [ 0.5 0.2 ]v torus 1 ] hit
		[ p trotate [ 0.2 0.5 0.6 time sin 2.0 * + ]v + 0.25 sphere 2 ] hit
		[ p -5.0 tz trotate [ 0.3 0.3 0.3 ]v box 3 ] hit
	] hitunion
;

:struct material
	@vec4 =color
	@float =ambient
	@float =diffuse
	@float =specular
	@float =reflection
	@float =refraction
;

: get-material ( id:int -> material )
	[
		0 [ [ 1.0 1.0 1.0 1.0 ]v 0.0 1.0 500.0 0.01 2.419  ] material
		1 [ [ 1.0 0.0 0.0 0.8 ]v 0.2 0.8 30.0 0.9 1.333 ] material
		2 [ [ 0.0 1.0 0.0 1.0 ]v 0.4 0.6 30.0 1.0 0.0   ] material
		3 [ [ 1.0 1.0 1.0 1.0 ]v 0.2 1.0 10.0 1.2 2.419 ] material
		  [ [ 1.0 1.0 1.0 1.0 ]v 0.2 1.0 10.0 1.2 5.0   ] material
	] id choose
;

:m eps 0.0001 ;

:m getnormal ( p )
	[
		p eps        tx scene .distance
		p eps negate tx scene .distance -
		p eps        ty scene .distance
		p eps negate ty scene .distance -
		p eps        tz scene .distance
		p eps negate tz scene .distance -
	]v normalize
;

gl_FragCoord .xy 2.0 * iResolution .xy - iResolution .y / =pos

3.0 =>focus
:m far 20.0 ;
:m close 0.01 ;

[ 0.0 0.0 5.0 ]v =origin
[ 0.0 0.0 0.0 ]v =>ct

ct origin - normalize =>cd
[ 0.0 0.5 0.0 ]v =cu
cd cu cross =>cs
cs pos .x * cu pos .y * + cd focus * + normalize =dir

[ 0.0 0.0 0.0 ]v =c

: shade ( cur:marched normal:vec3 level:float -> vec4 )
	cur .pos =>ray

	[ 0.0 8.0 0.0 ]v =>lightpos
	[ 1.0 1.0 1.0 ]v =>lightcolor
	lightpos ray - normalize =ivec
	ivec normal dot 0.0 max =incidence
	lightcolor incidence * =>diffuse
	0.1 =>ambient

	cur .material get-material =mat

	0.0 =specular
	{
		ivec cur .origin + normalize normal dot
		0.0 max mat .specular pow
		lightpos ray - length / =specular
	} mat .specular 0.0 != incidence 0.0 > and when

	[ mat .color .rgb.a * diffuse mat .diffuse * ambient mat .ambient * + specular + * level mat .reflection pow * mat .reflection ]v
;

: skip-bulk ( ray:vec3 dir:vec3 mat:int -> vec3 )
	{
		ray scene =cur
		ray dir cur .distance 0.025 max * + =ray
		{ break } cur .distance 0.01 > cur .material mat != or when
	} 100 times
	ray
;

: march ( ray:vec3 dir:vec3 -> marched )
	ray =origin
	@hit =cur
	0.0 =dist
	[ 0.0 0.0 0.0 ]v =color
	1.0 =trans
	{
		ray scene =cur
		dist cur .distance + far min =dist
		ray dir cur .distance * + =ray

		{ break } dist far >= when

		cur .material get-material =mat
		{
			{ break }
			{
				ray getnormal =normal
				{
					dir normal reflect normalize =rdir
					ray dir cur .distance * + =rorigin
					rorigin dir march-one color + =color
				} mat .reflection 0.0 > when
				[ dist cur .distance origin ray cur .material color ] marched =>cm
				cm normal 1.0 shade =>shaded
				shaded .rgb trans * color + =color
				mat .color .a trans * =trans
				dir normal 1.0 mat .refraction / refract =dir
				ray dir cur .material skip-bulk =ray
				dir normal mat .refraction refract =dir
			} mat .refraction 0.0 == if
		} cur .distance close < when
	} 50 times
	[
		dist far cur .distance close < select
		cur .distance
		origin
		ray
		cur .material
		color
	] marched
;

: march-one ( ray:vec3 dir:vec3 -> vec3 )
	ray =origin
	@hit =cur
	0.0 =dist
	[ 0.0 0.0 0.0 ]v =color
	{
		ray scene =cur
		dist cur .distance + far min =dist
		ray dir cur .distance * + =ray

		{ break } dist far >= when
		{ break } cur .distance close < when
	} 20 times
	[
		dist far cur .distance close < select
		cur .distance
		origin
		ray
		cur .material
		color
	] marched =mcur
	{
		ray getnormal =normal
		mcur normal 0.9 shade =shaded
		shaded .rgb =color
	} cur .distance far < when
	color
;

5 =>iters
{
	float iters float / 1.0 swap - =level

	origin dir march =cur
	c cur .color + =c

	{
		cur .pos getnormal =normal
		cur normal level shade =shaded
		c shaded .rgb + =c

		{
			dir normal reflect normalize =dir
			cur .pos dir cur .obj-distance * + =origin
		} {
			break
		} shaded .w 0.0 != if
	} {
		break
	} cur .distance far < if
} iters times

[ c 1.0 ]v =gl_FragColor