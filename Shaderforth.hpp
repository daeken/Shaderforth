#include <iostream>
#include <fstream>
using namespace std;

#include <png.h>

#ifdef GMP
#include <gmpxx.h>
#define float mpf_class
#else
#include <cmath>
typedef long double sfloat;
#define float sfloat
#endif

#define SF_FUNC inline __attribute__((always_inline))

typedef struct vec2 {
	float x, y;
	SF_FUNC vec2() : x(0), y(0) {}
	SF_FUNC vec2(float n) : x(n), y(n) {}
	SF_FUNC vec2(float x, float y) : x(x), y(y) {}

	SF_FUNC vec2 operator+(vec2 b) {
		return vec2(x+b.x, y+b.y);
	}
	SF_FUNC vec2 operator+(float b) {
		return vec2(x+b, y+b);
	}
	SF_FUNC vec2 operator-(vec2 b) {
		return vec2(x-b.x, y-b.y);
	}
	SF_FUNC vec2 operator-(float b) {
		return vec2(x-b, y-b);
	}
	SF_FUNC vec2 operator-() {
		return vec2(-x, -y);
	}
	SF_FUNC vec2 operator*(vec2 b) {
		return vec2(x*b.x, y*b.y);
	}
	SF_FUNC vec2 operator*(float b) {
		return vec2(x*b, y*b);
	}
	SF_FUNC vec2 operator/(vec2 b) {
		return vec2(x/b.x, y/b.y);
	}
	SF_FUNC vec2 operator/(float b) {
		return vec2(x/b, y/b);
	}

	SF_FUNC vec2 operator+=(vec2 b) {
		*this = *this + b;
		return *this;
	}
	SF_FUNC vec2 operator+=(float b) {
		*this = *this + b;
		return *this;
	}
	SF_FUNC vec2 operator-=(vec2 b) {
		*this = *this - b;
		return *this;
	}
	SF_FUNC vec2 operator-=(float b) {
		*this = *this - b;
		return *this;
	}
	SF_FUNC vec2 operator*=(vec2 b) {
		*this = *this * b;
		return *this;
	}
	SF_FUNC vec2 operator*=(float b) {
		*this = *this * b;
		return *this;
	}
	SF_FUNC vec2 operator/=(vec2 b) {
		*this = *this / b;
		return *this;
	}
	SF_FUNC vec2 operator/=(float b) {
		*this = *this / b;
		return *this;
	}
} vec2;
SF_FUNC static vec2 operator+(float n, vec2 a) {
	return vec2(n+a.x, n+a.y);
}
SF_FUNC static vec2 operator-(float n, vec2 a) {
	return vec2(n-a.x, n-a.y);
}
SF_FUNC static vec2 operator*(float n, vec2 a) {
	return vec2(n*a.x, n*a.y);
}
SF_FUNC static vec2 operator/(float n, vec2 a) {
	return vec2(n/a.x, n/a.y);
}
ostream& operator<<(ostream& os, const vec2 a) {
	os << "vec2[" << a.x << ", " << a.y << "]";
	return os;
}

