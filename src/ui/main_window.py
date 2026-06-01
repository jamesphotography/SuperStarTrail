"""
主窗口模块

应用程序的主界面
"""

from pathlib import Path
from typing import List, Optional
from threading import Event
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QMessageBox,
    QApplication,
    QAction,
    QSplitter,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon
import numpy as np

from core.raw_processor import RawProcessor
from core.cancellation import ProcessingCancelledError
from core.stacking_engine import StackingEngine, StackMode
from utils.logger import setup_logger
from utils.settings import get_settings
from utils.file_naming import FileNamingService
from ui.dialogs import AboutDialog, PreferencesDialog
from ui.panels import FileListPanel, ParametersPanel, ControlPanel, PreviewPanel
from i18n import get_translator, set_language
from ui.styles import get_complete_stylesheet

logger = setup_logger(__name__)


class PreviewThread(QThread):
    """单文件预览线程 —— 避免 RAW 解码阻塞主线程（C6）"""

    preview_ready = pyqtSignal(np.ndarray, object)  # (image, file_path)
    preview_error = pyqtSignal(str, object)          # (error_msg, file_path)

    def __init__(self, file_path: Path, raw_params: dict, rotation: int = 0):
        super().__init__()
        self.file_path = file_path
        self.raw_params = raw_params
        self.rotation = rotation

    def run(self):
        try:
            from core.raw_processor import RawProcessor
            processor = RawProcessor()
            img = processor.process(
                self.file_path, apply_exif_rotation=True,
                rotation=self.rotation, **self.raw_params
            )
            self.preview_ready.emit(img, self.file_path)
        except Exception as e:
            self.preview_error.emit(str(e), self.file_path)


class SaveThread(QThread):
    """TIFF 保存线程 —— 避免大文件写入阻塞主线程（C7）"""

    save_finished = pyqtSignal(bool, str)  # (success, filename)

    def __init__(self, image: np.ndarray, output_path: Path):
        super().__init__()
        self.image = image
        self.output_path = output_path

    def run(self):
        try:
            from core.exporter import ImageExporter
            success = ImageExporter().save_auto(self.image, self.output_path)
            self.save_finished.emit(success, self.output_path.name)
        except Exception as e:
            logger.error(f"SaveThread 保存失败: {e}")
            self.save_finished.emit(False, self.output_path.name)


