# Convert SHADERTOY shader to HARFANG® API

> In order to see if GLSL is portable in BGFX GLSL or BGFX HLSL, we decided to use a Shadertoy shader (that is using GLSL) and make it viable in HARFANG API (which is using BGFX)

In GLSL you can do this *= but not in HLSL so we are moving 

 - from this :
    ```glsl
        p.xz *= _dt;
    ```

 - to this :

    ```glsl
        p.xz = mul(_dt, p.xz);
    ```

 - or :

    ```glsl
        p.xz = p.xz * _dt;
    ```

In GLSL you can do vec2(0.2) and it declares both values of the vec2.
So we are moving 

 - from this :

    ```glsl
        myVec2 = vec2(0.2);
    ```

 - to this : 

    ```
        myVec2 = vec2(0.2, 0.2);
    ```

In GLSL you can return struct but not in HLSL.
So we are moving

 - from this :

    ```glsl
    struct obj
    {
        float d;
        vec3 cs;
        vec3 cl;
    }

    obj prim1(vec3 p)
    {
        p.x = abs(p.x)-3.;
        float per = 0.9;
        float id = round(p.y/per);
        p.xz *= rot(sin(dt(0.8,id*1.2)*TAU));
        crep(p.y, per,4.);
        mo(p.xz,vec2(0.3));
        p.x += bouncy(2.,0.)*0.8;
        float pd = box(p,vec3(1.5,0.2,0.2));
        return obj(pd,vec3(0.5,0.,0.),vec3(1.,0.5,0.9));
    }
    ```

 - to this : 

    ```glsl

    struct obj
    {
        float d;
        vec3 cs;
        vec3 cl;
    }

    obj prim1(vec3 p)
    {
        p.x = abs(p.x)-3.0;
        float per = 0.9;
        float id = round(p.y/per);
        mat2 _dt = rot(sin(dt(0.8,id*1.2)*TAU));
        p.xz = mul(_dt, p.xz); 
        crep(p.y, per,4.0);
        mo(p.xz,vec2(0.3, 0.3));
        p.x += bouncy(2.0,0.0)*0.8;
        float pd = box(p,vec3(1.5,0.2,0.2));

        obj result; 
        result.d = pd;
        result.cs = vec3(0.5, 0.0, 0.0);
        result.cl = vec3(1.0, 0.5, 0.9);
        return result;
    }
    ```

In native GLSL you can have all types of uniforms but not with BGFX GLSL or BGFX HLSL,

So we are moving 

 - from this 

    ```glsl
        uniform float x;
    ```

 - to this 

    ```glsl
        uniform vec4 (x, ~, ~, ~);
    ```

"~" are random values.