typedef struct vec3 {
	float x, y, z;
	SF_FUNC vec3() : x(0), y(0), z(0) {}
	SF_FUNC vec3(float n) : x(n), y(n), z(n) {}
	SF_FUNC vec3(float x, float y, float z) : x(x), y(y), z(z) {}
	SF_FUNC vec3(vec2 a, float z) : x(a.x), y(a.y), z(z) {}
	SF_FUNC vec3(float x, vec2 a) : x(x), y(a.x), z(a.y) {}

	SF_FUNC vec3 operator+(vec3 b) {
		return vec3(x+b.x, y+b.y, z+b.z);
	}
	SF_FUNC vec3 operator+(float b) {
		return vec3(x+b, y+b, z+b);
	}
	SF_FUNC vec3 operator-(vec3 b) {
		return vec3(x-b.x, y-b.y, z-b.z);
	}
	SF_FUNC vec3 operator-(float b) {
		return vec3(x-b, y-b, z-b);
	}
	SF_FUNC vec3 operator-() {
		return vec3(-x, -y, -z);
	}
	SF_FUNC vec3 operator*(vec3 b) {
		return vec3(x*b.x, y*b.y, z*b.z);
	}
	SF_FUNC vec3 operator*(float b) {
		return vec3(x*b, y*b, z*b);
	}
	SF_FUNC vec3 operator/(vec3 b) {
		return vec3(x/b.x, y/b.y, z/b.z);
	}
	SF_FUNC vec3 operator/(float b) {
		return vec3(x/b, y/b, z/b);
	}

	SF_FUNC vec3 operator+=(vec3 b) {
		*this = *this + b;
		return *this;
	}
	SF_FUNC vec3 operator+=(float b) {
		*this = *this + b;
		return *this;
	}
	SF_FUNC vec3 operator-=(vec3 b) {
		*this = *this - b;
		return *this;
	}
	SF_FUNC vec3 operator-=(float b) {
		*this = *this - b;
		return *this;
	}
	SF_FUNC vec3 operator*=(vec3 b) {
		*this = *this * b;
		return *this;
	}
	SF_FUNC vec3 operator*=(float b) {
		*this = *this * b;
		return *this;
	}
	SF_FUNC vec3 operator/=(vec3 b) {
		*this = *this / b;
		return *this;
	}
	SF_FUNC vec3 operator/=(float b) {
		*this = *this / b;
		return *this;
	}
} vec3;
SF_FUNC static vec3 operator+(float n, vec3 a) {
	return vec3(n+a.x, n+a.y, n+a.z);
}
SF_FUNC static vec3 operator-(float n, vec3 a) {
	return vec3(n-a.x, n-a.y, n-a.z);
}
SF_FUNC static vec3 operator*(float n, vec3 a) {
	return vec3(n*a.x, n*a.y, n*a.z);
}
SF_FUNC static vec3 operator/(float n, vec3 a) {
	return vec3(n/a.x, n/a.y, n/a.z);
}
ostream& operator<<(ostream& os, const vec3 a) {
	os << "vec3[" << a.x << ", " << a.y << ", " << a.z << "]";
	return os;
}

