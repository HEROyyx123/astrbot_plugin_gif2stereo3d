from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from PIL import Image, ImageSequence
import numpy as np
import io
import os
import tempfile
import aiohttp

@register("gif2stereo3d", "YourName", "将GIF图像转换为裸眼3D效果的插件", "1.0.0")
class GIF2Stereo3DPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.session = None

    async def initialize(self):
        """初始化插件"""
        # 初始化HTTP客户端会话
        self.session = aiohttp.ClientSession()
        logger.info("GIF2Stereo3D插件已加载")

    @filter.command("gif2stereo3d")
    async def gif2stereo3d(self, event: AstrMessageEvent):
        """将GIF转换为裸眼3D效果"""
        # 获取用户输入参数
        message_str = event.message_str
        args = self._parse_args(message_str)
        strength = args.get("strength", 5)
        effect = args.get("effect", "interlace")  # 默认效果为交错

        # 确保强度在合理范围内
        strength = max(1, min(10, int(strength)))

        # 验证效果类型
        if effect not in ["interlace", "anaglyph"]:
            effect = "interlace"

        # 检查是否有上传的图片
        message_chain = event.get_messages()
        image_url = None

        for msg in message_chain:
            if msg.type == "image":
                # 获取图片URL
                image_url = msg.data['url']
                break

        if image_url is None:
            # 如果没有图片，则提示用户上传
            yield event.plain_result("请上传一张GIF图片以进行3D转换。\n使用方法：发送此命令后跟一张GIF图片。\n可选参数：\n- strength=[1-10] (默认值: 5)\n- effect=[interlace|anaglyph] (默认值: interlace)")
            return

        try:
            yield event.plain_result("正在处理您上传的GIF图片，请稍候...")

            # 下载图片数据
            image_data = await self._download_image(image_url)

            # 处理GIF并转换为裸眼3D效果
            stereo_gif_data = self._convert_gif_to_stereo3d(image_data, strength, effect)

            # 创建临时文件保存结果
            with tempfile.NamedTemporaryFile(suffix='.gif', delete=False) as tmp_file:
                tmp_file.write(stereo_gif_data)
                tmp_filename = tmp_file.name

            # 发送处理后的GIF
            yield event.image_result(tmp_filename)
            yield event.plain_result(f"GIF已成功转换为裸眼3D效果！\n使用的参数: strength={strength}, effect={effect}")

            # 清理临时文件
            os.unlink(tmp_filename)

        except Exception as e:
            logger.error(f"GIF转换失败: {e}")
            yield event.plain_result(f"GIF转换失败，请确保上传的是有效的GIF图片。错误详情: {str(e)}")

    def _parse_args(self, message_str):
        """解析命令行参数"""
        args = {}
        parts = message_str.split()
        for part in parts[1:]:  # 跳过命令本身
            if '=' in part:
                key, value = part.split('=', 1)
                args[key.lower()] = value
        return args

    async def _download_image(self, url):
        """下载图片数据"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.read()
            else:
                raise Exception(f"下载图片失败，HTTP状态码: {response.status}")

    def _convert_gif_to_stereo3d(self, image_data, strength, effect):
        """
        将GIF转换为裸眼3D效果
        使用视差方法创建立体效果
        """
        # 使用Pillow打开GIF
        gif_image = Image.open(io.BytesIO(image_data))

        # 检查是否为GIF格式
        if gif_image.format != 'GIF':
            raise Exception("上传的图片不是GIF格式")

        # 创建一个新的GIF来存储结果
        frames = []
        durations = []
        disposals = []

        # 遍历每一帧
        for frame in ImageSequence.Iterator(gif_image):
            # 获取当前帧
            frame = frame.convert('RGBA')

            # 应用立体效果
            if effect == "anaglyph":
                stereo_frame = self._apply_anaglyph_effect(frame, strength)
            else:  # interlace
                stereo_frame = self._apply_interlace_effect(frame, strength)

            frames.append(stereo_frame)

            # 获取帧持续时间和处置方法
            durations.append(frame.info.get('duration', 100))
            disposals.append(frame.info.get('disposal', 2))

        # 保存处理后的GIF
        output_buffer = io.BytesIO()
        frames[0].save(
            output_buffer,
            format='GIF',
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            disposal=disposals,
            optimize=True
        )

        return output_buffer.getvalue()

    def _apply_interlace_effect(self, frame, strength):
        """
        对单个帧应用交错线立体效果
        奇数行显示左视图，偶数行显示右视图
        """
        # 调整强度参数，使其更适合像素偏移
        pixel_offset = max(1, min(10, strength // 2))

        # 将PIL图像转换为numpy数组
        frame_array = np.array(frame)
        height, width = frame_array.shape[:2]

        # 创建左右视图
        # 左视图：向左偏移
        left_view = np.zeros_like(frame_array)
        left_view[:, pixel_offset:, :] = frame_array[:, :-pixel_offset, :]

        # 右视图：向右偏移
        right_view = np.zeros_like(frame_array)
        right_view[:, :-pixel_offset, :] = frame_array[:, pixel_offset:, :]

        # 创建交替线立体效果（奇数行显示左视图，偶数行显示右视图）
        stereo_array = np.zeros_like(frame_array)
        # 奇数行 (1, 3, 5, ...)
        stereo_array[1::2, :, :] = left_view[1::2, :, :]
        # 偶数行 (0, 2, 4, ...)
        stereo_array[::2, :, :] = right_view[::2, :, :]

        # 转换回PIL图像
        stereo_frame = Image.fromarray(stereo_array.astype('uint8'), 'RGBA')

        return stereo_frame

    def _apply_anaglyph_effect(self, frame, strength):
        """
        对单个帧应用互补色立体效果（红青色立体视觉）
        """
        # 调整强度参数
        pixel_offset = max(1, min(10, strength // 2))

        # 将PIL图像转换为numpy数组
        frame_array = np.array(frame)
        height, width = frame_array.shape[:2]

        # 创建左右视图
        # 左视图：向左偏移（红色通道）
        left_view = np.zeros_like(frame_array)
        left_view[:, pixel_offset:, 0] = frame_array[:, :-pixel_offset, 0]  # 红色通道
        left_view[:, pixel_offset:, 3] = frame_array[:, :-pixel_offset, 3]  # Alpha通道

        # 右视图：向右偏移（青色通道）
        right_view = np.zeros_like(frame_array)
        right_view[:, :-pixel_offset, 1] = frame_array[:, pixel_offset:, 1]  # 绿色通道
        right_view[:, :-pixel_offset, 2] = frame_array[:, pixel_offset:, 2]  # 蓝色通道
        right_view[:, :-pixel_offset, 3] = frame_array[:, pixel_offset:, 3]  # Alpha通道

        # 合成：红色来自左视图，绿色和蓝色来自右视图
        stereo_array = np.zeros_like(frame_array)
        stereo_array[:, :, 0] = left_view[:, :, 0]  # 红色
        stereo_array[:, :, 1] = right_view[:, :, 1]  # 绿色
        stereo_array[:, :, 2] = right_view[:, :, 2]  # 蓝色
        stereo_array[:, :, 3] = np.maximum(left_view[:, :, 3], right_view[:, :, 3])  # Alpha

        # 转换回PIL图像
        stereo_frame = Image.fromarray(stereo_array.astype('uint8'), 'RGBA')

        return stereo_frame

    async def terminate(self):
        """插件终止时的清理工作"""
        # 关闭HTTP客户端会话
        if self.session:
            await self.session.close()
        logger.info("GIF2Stereo3D插件已卸载")