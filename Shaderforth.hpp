#include <iostream>
using namespace std;

#ifdef GMP
#include <gmpxx.h>
#define float mpf_class
#else
#include <cmath>
#define float long double
#endif

typedef struct vec2 {
	float x, y;
	vec2() : x(0), y(0) {}
	vec2(float n) : x(n), y(n) {}
	vec2(float x, float y) : x(x), y(y) {}

	vec2 operator+(vec2 b) {
		return vec2(x+b.x, y+b.y);
	}
	vec2 operator+(float b) {
		return vec2(x+b, y+b);
	}
	vec2 operator-(vec2 b) {
		return vec2(x-b.x, y-b.y);
	}
	vec2 operator-(float b) {
		return vec2(x-b, y-b);
	}
	vec2 operator-() {
		return vec2(-x, -y);
	}
	vec2 operator*(vec2 b) {
		return vec2(x*b.x, y*b.y);
	}
	vec2 operator*(float b) {
		return vec2(x*b, y*b);
	}
	vec2 operator/(vec2 b) {
		return vec2(x/b.x, y/b.y);
	}
	vec2 operator/(float b) {
		return vec2(x/b, y/b);
	}

	vec2 operator+=(vec2 b) {
		*this = *this + b;
		return *this;
	}
	vec2 operator+=(float b) {
		*this = *this + b;
		return *this;
	}
	vec2 operator-=(vec2 b) {
		*this = *this - b;
		return *this;
	}
	vec2 operator-=(float b) {
		*this = *this - b;
		return *this;
	}
	vec2 operator*=(vec2 b) {
		*this = *this * b;
		return *this;
	}
	vec2 operator*=(float b) {
		*this = *this * b;
		return *this;
	}
	vec2 operator/=(vec2 b) {
		*this = *this / b;
		return *this;
	}
	vec2 operator/=(float b) {
		*this = *this / b;
		return *this;
	}
} vec2;
static vec2 operator+(float n, vec2 a) {
	return vec2(n+a.x, n+a.y);
}
static vec2 operator-(float n, vec2 a) {
	return vec2(n-a.x, n-a.y);
}
static vec2 operator*(float n, vec2 a) {
	return vec2(n*a.x, n*a.y);
}
static vec2 operator/(float n, vec2 a) {
	return vec2(n/a.x, n/a.y);
}
ostream& operator<<(ostream& os, const vec2 a) {
	os << "vec2[" << a.x << ", " << a.y << "]";
	return os;
}

typedef struct vec3 {
	float x, y, z;
	vec3() : x(0), y(0), z(0) {}
	vec3(float n) : x(n), y(n), z(n) {}
	vec3(float x, float y, float z) : x(x), y(y), z(z) {}
	vec3(vec2 a, float z) : x(a.x), y(a.y), z(z) {}
	vec3(float x, vec2 a) : x(x), y(a.x), z(a.y) {}

	vec3 operator+(vec3 b) {
		return vec3(x+b.x, y+b.y, z+b.z);
	}
	vec3 operator+(float b) {
		return vec3(x+b, y+b, z+b);
	}
	vec3 operator-(vec3 b) {
		return vec3(x-b.x, y-b.y, z-b.z);
	}
	vec3 operator-(float b) {
		return vec3(x-b, y-b, z-b);
	}
	vec3 operator-() {
		return vec3(-x, -y, -z);
	}
	vec3 operator*(vec3 b) {
		return vec3(x*b.x, y*b.y, z*b.z);
	}
	vec3 operator*(float b) {
		return vec3(x*b, y*b, z*b);
	}
	vec3 operator/(vec3 b) {
		return vec3(x/b.x, y/b.y, z/b.z);
	}
	vec3 operator/(float b) {
		return vec3(x/b, y/b, z/b);
	}

	vec3 operator+=(vec3 b) {
		*this = *this + b;
		return *this;
	}
	vec3 operator+=(float b) {
		*this = *this + b;
		return *this;
	}
	vec3 operator-=(vec3 b) {
		*this = *this - b;
		return *this;
	}
	vec3 operator-=(float b) {
		*this = *this - b;
		return *this;
	}
	vec3 operator*=(vec3 b) {
		*this = *this * b;
		return *this;
	}
	vec3 operator*=(float b) {
		*this = *this * b;
		return *this;
	}
	vec3 operator/=(vec3 b) {
		*this = *this / b;
		return *this;
	}
	vec3 operator/=(float b) {
		*this = *this / b;
		return *this;
	}
} vec3;
static vec3 operator+(float n, vec3 a) {
	return vec3(n+a.x, n+a.y, n+a.z);
}
static vec3 operator-(float n, vec3 a) {
	return vec3(n-a.x, n-a.y, n-a.z);
}
static vec3 operator*(float n, vec3 a) {
	return vec3(n*a.x, n*a.y, n*a.z);
}
static vec3 operator/(float n, vec3 a) {
	return vec3(n/a.x, n/a.y, n/a.z);
}
ostream& operator<<(ostream& os, const vec3 a) {
	os << "vec3[" << a.x << ", " << a.y << ", " << a.z << "]";
	return os;
}

