import bpy
import gpu
import time

# 定义图像尺寸和名称 | Define image dimensions and name
IMAGE_NAME = "CameraRenderTexture"
WIDTH = 1024
HEIGHT = 768

# 创建离屏渲染缓冲区 | Create offscreen render buffer
offscreen = gpu.types.GPUOffScreen(WIDTH, HEIGHT)

# 跟踪上次更新时间 | Track last update time
last_update_time = 0
UPDATE_INTERVAL = 1.0  # 每1秒更新一次 | Update every 1 second

def render_to_texture():
    """
    将摄像机视图渲染到图像纹理
    Render camera view to image texture
    """
    if not bpy.context.scene.camera:
        print("场景中没有活动相机! | No active camera in scene!")
        return
        
    context = bpy.context
    scene = context.scene
    
    # 获取相机视图矩阵和投影矩阵 | Get camera view matrix and projection matrix
    view_matrix = scene.camera.matrix_world.inverted()
    projection_matrix = scene.camera.calc_matrix_camera(
        context.evaluated_depsgraph_get(), x=WIDTH, y=HEIGHT)
    
    # 查找3D视图区域 | Find 3D view area
    view3d_space = None
    view3d_region = None
    
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            view3d_space = area.spaces.active
            view3d_region = area.regions[-1]
            break
    
    if not view3d_space:
        print("未找到3D视图! | 3D view not found!")
        return
    
    view3d_space.overlay.show_overlays = False
    # 绑定离屏渲染缓冲区并渲染场景 | Bind offscreen buffer and render scene
    with offscreen.bind():
        # 渲染3D视图 | Render 3D view
        offscreen.draw_view3d(
            scene,
            context.view_layer,
            view3d_space,
            view3d_region,
            view_matrix,
            projection_matrix,
            do_color_management=True)
        
        # 读取渲染结果到缓冲区 | Read render result to buffer
        buffer = gpu.state.active_framebuffer_get().read_color(
            0, 0, WIDTH, HEIGHT, 4, 0, 'UBYTE')
    
    view3d_space.overlay.show_overlays = True
    
    # 创建或获取图像以存储渲染结果 | Create or get image to store render result
    if IMAGE_NAME not in bpy.data.images:
        image = bpy.data.images.new(IMAGE_NAME, WIDTH, HEIGHT)
    else:
        image = bpy.data.images[IMAGE_NAME]
        image.scale(WIDTH, HEIGHT)
    
    # 将缓冲区数据转换为图像像素 | Convert buffer data to image pixels
    buffer.dimensions = WIDTH * HEIGHT * 4
    image.pixels = [v / 255 for v in buffer]
    
    print(f"已更新图像纹理 '{IMAGE_NAME}' | Updated image texture '{IMAGE_NAME}'")

def has_3d_view():
    """
    检查是否有3D视图
    Check if there is a 3D view
    """
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            return True
    return False

def timed_update():
    """
    定时更新函数
    Timed update function
    """
    global last_update_time
    
    current_time = time.time()
    
    # 检查时间间隔和3D视图模式 | Check time interval and 3D view mode
    if current_time - last_update_time >= UPDATE_INTERVAL and has_3d_view():
        last_update_time = current_time
        render_to_texture()
    
    # 返回时间间隔（秒），确保定时器继续运行 | Return time interval (seconds) to keep timer running
    return int(UPDATE_INTERVAL * 1)

# 清除可能存在的定时器 | Clear existing timer if any
if hasattr(bpy.app.timers, "is_registered") and bpy.app.timers.is_registered(timed_update):
    bpy.app.timers.unregister(timed_update)

# 注册定时器 | Register timer
bpy.app.timers.register(timed_update)

# 立即执行一次初始更新 | Execute initial update immediately
if has_3d_view():
    render_to_texture()
    print(f"已创建图像纹理 '{IMAGE_NAME}'，可在UV编辑器中查看或用于材质 | Created image texture '{IMAGE_NAME}', viewable in UV Editor or usable in materials")