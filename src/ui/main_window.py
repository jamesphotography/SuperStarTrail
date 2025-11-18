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
    QPushButton,
    QLabel,
    QFileDialog,
    QListWidget,
    QComboBox,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QCheckBox,
    QApplication,
    QTextEdit,
    QAction,
    QMenu,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage, QIcon
import numpy as np

from core.raw_processor import RawProcessor
from core.stacking_engine import StackingEngine, StackMode
from utils.logger import setup_logger
from utils.settings import get_settings
from utils.file_naming import FileNamingService
from ui.dialogs import AboutDialog, PreferencesDialog
from i18n import get_translator, set_language
from ui.styles import (
    get_complete_stylesheet,
    PRIMARY_BUTTON_STYLE,
    SUCCESS_BUTTON_STYLE,
    DANGER_BUTTON_STYLE,
    SECONDARY_BUTTON_STYLE,
    TITLE_LABEL_STYLE,
    SUBTITLE_LABEL_STYLE,
    INFO_LABEL_STYLE,
    PREVIEW_AREA_STYLE,
    LOG_TEXT_STYLE,
    COLORS,
)

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
        self.output_dir = output_dir
        self.translator = translator
        self.video_fps = video_fps
        self._stop_event = Event()  # 使用线程安全的 Event 替代布尔标志

    def run(self):
        """执行处理"""
        import time
        from utils.logger import setup_logger

        logger = setup_logger("ProcessThread")

        try:
            processor = RawProcessor()

            # 确定输出目录（如果未指定，使用默认的"彗星星轨"子目录）
            from pathlib import Path
            if self.output_dir is None:
                output_dir = self.file_paths[0].parent / "StarTrail"
            else:
                output_dir = self.output_dir

            # 创建输出目录
            output_dir.mkdir(parents=True, exist_ok=True)
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
            self.log_message.emit(f"延时视频: {'启用 (4K ' + str(self.video_fps) + 'FPS)' if self.enable_timelapse else '禁用'}")
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

                # 生成延时视频（如果启用）
                if self.enable_timelapse:
                    self.log_message.emit("-" * 60)
                    self.log_message.emit("正在生成延时视频...")
                    logger.info(f"-" * 60)
                    logger.info(f"正在生成延时视频...")
                    self.status_message.emit("正在生成延时视频...")
                    timelapse_start = time.time()

                    success = engine.finalize_timelapse(cleanup=True)

                    if success:
                        timelapse_duration = time.time() - timelapse_start
                        self.log_message.emit(f"✅ 延时视频生成完成，耗时: {timelapse_duration:.2f} 秒")
                        self.log_message.emit(f"视频保存至: {timelapse_output_path.name}")
                        logger.info(f"延时视频生成完成，耗时: {timelapse_duration:.2f} 秒")
                        logger.info(f"视频保存至: {timelapse_output_path}")
                        # 发送视频路径信号
                        self.timelapse_generated.emit(str(timelapse_output_path))
                    else:
                        self.log_message.emit("❌ 延时视频生成失败")
                        logger.error("延时视频生成失败")

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
    """主窗口类"""

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
        self.raw_files: List[Path] = []
        self.result_image: np.ndarray = None
        self.process_thread: ProcessThread = None
        self.output_dir: Path = None  # 输出目录
        self.timelapse_video_path: Path = None  # 延时视频路径

        # 预览性能优化：缓存拉伸参数，避免每次都计算百分位数
        self._preview_stretch_cache = None  # (p_low, p_high)
        self._preview_cache_valid = False

        # 初始化 UI
        self.init_ui()

    def init_ui(self):
        """初始化用户界面"""
        # 应用全局样式表
        self.setStyleSheet(get_complete_stylesheet())

        # 创建菜单栏
        self.create_menu_bar()

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        central_widget.setLayout(main_layout)

        # 左侧面板（文件列表和控制）
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel, 1)

        # 右侧面板（预览）
        right_panel = self.create_right_panel()
        main_layout.addWidget(right_panel, 2)

    def create_left_panel(self) -> QWidget:
        """创建左侧控制面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # 文件选择组
        file_group = QGroupBox(self.tr.tr("file_list"))
        file_layout = QVBoxLayout()

        self.btn_select_folder = QPushButton(f"📁 {self.tr.tr('select_directory')}")
        self.btn_select_folder.clicked.connect(self.select_folder)
        self.btn_select_folder.setToolTip(self.tr.tr('tooltip_select_folder'))
        self.btn_select_folder.setStyleSheet(PRIMARY_BUTTON_STYLE)
        file_layout.addWidget(self.btn_select_folder)

        # 输出目录选择
        output_dir_layout = QHBoxLayout()
        self.btn_select_output = QPushButton(f"💾 {self.tr.tr('select_directory')}")
        self.btn_select_output.clicked.connect(self.select_output_dir)
        self.btn_select_output.setToolTip(self.tr.tr('tooltip_output_dir') if hasattr(self.tr, 'tr') else "Select output directory")
        self.btn_select_output.setStyleSheet(SECONDARY_BUTTON_STYLE)
        output_dir_layout.addWidget(self.btn_select_output)

        self.label_output_dir = QLabel(self.tr.tr("no_directory_selected"))
        self.label_output_dir.setWordWrap(True)
        self.label_output_dir.setStyleSheet(INFO_LABEL_STYLE)
        output_dir_layout.addWidget(self.label_output_dir, 1)

        file_layout.addLayout(output_dir_layout)

        self.file_list = QListWidget()
        self.file_list.itemClicked.connect(self.preview_single_file)  # 单击预览
        file_layout.addWidget(self.file_list)

        self.label_file_count = QLabel(self.tr.tr("files_selected").format(count=0))
        self.label_file_count.setStyleSheet(INFO_LABEL_STYLE)
        file_layout.addWidget(self.label_file_count)

        file_group.setLayout(file_layout)
        layout.addWidget(file_group)

        # 参数设置组
        params_group = QGroupBox(self.tr.tr("parameters"))
        params_layout = QVBoxLayout()

        # 堆栈模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel(self.tr.tr("stack_mode")))
        self.combo_stack_mode = QComboBox()
        self.combo_stack_mode.addItems(
            [
                self.tr.tr("mode_lighten"),
                self.tr.tr("mode_comet"),
                self.tr.tr("mode_average"),
                self.tr.tr("mode_darken"),
            ]
        )
        self.combo_stack_mode.setCurrentIndex(0)  # 默认选择传统星轨
        self.combo_stack_mode.currentIndexChanged.connect(self.on_stack_mode_changed)
        mode_layout.addWidget(self.combo_stack_mode, 1)
        params_layout.addLayout(mode_layout)

        # 彗星尾巴长度（仅彗星模式显示）
        tail_layout = QHBoxLayout()
        self.label_comet_tail = QLabel(self.tr.tr("comet_tail"))
        tail_layout.addWidget(self.label_comet_tail)
        self.combo_comet_tail = QComboBox()
        self.combo_comet_tail.addItems([
            self.tr.tr("tail_short"),
            self.tr.tr("tail_medium"),
            self.tr.tr("tail_long")
        ])
        self.combo_comet_tail.setCurrentIndex(1)  # 默认"中"
        self.combo_comet_tail.setToolTip(
            "控制彗星尾巴的长度\n"
            "短: 快速消失，彗星感强\n"
            "中: 适中效果（推荐）\n"
            "长: 慢慢消失"
        )
        tail_layout.addWidget(self.combo_comet_tail, 1)
        params_layout.addLayout(tail_layout)
        # 默认隐藏彗星选项（因为默认模式是传统星轨）
        self.label_comet_tail.hide()
        self.combo_comet_tail.hide()

        # 白平衡选择
        wb_layout = QHBoxLayout()
        wb_layout.addWidget(QLabel(self.tr.tr("white_balance")))
        self.combo_white_balance = QComboBox()
        self.combo_white_balance.addItems([
            self.tr.tr("wb_camera"),
            self.tr.tr("wb_daylight"),
            self.tr.tr("wb_auto")
        ])
        wb_layout.addWidget(self.combo_white_balance, 1)
        params_layout.addLayout(wb_layout)

        # 间隔填充和延时视频选项（同一行）
        options_layout = QHBoxLayout()
        self.check_enable_gap_filling = QCheckBox(self.tr.tr("gap_filling_checked"))
        self.check_enable_gap_filling.setToolTip(
            "填补星点之间的间隔，使星轨更加连续流畅\n"
            "使用形态学算法，3像素间隔（适合大部分场景）\n"
            "性能影响：几乎无（仅在最后应用一次）"
        )
        self.check_enable_gap_filling.setChecked(True)  # 默认启用
        self.check_enable_gap_filling.stateChanged.connect(
            lambda state: self.check_enable_gap_filling.setText(
                self.tr.tr("gap_filling_checked") if state else self.tr.tr("gap_filling")
            )
        )
        options_layout.addWidget(self.check_enable_gap_filling)

        self.check_enable_timelapse = QCheckBox(self.tr.tr("timelapse_video"))
        self.check_enable_timelapse.setToolTip(
            "将星轨形成过程制作为延时视频\n"
            "展示从第一张到最后一张的星轨变长过程\n"
            "分辨率: 3840×2160 (4K)\n"
            "帧率: 25 FPS（默认值）\n"
            "100张图片 ≈ 4秒视频\n"
            "额外处理时间：约 1-2 分钟"
        )
        self.check_enable_timelapse.setChecked(False)  # 默认关闭
        self.check_enable_timelapse.stateChanged.connect(
            lambda state: self.check_enable_timelapse.setText(
                self.tr.tr("timelapse_checked") if state else self.tr.tr("timelapse_video")
            )
        )
        options_layout.addWidget(self.check_enable_timelapse)
        options_layout.addStretch()
        params_layout.addLayout(options_layout)

        params_group.setLayout(params_layout)
        layout.addWidget(params_group)

        # 处理控制（同一行）
        control_layout = QHBoxLayout()

        self.btn_start = QPushButton(self.tr.tr("start"))
        self.btn_start.clicked.connect(self.start_processing)
        self.btn_start.setEnabled(False)
        # 缩小按钮尺寸
        self.btn_start.setStyleSheet(SUCCESS_BUTTON_STYLE + "padding: 8px 16px; font-size: 13px;")
        control_layout.addWidget(self.btn_start)

        self.btn_stop = QPushButton(self.tr.tr("stop"))
        self.btn_stop.clicked.connect(self.stop_processing)
        self.btn_stop.setEnabled(False)
        self.btn_stop.setStyleSheet(DANGER_BUTTON_STYLE + "padding: 8px 16px; font-size: 13px;")
        control_layout.addWidget(self.btn_stop)

        # 状态标签
        self.label_status = QLabel(self.tr.tr("ready"))
        self.label_status.setAlignment(Qt.AlignCenter)
        self.label_status.setStyleSheet(f"""
            padding: 8px 12px;
            background-color: {COLORS['bg_light']};
            border-radius: 5px;
            color: {COLORS['text_primary']};
            font-size: 11px;
            font-weight: bold;
        """)
        control_layout.addWidget(self.label_status, 1)

        layout.addLayout(control_layout)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setFormat("%p% (%v/%m)")  # 显示百分比和进度
        layout.addWidget(self.progress_bar)

        layout.addStretch()
        return panel

    def create_right_panel(self) -> QWidget:
        """创建右侧预览面板"""
        panel = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        panel.setLayout(layout)

        # 标题栏（带 Logo）
        title_layout = QHBoxLayout()
        title_layout.addStretch()

        # Logo 图标
        logo_path = Path(__file__).parent.parent / "resources" / "logo.png"
        if logo_path.exists():
            logo_label = QLabel()
            logo_pixmap = QPixmap(str(logo_path)).scaled(
                32, 32, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            logo_label.setPixmap(logo_pixmap)
            title_layout.addWidget(logo_label)

        # 标题文字
        title = QLabel(self.tr.tr("preview"))
        title.setStyleSheet(TITLE_LABEL_STYLE)
        title_layout.addWidget(title)
        title_layout.addStretch()

        layout.addLayout(title_layout)

        # 预览区域
        self.preview_label = QLabel(self.tr.tr("drop_files_here"))
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(PREVIEW_AREA_STYLE)
        self.preview_label.setMinimumSize(800, 400)
        layout.addWidget(self.preview_label)

        # 操作按钮（同一行）
        action_buttons_layout = QHBoxLayout()

        self.btn_play_video = QPushButton(self.tr.tr("play_video"))
        self.btn_play_video.clicked.connect(self.play_timelapse_video)
        self.btn_play_video.setEnabled(False)
        self.btn_play_video.setStyleSheet(PRIMARY_BUTTON_STYLE + "padding: 8px 16px; font-size: 12px;")
        action_buttons_layout.addWidget(self.btn_play_video)

        self.btn_open_output = QPushButton(self.tr.tr("open_output_dir"))
        self.btn_open_output.clicked.connect(self.open_output_dir)
        self.btn_open_output.setEnabled(False)
        self.btn_open_output.setStyleSheet(SECONDARY_BUTTON_STYLE + "padding: 8px 16px; font-size: 12px;")
        action_buttons_layout.addWidget(self.btn_open_output)

        layout.addLayout(action_buttons_layout)

        # 添加日志输出区域
        log_label = QLabel(f"📋 {self.tr.tr('processing_log')}")
        log_label.setStyleSheet(SUBTITLE_LABEL_STYLE)
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        self.log_text.setStyleSheet(LOG_TEXT_STYLE)
        layout.addWidget(self.log_text)

        return panel

    def select_folder(self):
        """选择包含图片文件的文件夹"""
        folder = QFileDialog.getExistingDirectory(self, self.tr.tr("select_directory"))
        if not folder:
            return

        folder_path = Path(folder)
        processor = RawProcessor()

        # 扫描 RAW 文件
        self.raw_files = []
        for file in folder_path.iterdir():
            if processor.is_raw_file(file):
                self.raw_files.append(file)

        # 按文件名排序（重要！确保堆栈顺序正确）
        self.raw_files.sort(key=lambda x: x.name)

        # 更新 UI
        self.file_list.clear()
        for file in self.raw_files:
            self.file_list.addItem(file.name)

        self.label_file_count.setText(self.tr.tr("files_selected").format(count=len(self.raw_files)))
        self.btn_start.setEnabled(len(self.raw_files) > 0)

        # 设置默认输出目录：原片目录/StarTrail/
        if len(self.raw_files) > 0:
            self.output_dir = folder_path / "StarTrail"
            self.label_output_dir.setText(self.tr.tr("output_to").format(path=self.output_dir))

        # 自动预览第一张图片
        if len(self.raw_files) > 0:
            self.label_status.setText(self.tr.tr("loading_preview").format(filename=self.raw_files[0].name))
            try:
                raw_params = self.get_raw_params()
                image = processor.process(self.raw_files[0], **raw_params)
                self.update_preview(image)
                self.label_status.setText(self.tr.tr("preview_file").format(filename=self.raw_files[0].name))
            except Exception as e:
                self.label_status.setText(self.tr.tr("preview_failed").format(error=str(e)))
                logger.error(f"自动预览第一张失败: {e}")

    def select_output_dir(self):
        """选择输出目录"""
        # 默认目录：如果已设置则使用当前输出目录，否则使用桌面
        default_dir = str(self.output_dir) if self.output_dir else str(Path.home() / "Desktop")

        folder = QFileDialog.getExistingDirectory(self, self.tr.tr("select_directory"), default_dir)
        if folder:
            self.output_dir = Path(folder)
            self.label_output_dir.setText(self.tr.tr("output_to").format(path=self.output_dir))

    def on_stack_mode_changed(self, index):
        """堆栈模式改变时的回调"""
        # 只在彗星模式(index=1)时显示尾巴长度选项
        is_comet_mode = (index == 1)
        self.label_comet_tail.setVisible(is_comet_mode)
        self.combo_comet_tail.setVisible(is_comet_mode)

    def preview_single_file(self, item):
        """预览单个NEF文件（双击文件列表时触发）"""
        # 获取选中文件的索引
        index = self.file_list.row(item)
        if 0 <= index < len(self.raw_files):
            file_path = self.raw_files[index]

            # 在状态栏显示正在加载
            self.label_status.setText(self.tr.tr("loading_preview").format(filename=file_path.name))

            try:
                # 读取RAW文件（注意：process 方法需要 Path 对象，不是字符串）
                processor = RawProcessor()
                raw_params = self.get_raw_params()
                image = processor.process(file_path, **raw_params)

                # 更新预览
                self.update_preview(image)
                self.label_status.setText(self.tr.tr("preview_file").format(filename=file_path.name))

            except Exception as e:
                self.label_status.setText(self.tr.tr("preview_failed").format(error=str(e)))
                logger.error(f"预览文件失败: {e}")

    def get_stack_mode(self) -> StackMode:
        """获取选择的堆栈模式"""
        mode_map = {
            0: StackMode.LIGHTEN,
            1: StackMode.COMET,
            2: StackMode.AVERAGE,
            3: StackMode.DARKEN,
        }
        return mode_map[self.combo_stack_mode.currentIndex()]

    def get_raw_params(self) -> dict:
        """获取 RAW 处理参数"""
        wb_map = {0: "camera", 1: "daylight", 2: "auto"}
        return {
            "white_balance": wb_map[self.combo_white_balance.currentIndex()],
            "exposure_compensation": 0.0,
        }

    def start_processing(self):
        """开始处理"""
        if not self.raw_files:
            return

        # 禁用开始按钮，启用停止按钮
        self.btn_start.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_open_output.setEnabled(False)

        # 重置进度条
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.raw_files))
        self.label_status.setText(self.tr.tr("preparing"))

        # 重置预览缓存（新处理开始）
        self._preview_cache_valid = False
        self._preview_stretch_cache = None

        # 从配置获取参数
        settings = get_settings()
        gap_fill_method = settings.get_gap_fill_method()
        gap_size = settings.get_gap_size()

        # 获取彗星模式参数
        comet_fade_map = {
            0: 0.96,  # 短
            1: 0.97,  # 中
            2: 0.98,  # 长
        }
        comet_fade_factor = comet_fade_map[self.combo_comet_tail.currentIndex()]

        # 从设置获取视频 FPS
        settings = get_settings()
        video_fps = settings.get_video_fps()

        # 创建并启动处理线程
        self.process_thread = ProcessThread(
            self.raw_files,
            self.get_stack_mode(),
            self.get_raw_params(),
            enable_alignment=False,  # 星轨摄影不需要对齐
            enable_gap_filling=self.check_enable_gap_filling.isChecked(),
            gap_fill_method=gap_fill_method,
            gap_size=gap_size,
            comet_fade_factor=comet_fade_factor,
            enable_timelapse=self.check_enable_timelapse.isChecked(),
            output_dir=self.output_dir,
            video_fps=video_fps,
            translator=self.tr,
        )
        self.process_thread.progress.connect(self.update_progress)
        self.process_thread.preview_update.connect(self.update_preview)
        self.process_thread.finished.connect(self.processing_finished)
        self.process_thread.error.connect(self.processing_error)
        self.process_thread.status_message.connect(self.update_status)
        self.process_thread.timelapse_generated.connect(self.on_timelapse_generated)
        self.process_thread.log_message.connect(self.append_log)
        self.process_thread.start()

    def stop_processing(self):
        """停止处理"""
        if self.process_thread:
            self.process_thread.stop()
            self.btn_stop.setEnabled(False)

    def update_progress(self, current: int, total: int):
        """更新进度条"""
        self.progress_bar.setValue(current)

    def update_status(self, message: str):
        """更新状态标签"""
        self.label_status.setText(message)

    def append_log(self, message: str):
        """添加日志消息到日志区域"""
        self.log_text.append(message)
        # 自动滚动到底部
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

    def update_preview(self, image: np.ndarray):
        """更新预览图像（自动曝光优化，使用缓存提升性能）"""
        import time
        start_time = time.time()

        # 从配置获取预览参数
        settings = get_settings()
        max_size = settings.get_preview_max_size()

        # 先缩放再做亮度拉伸，大幅提升速度
        h, w = image.shape[:2]

        # 先缩小图像以加快后续处理
        if max(h, w) > max_size:
            scale = max_size / max(h, w)
            new_h, new_w = int(h * scale), int(w * scale)
            import cv2
            image_small = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        else:
            image_small = image

        # 转换为 8-bit 用于显示，使用自动拉伸提升亮度
        if image_small.dtype == np.uint16:
            # 使用缓存的拉伸参数（仅在第一帧或缓存失效时计算）
            if not self._preview_cache_valid or self._preview_stretch_cache is None:
                # 从配置获取百分位数
                percentile_low, percentile_high = settings.get_preview_percentiles()
                # 对缩小后的图像使用百分位数拉伸（O(n log n)，较慢）
                p_low = np.percentile(image_small, percentile_low)
                p_high = np.percentile(image_small, percentile_high)
                self._preview_stretch_cache = (p_low, p_high)
                self._preview_cache_valid = True
                logger.debug(f"预览拉伸参数已缓存: low={p_low:.1f}, high={p_high:.1f}")
            else:
                # 使用缓存的参数（快速）
                p_low, p_high = self._preview_stretch_cache

            # 拉伸到 0-255
            img_stretched = np.clip((image_small - p_low) / (p_high - p_low) * 255, 0, 255)
            img_8bit = img_stretched.astype(np.uint8)
        else:
            img_8bit = image_small

        # 转换为 QPixmap
        h, w, c = img_8bit.shape
        bytes_per_line = c * w
        q_img = QImage(img_8bit.data, w, h, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(q_img)

        self.preview_label.setPixmap(pixmap)

        # 强制刷新UI
        self.preview_label.update()
        QApplication.processEvents()

        elapsed = time.time() - start_time
        logger.debug(f"预览更新完成，耗时: {elapsed:.3f}秒")

    def processing_finished(self, result: np.ndarray):
        """处理完成"""
        self.result_image = result
        self.update_preview(result)

        # 自动保存 TIFF 文件
        if self.output_dir:
            output_dir = self.output_dir
        else:
            output_dir = self.raw_files[0].parent / "StarTrail"

        output_dir.mkdir(parents=True, exist_ok=True)

        # 生成智能文件名
        tiff_filename = self.generate_output_filename()
        tiff_path = output_dir / tiff_filename

        # 添加保存日志
        self.append_log("-" * 60)
        self.append_log("正在保存 TIFF 文件...")
        self.append_log(f"应用亮度拉伸 (1%-99.5%)...")

        # 保存 TIFF
        from core.exporter import ImageExporter
        exporter = ImageExporter()
        success = exporter.save_auto(self.result_image, tiff_path)

        if success:
            self.append_log(f"✅ TIFF 保存成功: {tiff_filename}")
        else:
            self.append_log(f"❌ TIFF 保存失败")

        self.append_log("=" * 60)
        self.append_log("🎉 全部完成！可以打开输出目录查看结果")

        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)
        self.btn_open_output.setEnabled(True)

        if success:
            # 状态栏只显示简短信息
            self.label_status.setText("✅ 合成完成")
            self.label_status.setStyleSheet("padding: 5px; background: #d4edda; border-radius: 3px; color: #155724;")

            # 详细路径信息记录到日志
            logger.info(f"合成完成！文件已保存到: {output_dir}")

            # 播放完成音效
            self.play_completion_sound()

            QMessageBox.information(
                self,
                self.tr.tr("msg_complete_title"),
                self.tr.tr("msg_complete_text").format(path=output_dir)
            )
        else:
            self.label_status.setText("❌ 合成完成但保存失败")
            self.label_status.setStyleSheet("padding: 5px; background: #f8d7da; border-radius: 3px; color: #721c24;")
            QMessageBox.warning(
                self,
                self.tr.tr("msg_save_failed_title"),
                self.tr.tr("msg_save_failed_text")
            )

    def processing_error(self, error_msg: str):
        """处理错误"""
        self.btn_start.setEnabled(True)
        self.btn_stop.setEnabled(False)

        self.label_status.setText(self.tr.tr("failed"))
        self.label_status.setStyleSheet("padding: 5px; background: #f8d7da; border-radius: 3px; color: #721c24;")

        QMessageBox.critical(
            self,
            self.tr.tr("msg_error_title"),
            self.tr.tr("msg_error_text").format(error=error_msg)
        )

    def open_output_dir(self):
        """打开输出目录"""
        if self.output_dir and self.output_dir.exists():
            import subprocess
            import platform

            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(self.output_dir)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(self.output_dir)])
            else:  # Linux
                subprocess.run(["xdg-open", str(self.output_dir)])
        else:
            QMessageBox.warning(self, "提示", "输出目录不存在")

    def on_timelapse_generated(self, video_path: str):
        """处理延时视频生成完成事件"""
        from pathlib import Path
        self.timelapse_video_path = Path(video_path)
        self.btn_play_video.setEnabled(True)
        logger.info(f"延时视频已准备: {self.timelapse_video_path}")

    def play_timelapse_video(self):
        """播放延时视频（使用系统默认播放器）"""
        if self.timelapse_video_path and self.timelapse_video_path.exists():
            import subprocess
            import platform

            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(self.timelapse_video_path)])
            elif platform.system() == "Windows":
                subprocess.run(["start", str(self.timelapse_video_path)], shell=True)
            else:  # Linux
                subprocess.run(["xdg-open", str(self.timelapse_video_path)])
        else:
            QMessageBox.warning(self, "提示", "延时视频文件不存在")

    def play_completion_sound(self):
        """播放完成音效"""
        try:
            import subprocess
            import platform

            # ending.mp3 在项目根目录
            sound_path = Path(__file__).parent.parent.parent / "ending.mp3"

            if sound_path.exists():
                if platform.system() == "Darwin":  # macOS
                    # 使用 afplay 命令播放音频（macOS 内置）
                    subprocess.Popen(["afplay", str(sound_path)])
                elif platform.system() == "Windows":
                    # Windows 使用 winsound
                    import winsound
                    winsound.PlaySound(str(sound_path), winsound.SND_FILENAME | winsound.SND_ASYNC)
                else:  # Linux
                    # Linux 使用 aplay 或 paplay
                    try:
                        subprocess.Popen(["paplay", str(sound_path)])
                    except:
                        subprocess.Popen(["aplay", str(sound_path)])
            else:
                logger.warning(f"完成音效文件不存在: {sound_path}")
        except Exception as e:
            logger.error(f"播放完成音效失败: {e}")

    def generate_output_filename(self) -> str:
        """生成智能输出文件名（使用统一的文件命名服务）"""
        if not self.raw_files or len(self.raw_files) == 0:
            return "star_trail.tif"

        # 获取当前设置
        stack_mode = self.get_stack_mode()
        white_balance = ["camera", "daylight", "auto"][self.combo_white_balance.currentIndex()]
        comet_fade_factor = None
        if stack_mode == StackMode.COMET:
            comet_fade_map = {0: 0.96, 1: 0.97, 2: 0.98}
            comet_fade_factor = comet_fade_map[self.combo_comet_tail.currentIndex()]

        # 使用文件命名服务
        return FileNamingService.generate_output_filename(
            file_paths=self.raw_files,
            stack_mode=stack_mode,
            white_balance=white_balance,
            comet_fade_factor=comet_fade_factor,
            enable_gap_filling=self.check_enable_gap_filling.isChecked(),
            file_extension="tif"
        )

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu(self.tr.tr("menu_file"))

        # 打开文件夹
        open_folder_action = QAction(self.tr.tr("menu_open_folder"), self)
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.triggered.connect(self.select_folder)
        file_menu.addAction(open_folder_action)

        # 选择输出目录
        output_dir_action = QAction(self.tr.tr("menu_select_output"), self)
        output_dir_action.triggered.connect(self.select_output_dir)
        file_menu.addAction(output_dir_action)

        file_menu.addSeparator()

        # 退出
        exit_action = QAction(self.tr.tr("menu_exit"), self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 编辑菜单
        edit_menu = menubar.addMenu(self.tr.tr("menu_edit"))

        # 偏好设置
        preferences_action = QAction(self.tr.tr("menu_preferences"), self)
        preferences_action.setShortcut("Ctrl+,")
        preferences_action.triggered.connect(self.show_preferences)
        edit_menu.addAction(preferences_action)

        # 处理菜单
        process_menu = menubar.addMenu(self.tr.tr("menu_process"))

        # 开始处理
        start_action = QAction(self.tr.tr("menu_start"), self)
        start_action.setShortcut("Ctrl+R")
        start_action.triggered.connect(self.start_processing)
        process_menu.addAction(start_action)

        # 停止处理
        stop_action = QAction(self.tr.tr("menu_stop"), self)
        stop_action.setShortcut("Ctrl+.")
        stop_action.triggered.connect(self.stop_processing)
        process_menu.addAction(stop_action)

        process_menu.addSeparator()

        # 保存结果
        save_action = QAction(self.tr.tr("menu_save"), self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_result)
        process_menu.addAction(save_action)

        # 窗口菜单
        window_menu = menubar.addMenu(self.tr.tr("menu_window"))

        # 最小化
        minimize_action = QAction(self.tr.tr("menu_minimize"), self)
        minimize_action.setShortcut("Ctrl+M")
        minimize_action.triggered.connect(self.showMinimized)
        window_menu.addAction(minimize_action)

        # 缩放
        zoom_action = QAction(self.tr.tr("menu_zoom"), self)
        zoom_action.triggered.connect(self.toggle_maximized)
        window_menu.addAction(zoom_action)

        # 帮助菜单
        help_menu = menubar.addMenu(self.tr.tr("menu_help"))

        # 使用指南
        guide_action = QAction(self.tr.tr("menu_guide"), self)
        guide_action.triggered.connect(self.show_guide)
        help_menu.addAction(guide_action)

        help_menu.addSeparator()

        # 关于
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
            # 如果用户点击了确定，可以在这里保存设置
            logger.info("偏好设置已更新")

    def show_guide(self):
        """显示使用指南"""
        guide_text = """
        <h2>彗星星轨 - 使用指南</h2>

        <h3>基本流程：</h3>
        <ol>
            <li><b>选择文件：</b>点击"选择图片目录"，选择包含照片的文件夹<br>
            支持格式：RAW (CR2, NEF, ARW等)、TIFF、JPG、PNG</li>
            <li><b>选择模式：</b>
                <ul>
                    <li><b>常规星轨：</b>标准的星轨叠加效果</li>
                    <li><b>彗星星轨：</b>模拟彗星尾巴的渐变效果</li>
                </ul>
            </li>
            <li><b>调整参数：</b>
                <ul>
                    <li><b>RAW处理：</b>调整曝光补偿和白平衡</li>
                    <li><b>彗星衰减因子：</b>控制尾巴长度（仅彗星模式）</li>
                    <li><b>星点对齐：</b>补偿地球自转导致的星点偏移</li>
                    <li><b>间隙填充：</b>填补由于间隔拍摄产生的空隙</li>
                </ul>
            </li>
            <li><b>开始处理：</b>点击"开始处理"按钮</li>
            <li><b>保存结果：</b>处理完成后点击"保存结果"</li>
        </ol>

        <h3>彗星模式说明：</h3>
        <p>彗星模式会创建渐变的尾巴效果：</p>
        <ul>
            <li>衰减因子 0.90-0.95：短尾巴</li>
            <li>衰减因子 0.96-0.98：中等尾巴（推荐）</li>
            <li>衰减因子 0.99+：长尾巴</li>
        </ul>

        <h3>延时视频：</h3>
        <p>勾选"生成延时视频"可以将处理过程制作成视频，展示星轨形成的动态过程。</p>

        <h3>输出位置：</h3>
        <p>默认输出到：原片目录/彗星星轨/</p>
        <p>可通过"选择输出目录"自定义输出位置。</p>
        """

        msg = QMessageBox(self)
        msg.setWindowTitle("使用指南")
        msg.setTextFormat(Qt.RichText)
        msg.setText(guide_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.button(QMessageBox.Ok).setText("关闭")
        msg.exec_()

    def toggle_maximized(self):
        """切换最大化状态"""
        if self.isMaximized():
            self.showNormal()
        else:
            self.showMaximized()

    def stop_processing(self):
        """停止处理"""
        if self.process_thread and self.process_thread.isRunning():
            self.process_thread._is_running = False
            self.process_thread.wait()
            logger.info("处理已停止")

    def save_result(self):
        """手动保存结果"""
        if self.result_image is None:
            QMessageBox.warning(self, "警告", "没有可保存的结果\n请先处理图片")
            return

        # 让用户选择保存位置
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "保存星轨图片",
            str(Path.home() / "StarTrail.tif"),
            "TIFF 文件 (*.tif *.tiff);;PNG 文件 (*.png);;JPEG 文件 (*.jpg *.jpeg)"
        )

        if not file_path:
            return

        try:
            from core.output_exporter import OutputExporter
            exporter = OutputExporter()

            file_path = Path(file_path)

            # 根据文件扩展名选择保存格式
            if file_path.suffix.lower() in ['.tif', '.tiff']:
                success = exporter.save_auto(self.result_image, file_path)
            elif file_path.suffix.lower() == '.png':
                import imageio
                # 转换为 8-bit
                image_8bit = (self.result_image * 255).astype(np.uint8)
                imageio.imwrite(file_path, image_8bit)
                success = True
            elif file_path.suffix.lower() in ['.jpg', '.jpeg']:
                import imageio
                # 转换为 8-bit
                image_8bit = (self.result_image * 255).astype(np.uint8)
                imageio.imwrite(file_path, image_8bit, quality=95)
                success = True
            else:
                success = exporter.save_auto(self.result_image, file_path)

            if success:
                QMessageBox.information(self, "成功", f"文件已保存至:\n{file_path}")
                logger.info(f"手动保存成功: {file_path}")
            else:
                QMessageBox.warning(self, "错误", "保存文件失败")
                logger.error(f"手动保存失败: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存文件时出错:\n{str(e)}")
            logger.error(f"保存文件异常: {e}", exc_info=True)