typedef struct vec4 {
	float x, y, z, w;
	vec4() : x(0), y(0), z(0), w(0) {}
	vec4(float n) : x(n), y(n), z(n), w(n) {}
	vec4(float x, float y, float z, float w) : x(x), y(y), z(z), w(w) {}
	vec4(vec2 a, float z, float w) : x(a.x), y(a.y), z(z), w(w) {}
	vec4(float x, float y, vec2 a) : x(x), y(y), z(a.x), w(a.y) {}
	vec4(float x, vec2 a, float w) : x(x), y(a.x), z(a.y), w(w) {}
	vec4(vec2 a, vec2 b) : x(a.x), y(a.y), z(b.x), w(b.y) {}
	vec4(vec3 a, float w) : x(a.x), y(a.y), z(a.z), w(w) {}
	vec4(float x, vec3 a) : x(x), y(a.x), z(a.y), w(a.z) {}

	vec4 operator+(vec4 b) {
		return vec4(x+b.x, y+b.y, z+b.z, w+b.w);
	}
	vec4 operator+(float b) {
		return vec4(x+b, y+b, z+b, w+b);
	}
	vec4 operator-(vec4 b) {
		return vec4(x-b.x, y-b.y, z-b.z, w-b.w);
	}
	vec4 operator-(float b) {
		return vec4(x-b, y-b, z-b, w-b);
	}
	vec4 operator-() {
		return vec4(-x, -y, -z, -w);
	}
	vec4 operator*(vec4 b) {
		return vec4(x*b.x, y*b.y, z*b.z, w*b.w);
	}
	vec4 operator*(float b) {
		return vec4(x*b, y*b, z*b, w*b);
	}
	vec4 operator/(vec4 b) {
		return vec4(x/b.x, y/b.y, z/b.z, w/b.w);
	}
	vec4 operator/(float b) {
		return vec4(x/b, y/b, z/b, w/b);
	}

	vec4 operator+=(vec4 b) {
		*this = *this + b;
		return *this;
	}
	vec4 operator+=(float b) {
		*this = *this + b;
		return *this;
	}
	vec4 operator-=(vec4 b) {
		*this = *this - b;
		return *this;
	}
	vec4 operator-=(float b) {
		*this = *this - b;
		return *this;
	}
	vec4 operator*=(vec4 b) {
		*this = *this * b;
		return *this;
	}
	vec4 operator*=(float b) {
		*this = *this * b;
		return *this;
	}
	vec4 operator/=(vec4 b) {
		*this = *this / b;
		return *this;
	}
	vec4 operator/=(float b) {
		*this = *this / b;
		return *this;
	}
} vec4;
static vec4 operator+(float n, vec4 a) {
	return vec4(n+a.x, n+a.y, n+a.z, n+a.w);
}
static vec4 operator-(float n, vec4 a) {
	return vec4(n-a.x, n-a.y, n-a.z, n-a.w);
}
static vec4 operator*(float n, vec4 a) {
	return vec4(n*a.x, n*a.y, n*a.z, n*a.w);
}
static vec4 operator/(float n, vec4 a) {
	return vec4(n/a.x, n/a.y, n/a.z, n/a.w);
}
ostream& operator<<(ostream& os, const vec4 a) {
	os << "vec4[" << a.x << ", " << a.y << ", " << a.z << ", " << a.w << "]";
	return os;
}

#define sf_vec2 vec2
#define sf_vec3 vec3
#define sf_vec4 vec4

#define do2(func) \
	vec2 func(vec2 vec) { return vec2(func(vec.x), func(vec.y)); }
