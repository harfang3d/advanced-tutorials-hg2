import math

import harfang as hg

hg.InputInit()
hg.WindowSystemInit()

res_x, res_y = 1280, 720
win = hg.RenderInit("Harfang - Shadertoy to HARFANG", res_x, res_y, hg.RF_VSync | hg.RF_MSAA4X)

vtx_layout = hg.VertexLayoutPosFloatTexCoord0UInt8()
plane_mdl = hg.CreatePlaneModel(vtx_layout, 1, 1, 1, 1)

shader = hg.LoadProgramFromFile('resources_compiled/shaders/flopine')

while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(win):
    dt = hg.TickClock()

    val_uniforms = [hg.MakeUniformSetValue("iTime", hg.Vec4(hg.time_to_sec_f(hg.GetClock()), 0.0, 0.0, 0.0))]

    viewpoint = hg.TranslationMat4(hg.Vec3(0, 0, -0.3))
    hg.SetViewPerspective(0, 0, 0, res_x, res_y, viewpoint)
 
    hg.DrawModel(0, plane_mdl, shader, val_uniforms, [], hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(-math.pi/2, 0.0, 0.0)))
    hg.Frame()
    hg.UpdateWindow(win)
    
hg.RenderShutdown()

