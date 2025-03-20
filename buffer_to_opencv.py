import harfang as hg
import cv2
import ctypes
import numpy as np
import math


# Initializes a render-to-texture system
def InitRenderToTexture(res, frame_buffer_name="FrameBuffer", pipeline_texture_name="tex_rb", texture_name="tex_color_ref", res_x=1024, res_y=1024):
	frame_buffer = hg.CreateFrameBuffer(res_x, res_y, hg.TF_RGBA8, hg.TF_D24, 4, frame_buffer_name)
	color = hg.GetColorTexture(frame_buffer)
	tex_color_ref = res.AddTexture(pipeline_texture_name, color)
	tex_readback = hg.CreateTexture(res_x, res_y, texture_name, hg.TF_ReadBack | hg.TF_BlitDestination, hg.TF_RGBA8)
	picture = hg.Picture(res_x, res_y, hg.PF_RGBA32)
	return frame_buffer, color, tex_color_ref, tex_readback, picture

# Converts a Harfang Picture object into an OpenCV-compatible image
def GetOpenCvImageFromPicture(picture):
	picture_width, picture_height = picture.GetWidth(), picture.GetHeight()
	picture_data = picture.GetData()
	bytes_per_pixels = 4
	data_size = picture_width * picture_height * bytes_per_pixels
	buffer = (ctypes.c_char * data_size).from_address(picture_data)
	raw_data = bytes(buffer)
	np_array = np.frombuffer(raw_data, dtype=np.uint8)
	image_rgba = np_array.reshape((picture_height, picture_width, bytes_per_pixels))
	image_bgr = cv2.cvtColor(image_rgba, cv2.COLOR_BGR2RGB)
	return image_bgr

# Detects a QR code in the given OpenCV image and draws a blue border around detected QR codes
def DetectQrCode(image):
	qrCodeDetector = cv2.QRCodeDetector()
	decodedText, points, _ = qrCodeDetector.detectAndDecode(image)

	if points is not None:
		points = points[0]
		points_int = points.astype(int)

		for i in range(len(points_int)):
			start_point = tuple(points_int[i])
			end_point = tuple(points_int[(i + 1) % len(points_int)])
			cv2.line(image, start_point, end_point, (255, 0, 0), 2)

	return decodedText, points