#define do2_(func, other) \
	vec2 func(vec2 vec, other x) { return vec2(func(vec.x, x), func(vec.y, x)); } \
	vec2 func(vec2 vec, vec2 b) { return vec2(func(vec.x, b.x), func(vec.y, b.y)); }
#define do3(func) \
	vec3 func(vec3 vec) { return vec3(func(vec.x), func(vec.y), func(vec.z)); }
#define do3_(func, other) \
	vec3 func(vec3 vec, other x) { return vec3(func(vec.x, x), func(vec.y, x), func(vec.z, x)); } \
	vec3 func(vec3 vec, vec3 b) { return vec3(func(vec.x, b.x), func(vec.y, b.y), func(vec.z, b.z)); }
#define do4(func) \
	vec4 func(vec4 vec) { return vec4(func(vec.x), func(vec.y), func(vec.z), func(vec.w)); }
#define do4_(func, other) \
	vec4 func(vec4 vec, other x) { return vec4(func(vec.x, x), func(vec.y, x), func(vec.z, x), func(vec.w, x)); } \
	vec4 func(vec4 vec, vec4 b) { return vec4(func(vec.x, b.x), func(vec.y, b.y), func(vec.z, b.z), func(vec.w, b.w)); }

#define do_all(func) \
	do2(func); \
	do3(func); \
	do4(func);

#define do_all_(func, other) \
	do2_(func, other); \
	do3_(func, other); \
	do4_(func, other);

float sf_sqrt(float a) {
	return sqrt(a);
}
do_all(sf_sqrt);
float sf_inversesqrt(float a) {
	return 1 / sf_sqrt(a);
}
do_all(sf_inversesqrt);
float sf_dot(vec2 a, vec2 b) {
	return a.x*b.x + a.y*b.y;
}
float sf_dot(vec3 a, vec3 b) {
	return a.x*b.x + a.y*b.y + a.z*b.z;
}
float sf_dot(vec4 a, vec4 b) {
	return a.x*b.x + a.y*b.y + a.z*b.z + a.w*b.w;
}
float sf_length(vec2 a) {
	return sf_sqrt(sf_dot(a, a));
}
float sf_length(vec3 a) {
	return sf_sqrt(sf_dot(a, a));
}
float sf_length(vec4 a) {
	return sf_sqrt(sf_dot(a, a));
}

vec2 sf_normalize(vec2 a) {
	return a / sf_length(a);
}
vec3 sf_normalize(vec3 a) {
	return a / sf_length(a);
}
vec4 sf_normalize(vec4 a) {
	return a / sf_length(a);
}

vec3 sf_cross(vec3 a, vec3 b) {
	return vec3(
		a.y * b.z - a.z * b.y, 
		a.z * b.x - a.x * b.z, 
		a.x * b.y - a.y * b.x
	);
}

float sf_sin(float a) {
	return sin(a);
}
do_all(sf_sin);
float sf_cos(float a) {
	return cos(a);
}
do_all(sf_cos);
float sf_atan(float y, float x) {
	return atan2(y, x);
}

float sf_floor(float x) {
	return floor(x);
}
do_all(sf_floor);

float sf_fract(float x) {
	return x - sf_floor(x);
}
do_all(sf_fract);

float sf_sign(float x) {
	if(x == 0)
		return 0;
	else if(x > 0)
		return 1;
	return -1;
}

float sf_mod(float a, float b) {
	return a - b * sf_floor(a / b);
}
do_all_(sf_mod, float);
float sf_pow(float a, float b) {
	return pow(a, b);
}
do_all_(sf_pow, float);

float sf_abs(float a) {
	return fabs(a);
}
do_all(sf_abs);

float sf_log(float a) {
	return log(a);
}
do_all(sf_log);

float sf_max(float a, float b) {
	return fmax(a, b);
}
do_all_(sf_max, float);
float sf_min(float a, float b) {
	return fmin(a, b);
}
do_all_(sf_min, float);

float sf_clamp(float x, float minval, float maxval) {
	return sf_max(sf_min(x, maxval), minval);
}
vec2 sf_clamp(vec2 x, float minval, float maxval) {
	return vec2(
		sf_clamp(x.x, minval, maxval), 
		sf_clamp(x.y, minval, maxval)
	);
}
vec3 sf_clamp(vec3 x, float minval, float maxval) {
	return vec3(
		sf_clamp(x.x, minval, maxval), 
		sf_clamp(x.y, minval, maxval), 
		sf_clamp(x.z, minval, maxval)
	);
}
vec4 sf_clamp(vec4 x, float minval, float maxval) {
	return vec4(
		sf_clamp(x.x, minval, maxval), 
		sf_clamp(x.y, minval, maxval), 
		sf_clamp(x.z, minval, maxval), 
		sf_clamp(x.w, minval, maxval)
	);
}

