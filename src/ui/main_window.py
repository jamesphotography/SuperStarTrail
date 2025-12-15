"""
主窗口模块

应用程序的主界面
"""

from pathlib import Path
from typing import List
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
from core.stacking_engine import StackingEngine, StackMode
from utils.logger import setup_logger
from utils.settings import get_settings
from utils.file_naming import FileNamingService
from ui.dialogs import AboutDialog, PreferencesDialog
from ui.panels import FileListPanel, ParametersPanel, ControlPanel, PreviewPanel
from i18n import get_translator, set_language
from ui.styles import get_complete_stylesheet

logger = setup_logger(__name__)


class ProcessThread(QThread):
    """处理线程，避免阻塞 UI"""

    progress = pyqtSignal(int, int)  # 当前, 总数
    finished = pyqtSignal(np.ndarray)  # 完成信号
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
        enable_alignment: bool = False,
        enable_gap_filling: bool = False,
        gap_fill_method: str = "morphological",
        gap_size: int = 3,
        comet_fade_factor: float = 0.98,
        enable_timelapse: bool = False,
        enable_simple_timelapse: bool = False,
        output_dir: Path = None,
        video_fps: int = 30,
        translator = None,
    ):
        super().__init__()
        self.file_paths = file_paths
        self.stack_mode = stack_mode
        self.raw_params = raw_params
        self.enable_alignment = enable_alignment
        self.enable_gap_filling = enable_gap_filling
        self.gap_fill_method = gap_fill_method
        self.gap_size = gap_size
        self.comet_fade_factor = comet_fade_factor
        self.enable_timelapse = enable_timelapse
        self.enable_simple_timelapse = enable_simple_timelapse
        self.output_dir = output_dir
        self.translator = translator
        self.video_fps = video_fps
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
                    white_balance=self.raw_params.get('white_balance', 'camera'),
                    comet_fade_factor=self.comet_fade_factor if self.stack_mode == StackMode.COMET else None,
                    fps=self.video_fps
                )
                timelapse_output_path = output_dir / video_filename

            # 如果启用银河延时视频，创建生成器
            milkyway_timelapse_generator = None
            milkyway_timelapse_path = None
            if self.enable_simple_timelapse:
                from core.timelapse_generator import TimelapseGenerator
                # 生成银河延时视频文件名
                wb_str = self.raw_params.get('white_balance', 'camera').capitalize()
                milkyway_video_filename = f"MilkyWayTimelapse_{self.file_paths[0].stem}-{self.file_paths[-1].stem}_{wb_str}WB_{self.video_fps}FPS.mp4"
                milkyway_timelapse_path = output_dir / milkyway_video_filename
                milkyway_timelapse_generator = TimelapseGenerator(
                    output_path=milkyway_timelapse_path,
                    fps=self.video_fps,
                    resolution=(3840, 2160)
                )

            engine = StackingEngine(
                self.stack_mode,
                enable_alignment=self.enable_alignment,
                enable_gap_filling=self.enable_gap_filling,
                gap_fill_method=self.gap_fill_method,
                gap_size=self.gap_size,
                enable_timelapse=self.enable_timelapse,
                timelapse_output_path=timelapse_output_path,
                video_fps=self.video_fps,
            )

            # 如果是彗星模式，设置衰减因子
            if self.stack_mode == StackMode.COMET:
                engine.set_comet_fade_factor(self.comet_fade_factor)
                logger.info(f"彗星模式: 衰减因子 = {self.comet_fade_factor}")

            # 检查功能是否因依赖缺失而被降级
            if self.enable_alignment and not engine.enable_alignment:
                warning_msg = "⚠️  图像对齐功能不可用（OpenCV 未安装），已自动禁用"
                self.log_message.emit(warning_msg)
                logger.warning(warning_msg)

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
            self.log_message.emit(f"白平衡: {self.raw_params.get('white_balance', 'camera')}")
            self.log_message.emit(f"图像对齐: {'启用' if self.enable_alignment else '禁用'}")
            self.log_message.emit(f"间隔填充: {'启用' if self.enable_gap_filling else '禁用'}")
            if self.enable_gap_filling:
                self.log_message.emit(f"填充方法: {self.gap_fill_method}, 间隔大小: {self.gap_size}")
            self.log_message.emit(f"星轨延时: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_timelapse else '禁用'}")
            self.log_message.emit(f"银河延时: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_simple_timelapse else '禁用'}")
            self.log_message.emit("=" * 60)

            logger.info(f"=" * 60)
            logger.info(f"开始星轨合成")
            logger.info(f"文件数量: {total}")
            logger.info(f"堆栈模式: {mode_name}")
            logger.info(f"白平衡: {self.raw_params.get('white_balance', 'camera')}")
            logger.info(f"图像对齐: {'启用' if self.enable_alignment else '禁用'}")
            logger.info(f"间隔填充: {'启用' if self.enable_gap_filling else '禁用'}")
            if self.enable_gap_filling:
                logger.info(f"填充方法: {self.gap_fill_method}, 间隔大小: {self.gap_size}")
            logger.info(f"延时视频: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_timelapse else '禁用'}")
            logger.info(f"=" * 60)

            self.status_message.emit(f"开始处理 {total} 张图片...")

            start_time = time.time()
            failed_files = []  # 记录失败的文件

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

                    img = processor.process(path, **self.raw_params)

                    # 如果启用银河延时视频，添加此帧
                    if milkyway_timelapse_generator:
                        milkyway_timelapse_generator.add_frame(img)

                    # 添加到堆栈
                    engine.add_image(img)

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
                if (i + 1) % 3 == 0 or i == total - 1:
                    logger.info(f"更新预览 ({i+1}/{total})")
                    preview = engine.get_result(apply_gap_filling=False)
                    self.preview_update.emit(preview)

            # 获取最终结果
            if not self._stop_event.is_set():
                total_duration = time.time() - start_time
                self.log_message.emit("-" * 60)
                self.log_message.emit("✅ 堆栈完成!")
                self.log_message.emit(f"总耗时: {total_duration:.2f} 秒")
                self.log_message.emit(f"平均速度: {total_duration/total:.2f} 秒/张")

                logger.info(f"-" * 60)
                logger.info(f"✅ 堆栈完成!")
                logger.info(f"总耗时: {total_duration:.2f} 秒")
                logger.info(f"平均速度: {total_duration/total:.2f} 秒/张")

                # 应用间隔填充（如果启用）
                if self.enable_gap_filling:
                    self.log_message.emit("-" * 60)
                    self.log_message.emit("正在应用间隔填充...")
                    logger.info(f"-" * 60)
                    logger.info(f"正在应用间隔填充...")
                    gap_start = time.time()

                result = engine.get_result(apply_gap_filling=True)

                if self.enable_gap_filling:
                    gap_duration = time.time() - gap_start
                    self.log_message.emit(f"间隔填充完成，耗时: {gap_duration:.2f} 秒")
                    logger.info(f"间隔填充完成，耗时: {gap_duration:.2f} 秒")

                # 生成星轨延时视频（如果启用）
                if self.enable_timelapse:
                    self.log_message.emit("-" * 60)
                    self.log_message.emit("正在生成星轨延时视频...")
                    logger.info(f"-" * 60)
                    logger.info(f"正在生成星轨延时视频...")
                    self.status_message.emit("正在生成星轨延时...")
                    timelapse_start = time.time()

                    success = engine.finalize_timelapse(cleanup=True)

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

                # 生成银河延时视频（如果启用）
                if self.enable_simple_timelapse and milkyway_timelapse_generator:
                    self.log_message.emit("-" * 60)
                    self.log_message.emit("正在生成银河延时视频...")
                    logger.info(f"-" * 60)
                    logger.info(f"正在生成银河延时视频...")
                    self.status_message.emit("正在生成银河延时...")
                    milkyway_timelapse_start = time.time()

                    try:
                        success = milkyway_timelapse_generator.generate_video(cleanup=True)

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

                self.log_message.emit("=" * 60)
                logger.info(f"=" * 60)
                self.finished.emit(result)

        except Exception as e:
            logger.error(f"处理失败: {e}")
            import traceback
            traceback.print_exc()
            self.error.emit(str(e))

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
        self.setGeometry(100, 100, 1200, 800)

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

        # 初始化 UI
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        # 应用全局样式表
        self.setStyleSheet(get_complete_stylesheet())

        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)

        # 创建内容分割器（左右布局）
        content_splitter = QSplitter(Qt.Horizontal)

        # 创建左侧面板容器
        left_panel = QWidget()
        left_panel.setMinimumWidth(420)  # 设置最小宽度，避免太窄
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # 创建各个 Panel
        self.file_list_panel = FileListPanel(self.tr)
        self.params_panel = ParametersPanel(self.tr)
        self.control_panel = ControlPanel(self.tr)

        # 添加到左侧布局
        left_layout.addWidget(self.file_list_panel)
        left_layout.addWidget(self.params_panel)
        left_layout.addWidget(self.control_panel)
        left_layout.addStretch()

        # 创建右侧面板
        self.preview_panel = PreviewPanel(self.tr)

        # 添加到分割器
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(self.preview_panel)
        content_splitter.setStretchFactor(0, 1)  # 左侧占 1/3
        content_splitter.setStretchFactor(1, 2)  # 右侧占 2/3

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

        # ControlPanel 信号
        self.control_panel.start_clicked.connect(self.start_processing)
        self.control_panel.stop_clicked.connect(self.stop_processing)

        # FileListPanel 打开输出目录信号
        self.file_list_panel.open_output_clicked.connect(self.open_output_dir)

    def _on_files_selected(self, files: List[Path]):
        """文件列表改变时的处理"""
        # 根据文件列表更新开始按钮状态
        can_start = len(files) > 0
        self.control_panel.set_start_enabled(can_start)

    def _preview_single_file(self, file_path: Path):
        """预览单个文件"""
        try:
            from core.raw_processor import RawProcessor
            processor = RawProcessor()

            # 使用当前的 RAW 参数
            raw_params = self.params_panel.get_raw_params()
            img = processor.process(file_path, **raw_params)

            # 更新预览
            self.preview_panel.update_preview(img)
            logger.info(f"预览文件: {file_path.name}")
        except Exception as e:
            logger.error(f"预览失败: {e}")
            QMessageBox.warning(
                self,
                self.tr.tr("warning") if hasattr(self.tr, 'tr') else "警告",
                f"无法预览文件: {file_path.name}\n错误: {str(e)}"
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
            self.params_panel.get_raw_params(),
            enable_alignment=False,
            enable_gap_filling=self.params_panel.is_gap_filling_enabled(),
            gap_fill_method=gap_fill_method,
            gap_size=gap_size,
            comet_fade_factor=self.params_panel.get_comet_fade_factor(),
            enable_timelapse=self.params_panel.is_timelapse_enabled(),
            enable_simple_timelapse=self.params_panel.is_simple_timelapse_enabled(),
            output_dir=output_dir,
            video_fps=video_fps,
            translator=self.tr,
        )

        # 连接信号
        self.process_thread.progress.connect(self.control_panel.update_progress)
        self.process_thread.preview_update.connect(self.preview_panel.update_preview)
        self.process_thread.finished.connect(self.processing_finished)
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

    def processing_finished(self, result: np.ndarray):
        """处理完成"""
        self.result_image = result
        self.preview_panel.update_preview(result)

        # 获取输出目录
        output_dir = self.file_list_panel.get_output_dir()
        if not output_dir:
            output_dir = self.file_list_panel.get_all_files()[0].parent / "SuperStarTrail"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成文件名
        tiff_filename = self._generate_output_filename()
        tiff_path = output_dir / tiff_filename

        # 添加保存日志
        self.preview_panel.append_log("-" * 60)
        self.preview_panel.append_log("正在保存 TIFF 文件...")
        self.preview_panel.append_log(f"应用亮度拉伸 (1%-99.5%)...")

        # 保存 TIFF
        from core.exporter import ImageExporter
        exporter = ImageExporter()
        success = exporter.save_auto(self.result_image, tiff_path)

        if success:
            self.preview_panel.append_log(f"✅ TIFF 保存成功: {tiff_filename}")
        else:
            self.preview_panel.append_log(f"❌ TIFF 保存失败")

        self.preview_panel.append_log("=" * 60)
        self.preview_panel.append_log("🎉 全部完成！可以打开输出目录查看结果")

        # 更新按钮状态
        self.control_panel.set_idle_state(can_start=True)
        self.file_list_panel.set_open_output_enabled(True)

        if success:
            self.control_panel.update_status("✅ 合成完成")
            logger.info(f"合成完成！文件已保存到: {output_dir}")

            # 播放完成音效
            self.play_completion_sound()

            QMessageBox.information(
                self,
                self.tr.tr("msg_complete_title"),
                self.tr.tr("msg_complete_text").format(path=output_dir)
            )

            # 用户关闭对话框后，自动打开输出目录
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

        return FileNamingService.generate_output_filename(
            file_paths=all_files,
            stack_mode=self.params_panel.get_stack_mode(),
            white_balance=self.params_panel.get_white_balance(),
            comet_fade_factor=self.params_panel.get_comet_fade_factor() 
                if self.params_panel.get_stack_mode() == StackMode.COMET else None,
            enable_gap_filling=self.params_panel.is_gap_filling_enabled(),
            file_extension="tif"
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