# Main function to initialize the rendering, scene, and OpenCV processing
def main():
	hg.InputInit()
	hg.WindowSystemInit()
	res_x, res_y = 1280, 720
	fb_res_x, fb_res_y = 256, 256
	win = hg.RenderInit('Buffer to openCV', res_x, res_y, hg.RF_VSync)
	pipeline = hg.CreateForwardPipeline()
	res = hg.PipelineResources()
	hg.AddAssetsFolder('resources_compiled')
	imgui_prg = hg.LoadProgramFromAssets('core/shader/imgui')
	imgui_img_prg = hg.LoadProgramFromAssets('core/shader/imgui_image')
	hg.ImGuiInit(10, imgui_prg, imgui_img_prg)
	scene = hg.Scene()

	keyboard = hg.Keyboard()
	mouse = hg.Mouse()

	show_open_cv_border = False
	enable_rotation = False

	show_open_cv_button_clicked = False
	enable_rotation_button_clicked = False

	# Load scene assets
	ret = hg.LoadSceneFromAssets("opencv_scene.scn", scene, res, hg.GetForwardPipelineInfo())

	# Create a simple plane model
	vtx_layout = hg.VertexLayoutPosFloatTexCoord0UInt8()
	plane_mdl = hg.CreatePlaneModel(vtx_layout, 1, 1, 1, 1)

	plane_prg = hg.LoadProgramFromAssets('shaders/texture')

	# Setup camera
	cam = scene.GetNode("Camera")
	frame_buffer, color, tex_color_ref, tex_readback, picture = InitRenderToTexture(res, res_x=fb_res_x, res_y=fb_res_y)
	cam.GetTransform().SetPos(hg.Vec3(0, 0, -2.5))
	scene.SetCurrentCamera(cam)

	# Main loop
	while not hg.ReadKeyboard().Key(hg.K_Escape) and hg.IsWindowOpen(win):
		render_was_reset, res_x, res_y = hg.RenderResetToWindow(win, res_x, res_y, hg.RF_VSync)
		keyboard.Update()
		mouse.Update()
		dt = hg.TickClock()

		scene.Update(dt)

		# Rotate the cube if enabled
		trs = scene.GetNode("cube").GetTransform()
		if enable_rotation:
			trs.SetRot(trs.GetRot() + hg.Vec3(hg.Deg(15) * hg.time_to_sec_f(dt), hg.Deg(15) * hg.time_to_sec_f(dt), 0))

		# Submit the scene for rendering
		vid, pass_ids = hg.SubmitSceneToPipeline(0, scene, hg.IntRect(0, 0, fb_res_x, fb_res_y), True, pipeline, res, frame_buffer.handle)

		hg.ImGuiBeginFrame(res_x, res_y, dt, mouse.GetState(), keyboard.GetState())


		hg.ImGuiSetNextWindowPos(hg.Vec2(10, 10))
		hg.ImGuiSetNextWindowSize(hg.Vec2(300, 400), hg.ImGuiCond_Once)

		# Apply texture to the plane model
		val_uniforms = [hg.MakeUniformSetValue('color', hg.Vec4(1, 1, 1, 1))]
		tex_uniforms = [hg.MakeUniformSetTexture('s_tex', color, 0)]

		hg.DrawModel(vid, plane_mdl, plane_prg, val_uniforms, tex_uniforms, hg.TransformationMat4(hg.Vec3(0, 0, 0), hg.Vec3(math.pi / 2, 0, math.pi)))

		hg.SetViewPerspective(vid, 0, 0, res_x, res_y, hg.TranslationMat4(hg.Vec3(0, 0.1, -1)))

		# Capture the texture and process it with OpenCV
		frame_count_capture, vid = hg.CaptureTexture(vid, res, tex_color_ref, tex_readback, picture)
		image = GetOpenCvImageFromPicture(picture)
		if image is not None:
			decoded_text, points = DetectQrCode(image)
			if(show_open_cv_border):
				image = cv2.flip(image, 1)
				cv2.imshow("Image Captured", image)

		# ImGui interface for toggling rotation and OpenCV borders
		if hg.ImGuiBegin('OpenCV infos', True, hg.ImGuiWindowFlags_NoResize | hg.ImGuiWindowFlags_NoMove):
			enable_rotation_button_clicked, enable_rotation = hg.ImGuiCheckbox("Enable Rotation", enable_rotation)
			show_open_cv_button_clicked, show_open_cv_border = hg.ImGuiCheckbox("Show OpenCV borders", show_open_cv_border)

			if decoded_text:
				hg.ImGuiText(" >> QR Code detected:")
				hg.ImGuiSameLine()
				hg.ImGuiText(decoded_text)

				hg.ImGuiSeparator()

				if points is not None:
					points_list = points.tolist()
					hg.ImGuiText(" >> QR Code Position (Corners):")
					for i, (x, y) in enumerate(points_list):
						hg.ImGuiText(f"    Corner {i + 1}: ({int(x)}, {int(y)})")

					width = int(np.linalg.norm(points[1] - points[0]))
					height = int(np.linalg.norm(points[3] - points[0]))
					hg.ImGuiText(f" >> QR Code Size: {width} x {height} pixels")

			else:
				hg.ImGuiText(" >> No QR Code Detected")

			hg.ImGuiSeparator()
		hg.ImGuiEnd()

		hg.ImGuiEndFrame(255)
		frame = hg.Frame()
		hg.UpdateWindow(win)

	cv2.waitKey(0)
	cv2.destroyAllWindows()
	hg.RenderShutdown()
	hg.DestroyWindow(win)

main()