float sf_mix(float x, float y, float a) {
	if(a == 0) return x;
	else if(a == 1) return y;
	return x*(1-a)+y*a;
}
vec2 sf_mix(vec2 x, vec2 y, float a) {
	return vec2(
		sf_mix(x.x, y.x, a), 
		sf_mix(x.y, y.y, a)
	);
}
vec2 sf_mix(vec2 x, vec2 y, vec2 a) {
	return vec2(
		sf_mix(x.x, y.x, a.x), 
		sf_mix(x.y, y.y, a.y)
	);
}
vec3 sf_mix(vec3 x, vec3 y, float a) {
	return vec3(
		sf_mix(x.x, y.x, a), 
		sf_mix(x.y, y.y, a), 
		sf_mix(x.z, y.z, a)
	);
}
vec3 sf_mix(vec3 x, vec3 y, vec3 a) {
	return vec3(
		sf_mix(x.x, y.x, a.x), 
		sf_mix(x.y, y.y, a.y), 
		sf_mix(x.z, y.z, a.z)
	);
}
vec4 sf_mix(vec4 x, vec4 y, float a) {
	return vec4(
		sf_mix(x.x, y.x, a), 
		sf_mix(x.y, y.y, a), 
		sf_mix(x.z, y.z, a), 
		sf_mix(x.w, y.w, a)
	);
}
vec4 sf_mix(vec4 x, vec4 y, vec4 a) {
	return vec4(
		sf_mix(x.x, y.x, a.x), 
		sf_mix(x.y, y.y, a.y), 
		sf_mix(x.z, y.z, a.z), 
		sf_mix(x.w, y.w, a.w)
	);
}

float sf_smoothstep(float edge0, float edge1, float x) {
	if(edge1 == edge0)
		return 0;
	x = sf_clamp((x - edge0)/(edge1 - edge0), 0, 1);
	return x*x*(3 - 2*x);
}
vec2 sf_smoothstep(vec2 edge0, vec2 edge1, vec2 x) {
	return vec2(
		sf_smoothstep(edge0.x, edge1.x, x.x), 
		sf_smoothstep(edge0.y, edge1.y, x.y)
	);
}
vec3 sf_smoothstep(vec3 edge0, vec3 edge1, vec3 x) {
	return vec3(
		sf_smoothstep(edge0.x, edge1.x, x.x), 
		sf_smoothstep(edge0.y, edge1.y, x.y), 
		sf_smoothstep(edge0.z, edge1.z, x.z)
	);
}
vec4 sf_smoothstep(vec4 edge0, vec4 edge1, vec4 x) {
	return vec4(
		sf_smoothstep(edge0.x, edge1.x, x.x), 
		sf_smoothstep(edge0.y, edge1.y, x.y), 
		sf_smoothstep(edge0.z, edge1.z, x.z), 
		sf_smoothstep(edge0.w, edge1.w, x.w)
	);
}

vec4 gl_FragCoord;
vec4 gl_FragColor;

float iGlobalTime;
vec2 iResolution;

void _sf_main();

int main(int argc, char **argv) {
	int width = 1920, height = 1080;
	
	iGlobalTime = 7.146;
	iResolution = vec2(width, height);

	unsigned char *pixels = new unsigned char[width * height * 4];

	int i = 0;
	for(int y = height - 1; y >= 0; --y) {
		for(int x = 0; x < width; ++x) {
			gl_FragCoord = vec4(x, y, 0, 1);
			gl_FragColor = vec4(0, 0, 0, 0);
			_sf_main();
			pixels[i++] = sf_clamp(gl_FragColor.x, 0, 1) * 255;
			pixels[i++] = sf_clamp(gl_FragColor.y, 0, 1) * 255;
			pixels[i++] = sf_clamp(gl_FragColor.z, 0, 1) * 255;
			pixels[i++] = sf_clamp(gl_FragColor.w, 0, 1) * 255;
		}
	}

	cout << width << endl;
	cout << height << endl;
	for(int x = 0; x < width * height * 4; ++x)
		cout << (int) pixels[x] << endl;

	return 0;
}

#define main _sf_main
