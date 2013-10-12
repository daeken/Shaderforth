:globals
	@vec3 uniform =iResolution
	@float uniform =iGlobalTime
;

gl_FragCoord .xyz iResolution / 0.5 - iGlobalTime 10.0 / sin abs * 50.0 * =p
p length iGlobalTime + sin =d
p .y.x / atan iGlobalTime + d iGlobalTime + sin + 3.1416 3. / mod 3. * sin =a
a d + =v
p length 4. * a iGlobalTime + - sin =m
a negate =>-a
v negate m d negate sin * iGlobalTime .1 * + sin *
v m * -a sin tan -a 3. * sin * 3. * iGlobalTime .5 * + sin *
v m mod
iGlobalTime
vec4 =gl_FragColor
