# astrbot-plugin-gif2stereo3d

将GIF图像转换为裸眼3D效果的AstroBot插件。

## 功能

- 将普通GIF动画转换为具有裸眼3D效果的GIF
- 支持两种3D效果模式：
  - 交错线模式 (interlace) - 适用于大多数屏幕
  - 互补色模式 (anaglyph) - 红青色立体视觉效果
- 可调节3D效果强度

## 使用方法

在聊天中发送 `/gif2stereo3d` 命令，然后上传一张GIF图片，插件会自动将其转换为裸眼3D效果并返回结果。

## 参数

- `strength`: 3D效果强度 (默认值: 5, 范围: 1-10)
- `effect`: 3D效果类型 (默认值: interlace, 可选值: interlace, anaglyph)

示例:
- `/gif2stereo3d strength=7`
- `/gif2stereo3d effect=anaglyph`
- `/gif2stereo3d strength=8 effect=interlace`

## 效果说明

1. **交错线模式 (interlace)**:
   - 奇数行显示左视角图像
   - 偶数行显示右视角图像
   - 观看时需要将眼睛靠近屏幕或使用特殊的光栅屏

2. **互补色模式 (anaglyph)**:
   - 左眼图像使用红色通道
   - 右眼图像使用青色通道
   - 需要佩戴红青色立体眼镜观看

## 安装

确保已安装所有依赖项：
```
pip install -r requirements.txt
```

## 依赖项

- Pillow: 图像处理库
- NumPy: 数值计算库
- aiohttp: 异步HTTP客户端
- imageio: 图像序列处理库

## 注意事项

- 为了获得最佳效果，请使用清晰、对比度高的GIF图像
- 复杂背景的图像可能产生更好的3D效果
- 转换过程可能需要几秒钟，具体取决于GIF的大小和帧数