class ProcessThread(QThread):
    """处理线程，避免阻塞 UI"""

    progress = pyqtSignal(int, int)  # 当前, 总数
    finished = pyqtSignal(np.ndarray)  # 完成信号
    cancelled = pyqtSignal()  # 用户取消信号
    error = pyqtSignal(str)  # 错误信号
    preview_update = pyqtSignal(np.ndarray)  # 预览更新
    status_message = pyqtSignal(str)  # 状态消息
    timelapse_generated = pyqtSignal(str)  # 延时视频生成完成信号（视频路径）
    log_message = pyqtSignal(str)  # 日志消息

    def __init__(
        self,
        file_paths: List[Path],
        stack_mode: StackMode,
        raw_params: dict,
        enable_gap_filling: bool = False,
        gap_fill_method: str = "morphological",
        gap_size: int = 3,
        comet_fade_factor: float = 0.98,
        enable_timelapse: bool = False,
        enable_simple_timelapse: bool = False,
        output_dir: Path = None,
        video_fps: int = 30,
        translator = None,
        enable_satellite_removal: bool = False,
        rotation: int = 0,
        mask_path: Optional[Path] = None,
        fg_mode: "StackMode" = None,
    ):
        super().__init__()
        self.file_paths = file_paths
        self.stack_mode = stack_mode
        self.raw_params = raw_params
        self.enable_gap_filling = enable_gap_filling
        self.gap_fill_method = gap_fill_method
        self.gap_size = gap_size
        self.comet_fade_factor = comet_fade_factor
        self.enable_timelapse = enable_timelapse
        self.enable_simple_timelapse = enable_simple_timelapse
        self.output_dir = output_dir
        self.translator = translator
        self.video_fps = video_fps
        self.enable_satellite_removal = enable_satellite_removal
        self.rotation = rotation
        self.mask_path = mask_path
        self.fg_mode = fg_mode
        self._stop_event = Event()  # 使用线程安全的 Event 替代布尔标志

    def run(self):
        """执行处理"""
        import time
        from utils.logger import setup_logger, enable_file_logging

        logger = setup_logger("ProcessThread")

        try:
            processor = RawProcessor()

            # 确定输出目录（如果未指定，使用默认的"SuperStarTrail"子目录）
            from pathlib import Path
            if self.output_dir is None:
                output_dir = self.file_paths[0].parent / "SuperStarTrail"
            else:
                # 确保 output_dir 是 Path 对象
                output_dir = Path(self.output_dir) if isinstance(self.output_dir, str) else self.output_dir

            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # 启用文件日志记录（保存到输出目录）
            log_file_path = enable_file_logging(output_dir)
            logger.info(f"输出目录: {output_dir}")

            # 如果启用延时视频，生成输出路径
            timelapse_output_path = None
            if self.enable_timelapse:
                # 使用文件命名服务生成视频文件名
                video_filename = FileNamingService.generate_timelapse_filename(
                    file_paths=self.file_paths,
                    stack_mode=self.stack_mode,
                    comet_fade_factor=self.comet_fade_factor if self.stack_mode == StackMode.COMET else None,
                    fps=self.video_fps
                )
                timelapse_output_path = output_dir / video_filename

            # 如果启用银河延时视频，创建生成器
            milkyway_timelapse_generator = None
            milkyway_timelapse_path = None
            if self.enable_simple_timelapse:
                from core.timelapse_generator import TimelapseGenerator
                milkyway_video_filename = f"MilkyWayTimelapse_{self.file_paths[0].stem}-{self.file_paths[-1].stem}_{self.video_fps}FPS.mp4"
                milkyway_timelapse_path = output_dir / milkyway_video_filename
                milkyway_timelapse_generator = TimelapseGenerator(
                    output_path=milkyway_timelapse_path,
                    fps=self.video_fps,
                )

            # 加载蒙版（如有）
            sky_mask = None
            first_img = None
            if self.mask_path is not None:
                try:
                    from core.mask_processor import MaskProcessor
                    # 先读第一张图确定目标分辨率
                    first_img = processor.process(self.file_paths[0], rotation=self.rotation, **self.raw_params)
                    sky_mask = MaskProcessor.load(self.mask_path, target_shape=first_img.shape[:2], rotation=self.rotation)
                    self.log_message.emit(f"已加载蒙版: {self.mask_path.name}，形状: {sky_mask.shape}")
                    logger.info(f"已加载蒙版: {self.mask_path}")
                except Exception as e:
                    self.log_message.emit(f"⚠️  蒙版加载失败，将跳过双轨堆栈: {e}")
                    logger.warning(f"蒙版加载失败: {e}")

            engine = StackingEngine(
                self.stack_mode,
                enable_gap_filling=self.enable_gap_filling,
                gap_fill_method=self.gap_fill_method,
                gap_size=self.gap_size,
                enable_timelapse=self.enable_timelapse,
                timelapse_output_path=timelapse_output_path,
                video_fps=self.video_fps,
                sky_mask=sky_mask,
                fg_mode=self.fg_mode if self.fg_mode is not None else StackMode.AVERAGE,
            )

            # 如果是彗星模式，设置衰减因子
            if self.stack_mode == StackMode.COMET:
                engine.set_comet_fade_factor(self.comet_fade_factor)
                logger.info(f"彗星模式: 衰减因子 = {self.comet_fade_factor}")

            # 检查功能是否因依赖缺失而被降级
            if self.enable_gap_filling and not engine.enable_gap_filling:
                warning_msg = "⚠️  间隔填充功能不可用（scipy 未安装），已自动禁用"
                self.log_message.emit(warning_msg)
                logger.warning(warning_msg)

            total = len(self.file_paths)

            # 开始处理
            mode_name = self.stack_mode.value
            self.log_message.emit("=" * 60)
            self.log_message.emit("开始星轨合成")
            self.log_message.emit(f"文件数量: {total}")
            self.log_message.emit(f"堆栈模式: {mode_name}")
            self.log_message.emit("白平衡: 相机白平衡")
            self.log_message.emit(f"间隔填充: {'启用' if self.enable_gap_filling else '禁用'}")
            if self.enable_gap_filling:
                self.log_message.emit(f"填充方法: {self.gap_fill_method}, 间隔大小: {self.gap_size}")
            self.log_message.emit(f"去卫星划痕: {'启用 (Hough 直线检测)' if self.enable_satellite_removal else '禁用'}")
            self.log_message.emit(f"星轨延时: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_timelapse else '禁用'}")
            self.log_message.emit(f"银河延时: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_simple_timelapse else '禁用'}")
            self.log_message.emit("=" * 60)

            logger.info(f"=" * 60)
            logger.info(f"开始星轨合成")
            logger.info(f"文件数量: {total}")
            logger.info(f"堆栈模式: {mode_name}")
            logger.info("白平衡: 相机白平衡")
            logger.info(f"间隔填充: {'启用' if self.enable_gap_filling else '禁用'}")
            if self.enable_gap_filling:
                logger.info(f"填充方法: {self.gap_fill_method}, 间隔大小: {self.gap_size}")
            logger.info(f"延时视频: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_timelapse else '禁用'}")
            logger.info(f"=" * 60)

            self.status_message.emit(f"开始处理 {total} 张图片...")

            start_time = time.time()
            failed_files = []  # 记录失败的文件
            satellite_removed_count = 0  # 统计检测到划痕的帧数

            # 初始化划痕检测器（如果启用）
            sat_filter = None
            if self.enable_satellite_removal:
                from core.satellite_filter import SatelliteFilter
                sat_filter = SatelliteFilter()

            # 若蒙版加载时已处理第一张图，缓存以避免重复 I/O
            _cached_first_img = first_img if sky_mask is not None and first_img is not None else None

            for i, path in enumerate(self.file_paths):
                if self._stop_event.is_set():
                    logger.warning("用户取消处理")
                    break

                file_start = time.time()

                try:
                    # 读取并处理 RAW 文件
                    log_msg = f"[{i+1:3d}/{total}] 正在处理: {path.name}"
                    logger.info(log_msg)
                    self.log_message.emit(log_msg)

                    if i == 0 and _cached_first_img is not None:
                        img = _cached_first_img
                    else:
                        img = processor.process(path, rotation=self.rotation, **self.raw_params)

                    # 如果启用银河延时视频，添加此帧
                    if milkyway_timelapse_generator:
                        milkyway_timelapse_generator.add_frame(img)

                    # 划痕检测（如果启用）
                    satellite_mask = None
                    if sat_filter is not None:
                        satellite_mask = sat_filter.detect_streaks(img)
                        if satellite_mask.any():
                            satellite_removed_count += 1
                            log_msg = f"[{i+1:3d}/{total}] 🛸 检测到划痕，已遮罩 {satellite_mask.sum():,} 像素"
                            logger.info(log_msg)
                            self.log_message.emit(log_msg)

                    # 添加到堆栈（传入遮罩）
                    engine.add_image(img, satellite_mask=satellite_mask)

                    file_duration = time.time() - file_start
                    log_msg = f"[{i+1:3d}/{total}] 完成: {path.name} ({file_duration:.2f}秒)"
                    logger.info(log_msg)
                    self.log_message.emit(log_msg)

                except Exception as e:
                    log_msg = f"[{i+1:3d}/{total}] ⚠️  跳过损坏文件: {path.name}"
                    logger.error(f"{log_msg} - {e}")
                    self.log_message.emit(log_msg)
                    failed_files.append((path.name, str(e)))  # 记录失败的文件和错误信息
                    # 继续处理下一张

                # 发送进度
                self.progress.emit(i + 1, total)

                # 计算预计剩余时间
                elapsed = time.time() - start_time
                avg_time = elapsed / (i + 1)
                remaining = avg_time * (total - i - 1)

                # 格式化剩余时间
                if remaining >= 60:
                    remaining_str = f"{int(remaining // 60)}分{int(remaining % 60)}秒"
                else:
                    remaining_str = f"{int(remaining)}秒"

                # 根据是否启用额外功能，添加提示
                if self.enable_gap_filling or self.enable_timelapse or self.enable_simple_timelapse:
                    status = f"⏳ 处理中 - 预计剩余: {remaining_str} + 后期处理"
                else:
                    status = f"⏳ 处理中 - 预计剩余: {remaining_str}"
                self.status_message.emit(status)

                # 每处理 3 张图片更新一次预览（不应用填充，加快速度）
                if ((i + 1) % 3 == 0 or i == total - 1) and engine.count > 0:
                    logger.info(f"更新预览 ({i+1}/{total})")
                    preview = engine.get_result(apply_gap_filling=False)
                    self.preview_update.emit(preview)

            success_count = total - len(failed_files)
            if success_count == 0:
                raise ValueError("没有成功读取任何图像，请检查 RAW/TIFF 格式是否受支持，或文件是否已损坏")

            # 获取最终结果
            if not self._stop_event.is_set():
                total_duration = time.time() - start_time
                self.log_message.emit("-" * 60)
                self.log_message.emit("✅ 堆栈完成!")
                self.log_message.emit(f"总耗时: {total_duration:.2f} 秒")
                if self.enable_satellite_removal:
                    self.log_message.emit(
                        f"🛸 共检测到划痕帧: {satellite_removed_count}/{total} 张"
                    )
                self.log_message.emit(f"平均速度: {total_duration/total:.2f} 秒/张")

                logger.info(f"-" * 60)
                logger.info(f"✅ 堆栈完成!")
                logger.info(f"总耗时: {total_duration:.2f} 秒")
                logger.info(f"平均速度: {total_duration/total:.2f} 秒/张")

                # 应用间隔填充（如果启用）
                if self.enable_gap_filling and not self._stop_event.is_set():
                    self.log_message.emit("-" * 60)
                    self.log_message.emit("正在应用间隔填充...")
                    logger.info(f"-" * 60)
                    logger.info(f"正在应用间隔填充...")
                    gap_start = time.time()

                result = engine.get_result(
                    apply_gap_filling=not self._stop_event.is_set(),
                    stop_event=self._stop_event,
                )
                if self._stop_event.is_set():
                    raise ProcessingCancelledError("用户取消了后处理")

                if self.enable_gap_filling and not self._stop_event.is_set():
                    gap_duration = time.time() - gap_start
                    self.log_message.emit(f"间隔填充完成，耗时: {gap_duration:.2f} 秒")
                    logger.info(f"间隔填充完成，耗时: {gap_duration:.2f} 秒")

                # 生成星轨延时视频（如果启用，且未取消）
                if self.enable_timelapse and not self._stop_event.is_set():
                    self.log_message.emit("-" * 60)
                    self.log_message.emit("正在生成星轨延时视频...")
                    logger.info(f"-" * 60)
                    logger.info(f"正在生成星轨延时视频...")
                    self.status_message.emit("正在生成星轨延时...")
                    timelapse_start = time.time()

                    success = engine.finalize_timelapse(cleanup=True, stop_event=self._stop_event)
                    if self._stop_event.is_set():
                        raise ProcessingCancelledError("用户取消了星轨延时生成")

                    if success:
                        timelapse_duration = time.time() - timelapse_start
                        self.log_message.emit(f"✅ 星轨延时视频生成完成，耗时: {timelapse_duration:.2f} 秒")
                        self.log_message.emit(f"视频保存至: {timelapse_output_path.name}")
                        logger.info(f"星轨延时视频生成完成，耗时: {timelapse_duration:.2f} 秒")
                        logger.info(f"视频保存至: {timelapse_output_path}")
                        # 发送视频路径信号
                        self.timelapse_generated.emit(str(timelapse_output_path))
                    else:
                        self.log_message.emit("❌ 星轨延时视频生成失败")
                        logger.error("星轨延时视频生成失败")

                # 生成银河延时视频（如果启用，且未取消）
                if self.enable_simple_timelapse and milkyway_timelapse_generator and not self._stop_event.is_set():
                    self.log_message.emit("-" * 60)
                    self.log_message.emit("正在生成银河延时视频...")
                    logger.info(f"-" * 60)
                    logger.info(f"正在生成银河延时视频...")
                    self.status_message.emit("正在生成银河延时...")
                    milkyway_timelapse_start = time.time()

                    try:
                        success = milkyway_timelapse_generator.generate_video(cleanup=True, stop_event=self._stop_event)
                        if self._stop_event.is_set():
                            raise ProcessingCancelledError("用户取消了银河延时生成")

                        if success:
                            milkyway_timelapse_duration = time.time() - milkyway_timelapse_start
                            self.log_message.emit(f"✅ 银河延时视频生成完成，耗时: {milkyway_timelapse_duration:.2f} 秒")
                            self.log_message.emit(f"视频保存至: {milkyway_timelapse_path.name}")
                            logger.info(f"银河延时视频生成完成，耗时: {milkyway_timelapse_duration:.2f} 秒")
                            logger.info(f"视频保存至: {milkyway_timelapse_path}")
                            # 发送视频路径信号
                            self.timelapse_generated.emit(str(milkyway_timelapse_path))
                        else:
                            self.log_message.emit("❌ 银河延时视频生成失败")
                            logger.error("银河延时视频生成失败")
                    except ProcessingCancelledError:
                        raise
                    except Exception as e:
                        self.log_message.emit(f"❌ 银河延时视频生成失败: {str(e)}")
                        logger.error(f"银河延时视频生成失败: {e}")

                # 显示失败文件汇总
                if failed_files:
                    self.log_message.emit("=" * 60)
                    self.log_message.emit(f"⚠️  处理汇总: 成功 {total - len(failed_files)}/{total}, 失败 {len(failed_files)} 个文件")
                    self.log_message.emit("失败文件列表:")
                    for filename, error in failed_files:
                        self.log_message.emit(f"  • {filename}: {error}")
                    logger.warning(f"处理汇总: {len(failed_files)} 个文件失败")
                    for filename, error in failed_files:
                        logger.warning(f"  失败: {filename} - {error}")
                else:
                    self.log_message.emit("=" * 60)
                    self.log_message.emit(f"✅ 所有 {total} 个文件处理成功！")
                    logger.info(f"所有 {total} 个文件处理成功")

                if self._stop_event.is_set():
                    raise ProcessingCancelledError("用户取消了结果保存前流程")

                self.log_message.emit("=" * 60)
                logger.info(f"=" * 60)
                self.finished.emit(result)

        except ProcessingCancelledError as e:
            logger.info(f"处理已取消: {e}")
            self.log_message.emit("⏹️ 已取消当前任务")
        except Exception as e:
            logger.error(f"处理失败: {e}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))
        finally:
            if self._stop_event.is_set():
                self.cancelled.emit()

    def stop(self):
        """停止处理（线程安全）"""
        self._stop_event.set()



class MainWindow(QMainWindow):
    """主窗口类（重构版 - 使用 Panel 组件）"""

    def __init__(self):
        super().__init__()

        # 初始化翻译器
        settings = get_settings()
        language = settings.get_language()
        set_language(language)
        self.tr = get_translator()

        self.setWindowTitle(f"{self.tr.tr('app_name')} by James Zhen Yu")
        self.setMinimumSize(960, 640)
        self.showMaximized()

        # 设置窗口图标
        icon_path = Path(__file__).parent.parent / "resources" / "logo.png"
        if icon_path.exists():
            icon = QIcon(str(icon_path))
            # 添加多个尺寸以确保在不同场景下都显示正确
            for size in [16, 32, 48, 64, 128, 256, 512]:
                pixmap = QPixmap(str(icon_path)).scaled(
                    size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                icon.addPixmap(pixmap)
            self.setWindowIcon(icon)

            # 在macOS上，还需要设置应用程序级别的图标
            if hasattr(QApplication.instance(), 'setWindowIcon'):
                QApplication.instance().setWindowIcon(icon)

        # 数据
        self.result_image: np.ndarray = None
        self.process_thread: ProcessThread = None
        self.timelapse_video_path: Path = None
        self._current_preview_file: Path = None  # 当前预览的文件（用于实时WB更新）
        self._preview_thread: PreviewThread = None  # C6: 预览子线程
        self._old_preview_threads: list = []        # 保持旧线程引用直到其真正退出
        self._save_thread: SaveThread = None        # C7: 保存子线程
        self._pending_save_output_dir: Path = None  # C7: 保存完成后用于弹窗

        # 初始化 UI
        self.init_ui()

    def init_ui(self):
        """初始化用户界面（三栏布局：左侧文件栏 / 中间预览 / 右侧参数栏）"""
        from ui.styles import COLORS
        # 应用全局样式表
        self.setStyleSheet(get_complete_stylesheet())

        # 主容器
        main_widget = QWidget()
        main_widget.setStyleSheet(f"background-color: {COLORS['bg_base']};")
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_widget.setLayout(main_layout)

        # ── 三栏 QSplitter ─────────────────────────────────────────────────────
        content_splitter = QSplitter(Qt.Horizontal)
        content_splitter.setHandleWidth(1)
        content_splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background-color: {COLORS['border']};
            }}
        """)

        # ── 左侧文件管理栏 ──────────────────────────────────────────────────────
        self.file_list_panel = FileListPanel(self.tr)
        self.file_list_panel.setMinimumWidth(220)
        self.file_list_panel.setMaximumWidth(320)
        self.file_list_panel.setStyleSheet(
            f"background-color: {COLORS['bg_sidebar']}; border: none;"
        )

        # ── 中间预览区（弹性，占主要空间） ─────────────────────────────────────
        self.preview_panel = PreviewPanel(self.tr)

        # ── 右侧参数控制栏 ──────────────────────────────────────────────────────
        self.params_panel = ParametersPanel(self.tr)
        self.control_panel = ControlPanel(self.tr)

        right_panel = QWidget()
        right_panel.setMinimumWidth(240)
        right_panel.setMaximumWidth(320)
        right_panel.setStyleSheet(
            f"background-color: {COLORS['bg_sidebar']}; border: none;"
        )
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        right_layout.addWidget(self.params_panel, stretch=1)
        right_layout.addWidget(self.control_panel)
        right_panel.setLayout(right_layout)

        # 加入分割器
        content_splitter.addWidget(self.file_list_panel)
        content_splitter.addWidget(self.preview_panel)
        content_splitter.addWidget(right_panel)

        # 比例：左 260 / 中弹性 / 右 280
        content_splitter.setStretchFactor(0, 0)  # 左：固定
        content_splitter.setStretchFactor(1, 1)  # 中：弹性
        content_splitter.setStretchFactor(2, 0)  # 右：固定
        content_splitter.setSizes([260, 9999, 280])

        main_layout.addWidget(content_splitter)

        # 连接信号
        self._connect_signals()

        # 创建菜单栏
        self.create_menu_bar()

    def _connect_signals(self):
        """连接各个 Panel 的信号到处理函数"""
        # FileListPanel 信号
        self.file_list_panel.files_selected.connect(self._on_files_selected)
        self.file_list_panel.file_clicked.connect(self._preview_single_file)
        self.file_list_panel.rotation_changed.connect(self._on_rotation_changed_preview)
        self.params_panel.set_fg_mode_visible(False)

        # ControlPanel 信号
        self.control_panel.start_clicked.connect(self.start_processing)
        self.control_panel.stop_clicked.connect(self.stop_processing)

        # FileListPanel 打开输出目录信号
        self.file_list_panel.open_output_clicked.connect(self.open_output_dir)

    def _on_files_selected(self, files: List[Path]):
        """文件列表改变时的处理"""
        can_start = len(files) > 0
        self.control_panel.set_start_enabled(can_start)

    def _preview_single_file(self, file_path: Path):
        """预览单个文件（异步，不阻塞主线程）"""
        self._current_preview_file = file_path
        self.preview_panel.reset_preview_cache()

        # 若上一个预览线程仍在运行，断开信号并让它自行结束
        # 连接 finished → deleteLater 确保 Qt 持有对象直到线程真正退出
        if self._preview_thread is not None and self._preview_thread.isRunning():
            # 断开信号使结果被丢弃，但保持 Python 引用直到线程真正退出
            self._preview_thread.preview_ready.disconnect()
            self._preview_thread.preview_error.disconnect()
            self._old_preview_threads.append(self._preview_thread)

        self._preview_thread = PreviewThread(
            file_path, {}, rotation=self.file_list_panel.get_rotation()
        )
        self._preview_thread.preview_ready.connect(self._on_preview_ready)
        self._preview_thread.preview_error.connect(self._on_preview_error)
        self._preview_thread.finished.connect(self._prune_old_preview_threads)
        self._preview_thread.start()

    def _on_preview_ready(self, img: np.ndarray, file_path: Path):
        """预览线程完成回调"""
        if file_path != self._current_preview_file:
            return
        mask = None
        self.preview_panel.update_preview(img, mask=mask)
        self.preview_panel.set_status_file(file_path.name)
        logger.info(f"预览文件: {file_path.name}")

    def _prune_old_preview_threads(self):
        """线程结束后从列表中移除已完成的旧线程，允许 GC 回收"""
        self._old_preview_threads = [t for t in self._old_preview_threads if t.isRunning()]

    def _on_rotation_changed_preview(self, _angle: int):
        """旋转角度变化时刷新预览（含蒙版叠加）"""
        if self._current_preview_file is not None:
            self._preview_single_file(self._current_preview_file)

    def _on_mask_path_changed(self, _mask_path):
        """蒙版选择/清除时刷新预览"""
        if self._current_preview_file is not None:
            self._preview_single_file(self._current_preview_file)

    def _on_preview_error(self, error_msg: str, file_path: Path):
        """预览线程出错回调"""
        if file_path != self._current_preview_file:
            return
        logger.error(f"预览失败: {error_msg}")
        QMessageBox.warning(
            self,
            self.tr.tr("warning") if hasattr(self.tr, 'tr') else "警告",
            f"无法预览文件: {file_path.name}\n错误: {error_msg}"
        )

    def start_processing(self):
        """开始处理"""
        files_to_process = self.file_list_panel.get_files_to_process()

        if not files_to_process:
            QMessageBox.warning(
                self,
                self.tr.tr("warning") if hasattr(self.tr, 'tr') else "警告",
                self.tr.tr("all_files_excluded") if hasattr(self.tr, 'tr') else "所有文件都已被排除，无法进行处理"
            )
            return

        # 更新UI状态
        self.control_panel.set_processing_state()
        self.file_list_panel.set_open_output_enabled(False)
        self.control_panel.reset_progress(len(files_to_process))
        self.control_panel.update_status(self.tr.tr("preparing"))

        # 重置预览缓存
        self.preview_panel.reset_preview_cache()

        # 清除默认使用说明，开始记录处理日志
        self.preview_panel.clear_log()

        # 从配置获取参数
        settings = get_settings()
        gap_fill_method = settings.get_gap_fill_method()
        gap_size = settings.get_gap_size()
        video_fps = settings.get_video_fps()

        # 获取输出目录
        output_dir = self.file_list_panel.get_output_dir()

        # 创建并启动处理线程
        self.process_thread = ProcessThread(
            files_to_process,
            self.params_panel.get_stack_mode(),
            {},
            enable_gap_filling=self.params_panel.is_gap_filling_enabled(),
            gap_fill_method=gap_fill_method,
            gap_size=gap_size,
            comet_fade_factor=self.params_panel.get_comet_fade_factor(),
            enable_timelapse=self.params_panel.is_timelapse_enabled(),
            enable_simple_timelapse=self.params_panel.is_simple_timelapse_enabled(),
            output_dir=output_dir,
            video_fps=video_fps,
            translator=self.tr,
            enable_satellite_removal=self.params_panel.is_satellite_removal_enabled(),
            rotation=self.file_list_panel.get_rotation(),
            mask_path=None,
            fg_mode=None,
        )

        # 连接信号
        self.process_thread.progress.connect(self.control_panel.update_progress)
        self.process_thread.preview_update.connect(self.preview_panel.update_preview)
        self.process_thread.finished.connect(self.processing_finished)
        self.process_thread.cancelled.connect(self.processing_cancelled)
        self.process_thread.error.connect(self.processing_error)
        self.process_thread.status_message.connect(self.control_panel.update_status)
        self.process_thread.timelapse_generated.connect(self.on_timelapse_generated)
        self.process_thread.log_message.connect(self.preview_panel.append_log)

        self.process_thread.start()

    def stop_processing(self):
        """停止处理"""
        if self.process_thread:
            self.process_thread.stop()
            self.control_panel.set_stop_enabled(False)
            self.control_panel.update_status("正在取消...")

    def processing_cancelled(self):
        """用户取消处理后恢复 UI 状态"""
        if self.process_thread:
            self.process_thread.deleteLater()  # 转交 Qt 管理生命周期，避免 GC 提前销毁
        self.process_thread = None
        self.control_panel.set_idle_state(can_start=True)
        self.control_panel.update_status("已取消")

    def processing_finished(self, result: np.ndarray):
        """堆栈完成 —— 启动后台保存线程，不阻塞主线程（C7）"""
        self.result_image = result
        if self.process_thread:
            self.process_thread.deleteLater()  # 转交 Qt 管理生命周期，避免 GC 提前销毁
        self.process_thread = None
        self.preview_panel.update_preview(result)

        # 确定输出目录和文件路径
        output_dir = self.file_list_panel.get_output_dir()
        if not output_dir:
            output_dir = self.file_list_panel.get_all_files()[0].parent / "SuperStarTrail"
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        self._pending_save_output_dir = output_dir

        tiff_path = output_dir / self._generate_output_filename()

        # 日志提示
        self.preview_panel.append_log("-" * 60)
        self.preview_panel.append_log(f"正在保存 TIFF 文件: {tiff_path.name}")
        self.preview_panel.append_log("应用亮度拉伸 (1%-99.5%)...")
        self.control_panel.update_status("正在保存 TIFF...")

        # 后台保存，保存期间保持按钮禁用
        self._save_thread = SaveThread(self.result_image, tiff_path)
        self._save_thread.save_finished.connect(self._on_save_finished)
        self._save_thread.start()

    def _on_save_finished(self, success: bool, filename: str):
        """TIFF 保存完成回调"""
        output_dir = self._pending_save_output_dir

        if success:
            self.preview_panel.append_log(f"✅ TIFF 保存成功: {filename}")
        else:
            self.preview_panel.append_log("❌ TIFF 保存失败")

        self.preview_panel.append_log("=" * 60)
        self.preview_panel.append_log("全部完成！可以打开输出目录查看结果")

        # 恢复 UI 状态
        self.control_panel.set_idle_state(can_start=True)
        self.file_list_panel.set_open_output_enabled(True)

        if success:
            self.control_panel.update_status("✅ 合成完成")
            logger.info(f"合成完成！文件已保存到: {output_dir}")
            self.play_completion_sound()
            QMessageBox.information(
                self,
                self.tr.tr("msg_complete_title"),
                self.tr.tr("msg_complete_text").format(path=output_dir)
            )
            self.open_output_dir()
        else:
            self.control_panel.update_status("❌ 合成完成但保存失败")
            QMessageBox.warning(
                self,
                self.tr.tr("msg_save_failed_title"),
                self.tr.tr("msg_save_failed_text")
            )

    def processing_error(self, error_msg: str):
        """处理错误"""
        self.control_panel.set_idle_state(can_start=True)
        self.control_panel.update_status(self.tr.tr("failed"))

        QMessageBox.critical(
            self,
            self.tr.tr("msg_error_title"),
            self.tr.tr("msg_error_text").format(error=error_msg)
        )

    def _generate_output_filename(self) -> str:
        """生成智能输出文件名"""
        all_files = self.file_list_panel.get_all_files()
        if not all_files:
            return "star_trail.tif"

        mask_path = self.file_list_panel.get_mask_path()
        return FileNamingService.generate_output_filename(
            file_paths=all_files,
            stack_mode=self.params_panel.get_stack_mode(),
            comet_fade_factor=self.params_panel.get_comet_fade_factor()
                if self.params_panel.get_stack_mode() == StackMode.COMET else None,
            enable_gap_filling=self.params_panel.is_gap_filling_enabled(),
            file_extension="tif",
            has_mask=mask_path is not None,
            fg_mode=self.params_panel.get_fg_mode() if mask_path is not None else None,
        )

    def on_timelapse_generated(self, video_path: str):
        """处理延时视频生成完成事件"""
        self.timelapse_video_path = Path(video_path)
        logger.info(f"延时视频已生成: {self.timelapse_video_path}")

    def open_output_dir(self):
        """打开输出目录"""
        output_dir = self.file_list_panel.get_output_dir()
        if not output_dir:
            QMessageBox.warning(self, "提示", "输出目录不存在")
            return

        output_dir_path = Path(output_dir)
        if not output_dir_path.exists():
            QMessageBox.warning(self, "提示", "输出目录不存在")
            return

        try:
            import subprocess
            import platform

            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(output_dir_path)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(output_dir_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(output_dir_path)])
        except Exception as e:
            logger.error(f"打开输出目录失败: {e}")

    def play_completion_sound(self):
        """播放完成音效"""
        try:
            import subprocess
            import platform

            sound_path = Path(__file__).parent.parent.parent / "ending.mp3"

            if sound_path.exists():
                if platform.system() == "Darwin":  # macOS
                    subprocess.Popen(["afplay", str(sound_path)])
                elif platform.system() == "Windows":
                    import winsound
                    winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:  # Linux
                    try:
                        subprocess.Popen(["paplay", str(sound_path)])
                    except:
                        subprocess.Popen(["aplay", str(sound_path)])
            else:
                logger.warning(f"完成音效文件不存在: {sound_path}")
        except Exception as e:
            logger.error(f"播放完成音效失败: {e}")

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu(self.tr.tr("menu_file"))

        open_folder_action = QAction(self.tr.tr("menu_open_folder"), self)
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.triggered.connect(self.file_list_panel.select_folder)
        file_menu.addAction(open_folder_action)

        output_dir_action = QAction(self.tr.tr("menu_select_output"), self)
        output_dir_action.triggered.connect(self.file_list_panel.select_output_dir)
        file_menu.addAction(output_dir_action)

        file_menu.addSeparator()

        exit_action = QAction(self.tr.tr("menu_exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu(self.tr.tr("menu_edit"))

        preferences_action = QAction(self.tr.tr("menu_preferences"), self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)

        # 处理菜单
        process_menu = menubar.addMenu(self.tr.tr("menu_process"))

        start_action = QAction(self.tr.tr("menu_start"), self)
        start_action.setShortcut("Ctrl+R")
        start_action.triggered.connect(self.start_processing)
        process_menu.addAction(start_action)

        stop_action = QAction(self.tr.tr("menu_stop"), self)
        stop_action.setShortcut("Ctrl+.")
        stop_action.triggered.connect(self.stop_processing)
        process_menu.addAction(stop_action)

        # 窗口菜单
        window_menu = menubar.addMenu(self.tr.tr("menu_window"))

        minimize_action = QAction(self.tr.tr("menu_minimize"), self)
        minimize_action.setShortcut("Ctrl+M")
        minimize_action.triggered.connect(self.showMinimized)
        window_menu.addAction(minimize_action)

        zoom_action = QAction(self.tr.tr("menu_zoom"), self)
        zoom_action.triggered.connect(self.toggle_maximized)
        window_menu.addAction(zoom_action)

        # 帮助菜单
        help_menu = menubar.addMenu(self.tr.tr("menu_help"))

        guide_action = QAction(self.tr.tr("menu_guide"), self)
        guide_action.triggered.connect(self.show_guide)
        help_menu.addAction(guide_action)

        help_menu.addSeparator()

        about_action = QAction(self.tr.tr("menu_about"), self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_about(self):
        """显示关于对话框"""
        dialog = AboutDialog(self)
        dialog.exec_()

    def show_preferences(self):
        """显示偏好设置对话框"""
        dialog = PreferencesDialog(self)
        if dialog.exec_():
            logger.info("偏好设置已更新")

    def show_guide(self):
        """显示使用指南"""
        guide_text = """
        <h2>彗星星轨 - 使用指南</h2>

        <h3>基本流程：</h3>
        <ol>
            <li><b>选择文件：</b>点击"选择图片目录"，选择包含照片的文件夹<br>
            支持格式：RAW (CR2, NEF, ARW等)</li>
            <li><b>选择模式：</b>
                <ul>
                    <li><b>传统星轨：</b>标准的星轨叠加效果</li>
                    <li><b>彗星星轨：</b>模拟彗星尾巴的渐变效果</li>
                    <li><b>平均值：</b>用于去噪等应用</li>
                    <li><b>最暗值：</b>用于去除动态物体</li>
                </ul>
            </li>
            <li><b>调整参数：</b>选择白平衡、彗星尾巴长度等</li>
            <li><b>开始处理：</b>点击"开始处理"按钮</li>
            <li><b>查看结果：</b>处理完成后可打开输出目录查看</li>
        </ol>

        <h3>高级功能：</h3>
        <ul>
            <li><b>间隔填充：</b>填补星点之间的间隔，使星轨更连续</li>
            <li><b>延时视频：</b>生成4K延时视频，展示星轨形成过程</li>
            <li><b>文件排除：</b>右键点击文件列表可排除特定文件</li>
        </ul>
        """

        msg_box = QMessageBox(self)
        msg_box.setWindowTitle(self.tr.tr("menu_guide"))
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(guide_text)
        msg_box.exec_()

    def toggle_maximized(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()