typedef struct vec4 {
	float x, y, z, w;
	SF_FUNC vec4() : x(0), y(0), z(0), w(0) {}
	SF_FUNC vec4(float n) : x(n), y(n), z(n), w(n) {}
	SF_FUNC vec4(float x, float y, float z, float w) : x(x), y(y), z(z), w(w) {}
	SF_FUNC vec4(vec2 a, float z, float w) : x(a.x), y(a.y), z(z), w(w) {}
	SF_FUNC vec4(float x, float y, vec2 a) : x(x), y(y), z(a.x), w(a.y) {}
	SF_FUNC vec4(float x, vec2 a, float w) : x(x), y(a.x), z(a.y), w(w) {}
	SF_FUNC vec4(vec2 a, vec2 b) : x(a.x), y(a.y), z(b.x), w(b.y) {}
	SF_FUNC vec4(vec3 a, float w) : x(a.x), y(a.y), z(a.z), w(w) {}
	SF_FUNC vec4(float x, vec3 a) : x(x), y(a.x), z(a.y), w(a.z) {}

	SF_FUNC vec4 operator+(vec4 b) {
		return vec4(x+b.x, y+b.y, z+b.z, w+b.w);
	}
	SF_FUNC vec4 operator+(float b) {
		return vec4(x+b, y+b, z+b, w+b);
	}
	SF_FUNC vec4 operator-(vec4 b) {
		return vec4(x-b.x, y-b.y, z-b.z, w-b.w);
	}
	SF_FUNC vec4 operator-(float b) {
		return vec4(x-b, y-b, z-b, w-b);
	}
	SF_FUNC vec4 operator-() {
		return vec4(-x, -y, -z, -w);
	}
	SF_FUNC vec4 operator*(vec4 b) {
		return vec4(x*b.x, y*b.y, z*b.z, w*b.w);
	}
	SF_FUNC vec4 operator*(float b) {
		return vec4(x*b, y*b, z*b, w*b);
	}
	SF_FUNC vec4 operator/(vec4 b) {
		return vec4(x/b.x, y/b.y, z/b.z, w/b.w);
	}
	SF_FUNC vec4 operator/(float b) {
		return vec4(x/b, y/b, z/b, w/b);
	}

	SF_FUNC vec4 operator+=(vec4 b) {
		*this = *this + b;
		return *this;
	}
	SF_FUNC vec4 operator+=(float b) {
		*this = *this + b;
		return *this;
	}
	SF_FUNC vec4 operator-=(vec4 b) {
		*this = *this - b;
		return *this;
	}
	SF_FUNC vec4 operator-=(float b) {
		*this = *this - b;
		return *this;
	}
	SF_FUNC vec4 operator*=(vec4 b) {
		*this = *this * b;
		return *this;
	}
	SF_FUNC vec4 operator*=(float b) {
		*this = *this * b;
		return *this;
	}
	SF_FUNC vec4 operator/=(vec4 b) {
		*this = *this / b;
		return *this;
	}
	SF_FUNC vec4 operator/=(float b) {
		*this = *this / b;
		return *this;
	}
} vec4;
SF_FUNC static vec4 operator+(float n, vec4 a) {
	return vec4(n+a.x, n+a.y, n+a.z, n+a.w);
}
SF_FUNC static vec4 operator-(float n, vec4 a) {
	return vec4(n-a.x, n-a.y, n-a.z, n-a.w);
}
SF_FUNC static vec4 operator*(float n, vec4 a) {
	return vec4(n*a.x, n*a.y, n*a.z, n*a.w);
}
SF_FUNC static vec4 operator/(float n, vec4 a) {
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
	SF_FUNC vec2 func(vec2 vec) { return vec2(func(vec.x), func(vec.y)); }
#define do2_(func, other) \
	SF_FUNC vec2 func(vec2 vec, other x) { return vec2(func(vec.x, x), func(vec.y, x)); } \
	SF_FUNC vec2 func(vec2 vec, vec2 b) { return vec2(func(vec.x, b.x), func(vec.y, b.y)); }
#define do3(func) \
	SF_FUNC vec3 func(vec3 vec) { return vec3(func(vec.x), func(vec.y), func(vec.z)); }
#define do3_(func, other) \
	SF_FUNC vec3 func(vec3 vec, other x) { return vec3(func(vec.x, x), func(vec.y, x), func(vec.z, x)); } \
	SF_FUNC vec3 func(vec3 vec, vec3 b) { return vec3(func(vec.x, b.x), func(vec.y, b.y), func(vec.z, b.z)); }
#define do4(func) \
	SF_FUNC vec4 func(vec4 vec) { return vec4(func(vec.x), func(vec.y), func(vec.z), func(vec.w)); }
#define do4_(func, other) \
	SF_FUNC vec4 func(vec4 vec, other x) { return vec4(func(vec.x, x), func(vec.y, x), func(vec.z, x), func(vec.w, x)); } \
	SF_FUNC vec4 func(vec4 vec, vec4 b) { return vec4(func(vec.x, b.x), func(vec.y, b.y), func(vec.z, b.z), func(vec.w, b.w)); }

#define do_all(func) \
	do2(func); \
	do3(func); \
	do4(func);

#define do_all_(func, other) \
	do2_(func, other); \
	do3_(func, other); \
	do4_(func, other);

SF_FUNC float sf_sqrt(float a) {
	return sqrt(a);
}
do_all(sf_sqrt);
SF_FUNC float sf_inversesqrt(float a) {
	return 1 / sf_sqrt(a);
}
do_all(sf_inversesqrt);
SF_FUNC float sf_dot(vec2 a, vec2 b) {
	return a.x*b.x + a.y*b.y;
}
SF_FUNC float sf_dot(vec3 a, vec3 b) {
	return a.x*b.x + a.y*b.y + a.z*b.z;
}
SF_FUNC float sf_dot(vec4 a, vec4 b) {
	return a.x*b.x + a.y*b.y + a.z*b.z + a.w*b.w;
}
SF_FUNC float sf_length(vec2 a) {
	return sf_sqrt(sf_dot(a, a));
}
SF_FUNC float sf_length(vec3 a) {
	return sf_sqrt(sf_dot(a, a));
}
SF_FUNC float sf_length(vec4 a) {
	return sf_sqrt(sf_dot(a, a));
}

SF_FUNC vec2 sf_normalize(vec2 a) {
	return a / sf_length(a);
}
SF_FUNC vec3 sf_normalize(vec3 a) {
	return a / sf_length(a);
}
SF_FUNC vec4 sf_normalize(vec4 a) {
	return a / sf_length(a);
}

SF_FUNC vec3 sf_cross(vec3 a, vec3 b) {
	return vec3(
		a.y * b.z - a.z * b.y, 
		a.z * b.x - a.x * b.z, 
		a.x * b.y - a.y * b.x
	);
}

SF_FUNC float sf_sin(float a) {
	return sin(a);
}
do_all(sf_sin);
SF_FUNC float sf_cos(float a) {
	return cos(a);
}
do_all(sf_cos);
SF_FUNC float sf_atan(float y, float x) {
	return atan2(y, x);
}

SF_FUNC float sf_floor(float x) {
	return floor(x);
}
do_all(sf_floor);

SF_FUNC float sf_fract(float x) {
	return x - sf_floor(x);
}
do_all(sf_fract);

SF_FUNC float sf_sign(float x) {
	if(x == 0)
		return 0;
	else if(x > 0)
		return 1;
	return -1;
}

SF_FUNC float sf_mod(float a, float b) {
	return a - b * sf_floor(a / b);
}
do_all_(sf_mod, float);
SF_FUNC float sf_pow(float a, float b) {
	return pow(a, b);
}
do_all_(sf_pow, float);

SF_FUNC float sf_abs(float a) {
	return fabs(a);
}
do_all(sf_abs);

SF_FUNC float sf_log(float a) {
	return log(a);
}
do_all(sf_log);

SF_FUNC float sf_max(float a, float b) {
	return fmax(a, b);
}
do_all_(sf_max, float);
SF_FUNC float sf_min(float a, float b) {
	return fmin(a, b);
}
do_all_(sf_min, float);

SF_FUNC float sf_clamp(float x, float minval, float maxval) {
	return sf_max(sf_min(x, maxval), minval);
}
SF_FUNC vec2 sf_clamp(vec2 x, float minval, float maxval) {
	return vec2(
		sf_clamp(x.x, minval, maxval), 
		sf_clamp(x.y, minval, maxval)
	);
}
SF_FUNC vec3 sf_clamp(vec3 x, float minval, float maxval) {
	return vec3(
		sf_clamp(x.x, minval, maxval), 
		sf_clamp(x.y, minval, maxval), 
		sf_clamp(x.z, minval, maxval)
	);
}
SF_FUNC vec4 sf_clamp(vec4 x, float minval, float maxval) {
	return vec4(
		sf_clamp(x.x, minval, maxval), 
		sf_clamp(x.y, minval, maxval), 
		sf_clamp(x.z, minval, maxval), 
		sf_clamp(x.w, minval, maxval)
	);
}

SF_FUNC float sf_mix(float x, float y, float a) {
	if(a == 0) return x;
	else if(a == 1) return y;
	return x*(1-a)+y*a;
}
SF_FUNC vec2 sf_mix(vec2 x, vec2 y, float a) {
	return vec2(
		sf_mix(x.x, y.x, a), 
		sf_mix(x.y, y.y, a)
	);
}
SF_FUNC vec2 sf_mix(vec2 x, vec2 y, vec2 a) {
	return vec2(
		sf_mix(x.x, y.x, a.x), 
		sf_mix(x.y, y.y, a.y)
	);
}
SF_FUNC vec3 sf_mix(vec3 x, vec3 y, float a) {
	return vec3(
		sf_mix(x.x, y.x, a), 
		sf_mix(x.y, y.y, a), 
		sf_mix(x.z, y.z, a)
	);
}
SF_FUNC vec3 sf_mix(vec3 x, vec3 y, vec3 a) {
	return vec3(
		sf_mix(x.x, y.x, a.x), 
		sf_mix(x.y, y.y, a.y), 
		sf_mix(x.z, y.z, a.z)
	);
}
SF_FUNC vec4 sf_mix(vec4 x, vec4 y, float a) {
	return vec4(
		sf_mix(x.x, y.x, a), 
		sf_mix(x.y, y.y, a), 
		sf_mix(x.z, y.z, a), 
		sf_mix(x.w, y.w, a)
	);
}
SF_FUNC vec4 sf_mix(vec4 x, vec4 y, vec4 a) {
	return vec4(
		sf_mix(x.x, y.x, a.x), 
		sf_mix(x.y, y.y, a.y), 
		sf_mix(x.z, y.z, a.z), 
		sf_mix(x.w, y.w, a.w)
	);
}

SF_FUNC float sf_smoothstep(float edge0, float edge1, float x) {
	if(edge1 == edge0)
		return 0;
	x = sf_clamp((x - edge0)/(edge1 - edge0), 0, 1);
	return x*x*(3 - 2*x);
}
SF_FUNC vec2 sf_smoothstep(vec2 edge0, vec2 edge1, vec2 x) {
	return vec2(
		sf_smoothstep(edge0.x, edge1.x, x.x), 
		sf_smoothstep(edge0.y, edge1.y, x.y)
	);
}
SF_FUNC vec3 sf_smoothstep(vec3 edge0, vec3 edge1, vec3 x) {
	return vec3(
		sf_smoothstep(edge0.x, edge1.x, x.x), 
		sf_smoothstep(edge0.y, edge1.y, x.y), 
		sf_smoothstep(edge0.z, edge1.z, x.z)
	);
}
SF_FUNC vec4 sf_smoothstep(vec4 edge0, vec4 edge1, vec4 x) {
	return vec4(
		sf_smoothstep(edge0.x, edge1.x, x.x), 
		sf_smoothstep(edge0.y, edge1.y, x.y), 
		sf_smoothstep(edge0.z, edge1.z, x.z), 
		sf_smoothstep(edge0.w, edge1.w, x.w)
	);
}

SF_FUNC int sf_int(float v) {
	return (int) v;
}

vec4 gl_FragCoord;
vec4 gl_FragColor;

float iGlobalTime;
vec2 iResolution;

void _sf_main();

int main(int argc, char **argv) {
	if(argc != 5) {
		cout << "Usage: " << argv[0] << " width height time filename" << endl;
		return -1;
	}

	int width = atoi(argv[1]), height = atoi(argv[2]);
	
	iGlobalTime = atof(argv[3]);
	iResolution = vec2(width, height);

	unsigned char *pixels = new unsigned char[width * height * 3];
	png_byte **rows = new png_byte*[height];

	for(int i = 0, y = height - 1; y >= 0; --y) {
		rows[y] = &pixels[i];
		for(int x = 0; x < width; ++x) {
			gl_FragCoord = vec4(x, y, 0, 1);
			gl_FragColor = vec4(0, 0, 0, 0);
			_sf_main();
			pixels[i++] = sf_clamp(gl_FragColor.x, 0, 1) * 255;
			pixels[i++] = sf_clamp(gl_FragColor.y, 0, 1) * 255;
			pixels[i++] = sf_clamp(gl_FragColor.z, 0, 1) * 255;
			//pixels[i++] = sf_clamp(gl_FragColor.w, 0, 1) * 255;
		}
	}
	
	FILE *fp = fopen(argv[4], "wb");
	png_structp png_ptr = png_create_write_struct(PNG_LIBPNG_VER_STRING, NULL, NULL, NULL);
	png_infop info_ptr = png_create_info_struct(png_ptr);
	png_init_io(png_ptr, fp);

	png_set_IHDR(png_ptr, info_ptr, width, height,
		8, PNG_COLOR_TYPE_RGB, PNG_INTERLACE_NONE,
		PNG_COMPRESSION_TYPE_BASE, PNG_FILTER_TYPE_BASE);
	png_write_info(png_ptr, info_ptr);

	png_write_image(png_ptr, rows);

	png_write_end(png_ptr, NULL);
	fclose(fp);

	return 0;
}

#define main _sf_main
