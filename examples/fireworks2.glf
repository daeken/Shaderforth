:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;

: rotationmat ( axis:vec3 angle:float -> mat4 )
	axis normalize =axis
	angle sin =s
	angle cos =c
	1 c - =>oc

	[
		oc axis .x * axis .x * c +           , oc axis .x * axis .y * axis .z s * - , oc axis .z * axis .x * axis .y s * + , 0
		oc axis .x * axis .y * axis .z s * + , oc axis .y * axis .y * c +           , oc axis .y * axis .z * axis .x s * - , 0
		oc axis .z * axis .x * axis .y s * - , oc axis .y * axis .z * axis .x s * + , oc axis .z * axis .z * c +           , 0
		0                                    , 0                                    , 0                                    , 1
	]m
;

:m res-scale iResolution .xy / 0.5 - 2 * [ 1 iResolution .y.x / ] * ;

:m rotate ( p axis angle ) [ p 1 ] axis angle rotationmat * .xyz ;

:m sphere ( p s ) p length s - ;
:m torus ( p t ) [ p .xy length t .x - p .z ] length t .y - ;
: box ( p:vec3 b:vec3 -> float )
	p abs b - =d
	d \max 0 min
	d 0 max length +
;
:m plane ( p n ) p n .xyz dot n .w + ;

:m union \min ;
:m hitunion \{ ( $a $b ) a b a .distance b .distance < select } ;
:m subtract \{ ( d1 d2 ) d1 neg d2 max } ;
:m intersect \max ;
:m repeat ( block p c ) p c mod 0.5 c * - *block ;

:m time iGlobalTime ;

:m x+ ( p t ) p [ t 0 0 ] + ;
:m y+ ( p t ) p [ 0 t 0 ] + ;
:m z+ ( p t ) p [ 0 0 t ] + ;

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

:m terrain ( p )
	 p .y p sin .x.z * 2 - -
;

: derive-pos ( p:vec3 v:vec3 a:vec3 t:float -> vec3 )
	p v t * +
	a 2 / t t * * +
;

:m gravity [ 0 1 0 ] ;

:m trotate [ 0.4 1.1 1.7 ] time rotate ;
: scene ( p:vec3 -> hit )
	( p trotate =p )
	[
		[ p terrain #0 ] hit
		[ p [ -5 2 0 ] [ 1 -4 0 ] gravity time 10 mod derive-pos + 30 z+ 0.25 sphere #1 ] hit
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

: get-material ( id:int pos:vec3 -> material )
	[
		#0 [ [ 0 1 0 1 ] 1 1 0 0 0  ] material
		#1 [ [ 1 0 1 1 ] .5 1 100 200 0  ] material
		   [ [ 1 1 1 1 ] 0.2 1 10 1.2 5   ] material
	] id choose
;

:m eps 0.0001 ;

:m getnormal ( p )
	[
		p eps     x+ scene .distance
		p eps neg x+ scene .distance -
		p eps     y+ scene .distance
		p eps neg y+ scene .distance -
		p eps     z+ scene .distance
		p eps neg z+ scene .distance -
	] normalize
;

iResolution frag->position =pos

3 =>focus
:m far 100 ;
:m close .1 ;

[ 0 0 5 ] =origin
[ 0 0 0 ] =>ct

ct origin - normalize =>cd
[ 0 0.5 0 ] =cu
cd cu cross =>cs
cs pos .x * cu pos .y * + cd focus * + normalize =dir

[ 0 0 0 ] =c

: shade ( cur:marched normal:vec3 level:float -> vec4 )
	cur .pos =>ray

	[ 0 8 0 ] =>lightpos
	[ 1 1 1 ] =>lightcolor
	lightpos ray - normalize =ivec
	ivec normal dot 0 max =incidence
	lightcolor incidence * =>diffuse
	0.1 =>ambient

	cur .material.pos get-material =mat

	0 =specular
	{
		ivec cur .origin + normalize normal dot
		0 max mat .specular pow
		lightpos ray - length / =specular
	} mat .specular 0 != incidence 0 > and when

	[ mat .color .rgb.a * diffuse mat .diffuse * ambient mat .ambient * + specular + * level mat .reflection pow * mat .reflection ]
;

: skip-bulk ( ray:vec3 dir:vec3 mat:int -> vec3 )
	{
		ray scene =cur
		ray dir cur .distance 0.025 max * + =ray
		{ break } cur .distance 0.01 > cur .material mat != or when
	} #100 times
	ray
;

: march ( ray:vec3 dir:vec3 -> marched )
	ray =origin
	0 =dist
	[ 0 0 0 ] =color
	1 =trans
	{
		ray scene =cur
		dist cur .distance + far min =dist
		ray dir cur .distance * + =ray

		{ break } dist far >= when

		cur .material ray get-material =mat
		{
			{ break }
			{
				ray getnormal =normal
				{
					dir normal reflect normalize =rdir
					ray dir cur .distance * + =rorigin
					rorigin dir march-one color + =color
				} mat .reflection 0 > when
				[ dist cur .distance origin ray cur .material color ] marched =>cm
				cm normal 1 shade =>shaded
				shaded .rgb trans * color + =color
				mat .color .a trans * =trans
				dir normal 1 mat .refraction / refract =dir
				ray dir cur .material skip-bulk =ray
				dir normal mat .refraction refract =dir
			} mat .refraction 0 == if
		} cur .distance close < when
	} #200 times
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
	0 =dist
	[ 0 0 0 ] =color
	{
		ray scene =cur
		dist cur .distance + far min =dist
		ray dir cur .distance * + =ray

		{ break } dist far >= when
		{ break } cur .distance close < when
	} #200 times
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

#5 =>iters
{
	float iters float / 1 swap - =level

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
		} shaded .w 0 != if
	} {
		break
	} cur .distance far < if
} iters times

[ c 1 ] =gl_FragColor
