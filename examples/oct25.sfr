:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
	@vec4 uniform =iDate
;
:m gtime iGlobalTime ;

:m overlap 5 ;

: split ( p:vec2 time:float -> vec3 )
	p cart->polar =pol
	[
			pol .y 10 / time 7.1 / + sin 10 /
			pol .y 100 * sin 350 /
		+
		0
	] pol + pi 2 * mod =pol
	pol .x 60 deg->rad mod 30 deg->rad - 30 deg->rad / =dist

	0 =top
	{ dist 30 overlap + deg->rad 30 deg->rad / / =dist 1 =top }
	{
		{ dist 30 overlap - deg->rad 30 deg->rad / / =dist }
		{
				1 dist abs - 1 + dist sign neg *
				30 overlap + deg->rad 30 deg->rad /
			/ =dist
			1 =top
		} dist abs 30 overlap - deg->rad 30 deg->rad / < if
	}
	pol .x 120 deg->rad mod 60 deg->rad >= if

	[
		dist abs
		pol .y
		top
	]
;

: warp ( ip:vec3 time:float -> vec3 )
	ip [
		time 5 / ip .y + sin 10 /
			time 3.7 / ip .x + sin 100 /
			1 ip .z - 75 /
		+
		0
	] +
;

:m matunion { .x } amin ;

: shape ( to:float p:vec2 -> vec2 )
	gtime to + =time

	p time split time warp =flower

	[
		flower .y 1 flower .x 2 / - -
		flower .x
	]
;

: shape-deriv ( p:vec2 -> float )
	$[-.1:+.1:.05] !size =>len
		/{ p shape .x }
	\+ len /
;

:m petal-color [ .95 .95 0 ] ;
:m interior-color [ 1 .8 0 ] ;
:m stamen-color [ 1 1 0 ] ;

:m earth-color [ .67 .30 .05 ] ;
:m leaf-color [ .10 .39 .08 ] ;
:m stem-color [ .10 .70 .06 ] ;

: background ( p:vec2 -> vec3 )
		{ [
			stem-color
			p .x p .y + 7.1 * sin abs .3 * .7 +
			p .x 3.7 * sin abs .5 * .5 +
			p .x 57 * p .y 13 * + sin abs .1 * .9 +
			p .x 2 * .5 +
		] /abs \* }
		{ [
			[
				earth-color
				p .x p .y .3 + * sin
				p .x 3.7 * p .y -1.1 * + gtime 3.7 / + sin
			] /abs \*
			[
				leaf-color
				p .x p .y .7 * + gtime 7.9 / + sin
				p .y 3.7 * sin
			] /abs \*
		] /{ 0 1 clamp } \+ }
			p .x p .y .3 gtime 3.7 / sin .05 * + * + abs p .y 7.9 * sin .02 * + .1 <
			p .y 0 <
	and if
;

: texture ( d:float p:vec2 -> vec3 )
	{ gtime split .x } p gradient =dist
	p gtime split gtime warp =flower
	p cart->polar =pol
		{
			[
				petal-color
				d neg 500 * 0 1 clamp
				dist 90 * pol .y pol .x 79 * sin * * 1 pol .y - 20 * + sin abs .05 * .95 +
				flower .z .9 + 0 1 clamp
			] \*
			d sign 1 + 2 / p background *
		+ }
		{
				{ [
					interior-color
					.5 1 pol .y 5 * smoothstep .2 +
					pol .x 13 * sin pol .x 9 * sin * abs .1 * .9 +
				] \* }
				{ [
					stamen-color
					pol .y 137 * sin pol .x 17 * sin * abs .7 * .3 +
				] \* }
				pol .y .05 >
			if
		}
		pol .y pol .x p .x + 17 * sin .01 * .3 + >
	if
;

iResolution frag->position =p
&shape-deriv p gradient p texture ->fragcolor
