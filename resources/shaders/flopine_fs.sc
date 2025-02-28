$input v_texcoord0

#include <bgfx_shader.sh>

#define PI acos(-1.0)
#define TAU 6.283581
#define ITER 80.0

#define rot(a) mat2(cos(a),sin(a),-sin(a),cos(a))
#define crep(p,c,l) p=p-c*clamp(round(p/c),-l,l)

#define dt(sp,off) frac((iTime+off)*sp)
#define bouncy(sp,off) sqrt(sin(dt(sp,off)*PI))

uniform float iTime;

struct ObjectData
{
    float d;
    vec3 cs;
    vec3 cl;
};

ObjectData minobj(ObjectData a, ObjectData b)
{
    if (a.d < b.d)
        return a;
    else
        return b;
}

float stmin(float a, float b, float k, float n)
{
    float st = k/n;
    float u = b-k;
    return min(min(a,b), 0.5*(u+a+abs(mod(u-a+st,2.*st)-st)));
}

void mo(inout vec2 p, vec2 d)
{
    p = abs(p)-d;
    if(p.y > p.x) p = p.yx;
}

float box(vec3 p, vec3 c)
{
    vec3 q = abs(p)-c;
    return min(0., max(q.x, max(q.y, q.z)))+length(max(q, 0.));
}

float sc(vec3 p, float d)
{
    p=abs(p);
    p=max(p,p.yzx);
    return min(p.x, min(p.y, p.z))-d;
}

ObjectData prim1(vec3 p)
{
    p.x = abs(p.x)-3.0;
    float per = 0.9;
    float id = round(p.y/per);
    mat2 _dt = rot(sin(dt(0.8,id*1.2)*TAU));
    p.xz = mul(_dt, p.xz); // utiliser mul a la place d'un * pour les vecteurs.
    crep(p.y, per,4.0);
    mo(p.xz,vec2(0.3, 0.3)); // déclarer les deux valeurs du vecteur
    p.x += bouncy(2.0,0.0)*0.8;
    float pd = box(p,vec3(1.5,0.2,0.2));

    ObjectData result; //briser la structure d'une struct pour la return
    result.d = pd;
    result.cs = vec3(0.5, 0.0, 0.0);
    result.cl = vec3(1.0, 0.5, 0.9);
    return result;
}

ObjectData prim2 (vec3 p)
{
    p.y = abs(p.y)-6.0;
    p.z = abs(p.z)-4.0;
    mo(p.xz, vec2(1.0, 1.0));
    vec3 pp = p;
    mo(p.yz, vec2(0.5, 0.5));
    p.y -= 0.5;
    float p2d = max(-sc(p,0.7),box(p,vec3(1.0, 1.0, 1.0)));
    p = pp;
    p2d = min(p2d, max(box(p,vec3(bouncy(2.0,0.0), bouncy(2.0,0.0), bouncy(2.0,0.0))*4.0),sc(p,0.2)));

    ObjectData result;
    result.d = p2d;
    result.cs = vec3(0.2,0.2,0.2);
    result.cl = vec3(1.0,1.0,1.0);
    return result;
}

ObjectData prim3 (vec3 p)
{
    p.z = abs(p.z)-9.0;
    float per = 0.8;
    vec2 id = round(p.xy/per)-0.5;
    float height = 1.0*bouncy(2.0,sin(length(id*0.05)));
    float p3d = box(p,vec3(2.0,2.0,0.2));
    crep(p.xy,per,2.0);
    p3d = stmin(p3d,box(p+vec3(0.0,0.0,height*0.9),vec3(0.15,0.15,height)),0.2,3.0);

    ObjectData result;
    result.d = p3d;
    result.cs = vec3(0.1,0.7,0.0);
    result.cl = vec3(1.,0.9,0.0);

    return result;
}

ObjectData prim4 (vec3 p)
{
    p.y = abs(p.y)-5.0;
    mo(p.xz, vec2(1.0, 1.0));
    float scale = 1.5;
    p *= scale;
    float per = 2.0*(bouncy(0.5,0.0));
    crep(p.xz,per,2.0);
    float p4d = max(box(p,vec3(0.9, 0.9, 0.9)),sc(p,0.25));

    ObjectData result;
    result.d = p4d/scale;
    result.cs = vec3(0.1,0.2,0.4);
    result.cl = vec3(0.1,0.8,0.9);

    return result;
}

float squared (vec3 p,float s)
{
    mo(p.zy,vec2(s, s));
    return box(p,vec3(0.2,10.0,0.2));
}

ObjectData prim5 (vec3 p)
{
    p.x = abs(p.x)-8.0;
    float id = round(p.z/7.0);
    crep(p.z,7.0,2.0);
    float scarce = 3.0;
    float p5d=1e10;
    for(int i=0;i<4; i++)
    {
        p.x += bouncy(1.0,id*0.9)*0.6;
        p5d = min(p5d,squared(p,scarce));
        p.yz = mul(rot(PI/4.0), p.yz);
        scarce -= 1.0;
    }

    ObjectData result;
    result.d = p5d;
    result.cs = vec3(0.5,0.2,0.1);
    result.cl = vec3(1.,0.9,0.1);

    return result;
}

ObjectData SDF (vec3 p)
{
    p.yz = mul(rot(-atan(1./sqrt(2.))), p.yz);
    p.xz = mul(rot(PI/4.), p.xz);

    ObjectData scene = prim1(p);
    scene = minobj(scene,prim2(p));
    scene = minobj(scene,prim3(p));
    scene = minobj(scene,prim4(p));
    scene = minobj(scene, prim5(p));
    return scene;
}

vec3 getnorm (vec3 p)
{
    vec2 eps = vec2(0.001,0.);
    return normalize(SDF(p).d-vec3(SDF(p-eps.xyy).d,SDF(p-eps.yxy).d,SDF(p-eps.yyx).d));
}

void main()
{
    vec3 ro = vec3((v_texcoord0-vec2(0.5, 0.5))*30.,-30.0),rd = vec3(0.,0.,1.),
    p = ro,
    col = vec3(0.0, 0.0, 0.0),
    l = normalize(vec3(1.0,1.4,-2.0));

    ObjectData O;
    bool hit = false;

    for (float i=0.0; i<ITER;i++)
    {
        O = SDF(p);
        if (O.d<0.001)
        {hit = true; break;}
        p += O.d*rd;
    }

    if (hit)
    {
        vec3 n = getnorm(p);
        float light = max(dot(n,l),0.);
        col = mix(O.cs,O.cl, light);
    }
    //gl_FragColor = vec4(sqrt(col),1.);
    gl_FragColor = vec4(mod(iTime, 1.0), 0.0, 0.0, 1.0);
}
