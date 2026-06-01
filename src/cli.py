"""
SuperStarTrail CLI

用法:
  sst stack <dir>               基础星轨合成
  sst stack <dir> --mode comet  彗星模式
  sst stack <dir> --fill-gaps   启用间隔填充
  sst stack <dir> --timelapse   生成星轨延时视频
  sst stack <dir> --milkyway    生成银河延时视频
  sst stack <dir> --remove-satellites  去除卫星划痕
  sst info <file>               查看 RAW 文件元数据
  sst export <file>             转换/导出图像
"""

import argparse
import sys
import time
from pathlib import Path


def _setup_path():
    """确保 src/ 在 Python 路径中"""
    src_dir = Path(__file__).parent
    if str(src_dir) not in sys.path:
        sys.path.insert(0, str(src_dir))


_setup_path()


# ─────────────────────────────────────────────
# 子命令: info
# ─────────────────────────────────────────────

def cmd_info(args):
    """显示 RAW 文件的元数据（从内嵌缩略图读取 EXIF）"""
    import io
    import rawpy
    from PIL import Image
    from PIL.ExifTags import TAGS
    from core.raw_processor import RawProcessor

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"错误: 文件不存在 - {file_path}")
        return 1

    print(f"\n文件: {file_path.name}")
    print(f"大小: {file_path.stat().st_size / 1024 / 1024:.1f} MB")
    print("-" * 40)

    try:
        with rawpy.imread(str(file_path)) as raw:
            # 分辨率来自 rawpy
            s = raw.sizes
            print(f"  {'分辨率':<10}: {s.width} x {s.height}  (裁剪后 {s.crop_width} x {s.crop_height})")

            # EXIF 从内嵌缩略图中读取
            try:
                thumb = raw.extract_thumb()
                img = Image.open(io.BytesIO(thumb.data))
                exif = img._getexif() or {}
                tag_map = {TAGS.get(k, k): v for k, v in exif.items()}

                fields = [
                    ("品牌",   "Make"),
                    ("型号",   "Model"),
                    ("ISO",    "ISOSpeedRatings"),
                    ("快门",   "ExposureTime"),
                    ("光圈",   "FNumber"),
                    ("焦距",   "FocalLength"),
                    ("拍摄时间", "DateTimeOriginal"),
                    ("镜头型号", "LensModel"),
                ]
                for label, key in fields:
                    val = tag_map.get(key)
                    if val is None:
                        continue
                    if key == "ExposureTime":
                        val = f"{val}s" if val >= 1 else f"1/{round(1/val)}s"
                    elif key == "FNumber":
                        val = f"f/{val}"
                    elif key == "FocalLength":
                        val = f"{val}mm"
                    print(f"  {label:<10}: {val}")
            except Exception:
                print("  (EXIF 读取失败，仅显示分辨率)")
    except Exception as e:
        if RawProcessor.is_unsupported_raw_exception(e):
            print(f"错误: {file_path.name}: {RawProcessor.UNSUPPORTED_COMPRESSED_RAW_MESSAGE}")
            return 1
        print(f"错误: 无法读取文件 - {e}")
        return 1

    print()
    return 0


# ─────────────────────────────────────────────
# 子命令: stack
# ─────────────────────────────────────────────

def cmd_stack(args):
    """星轨合成主流程"""
    from core.raw_processor import RawProcessor
    from core.stacking_engine import StackingEngine, StackMode
    from core.exporter import ImageExporter
    from utils.file_naming import FileNamingService

    source_dir = Path(args.dir)
    if not source_dir.exists():
        print(f"错误: 目录不存在 - {source_dir}")
        return 1

    # 扫描文件
    processor = RawProcessor()
    raw_exts = RawProcessor.SUPPORTED_RAW_FORMATS
    jpg_exts = {".jpg", ".jpeg"}

    candidate_files = RawProcessor.scan_directory(source_dir)
    raw_files = sorted([f for f in candidate_files if f.suffix.lower() in raw_exts])
    jpg_files = sorted([f for f in candidate_files if f.suffix.lower() in jpg_exts])
    other_files = sorted([
        f for f in candidate_files
        if f.suffix.lower() not in raw_exts and f.suffix.lower() not in jpg_exts
    ])

    # 同名 RAW+JPG 配对时，按 --jpg 参数决定使用哪种格式
    raw_stems = {f.stem for f in raw_files}
    jpg_stems = {f.stem for f in jpg_files}
    common_stems = raw_stems & jpg_stems

    if common_stems:
        if args.jpg:
            # 去掉与 JPG 同名的 RAW
            raw_files = [f for f in raw_files if f.stem not in common_stems]
        else:
            # 默认：去掉与 RAW 同名的 JPG
            jpg_files = [f for f in jpg_files if f.stem not in common_stems]
        if common_stems:
            fmt = "JPG" if args.jpg else "NEF/RAW"
            print(f"检测到 {len(common_stems)} 对同名 RAW+JPG，自动选择 {fmt}（可用 --jpg 切换）")

    all_files = sorted(raw_files + jpg_files + other_files, key=lambda f: f.name)

    if not all_files:
        print(f"错误: 目录中没有支持的图片文件 - {source_dir}")
        return 1

    # 限制处理数量（--limit）
    if args.limit and args.limit > 0:
        all_files = all_files[:args.limit]

    # 确定输出目录
    output_dir = Path(args.output) if args.output else source_dir / "SuperStarTrail"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 确定堆栈模式
    mode_map = {
        "lighten": StackMode.LIGHTEN,
        "comet":   StackMode.COMET,
        "average": StackMode.AVERAGE,
    }
    stack_mode = mode_map.get(args.mode, StackMode.LIGHTEN)

    # 延时视频路径
    timelapse_output_path = None
    if args.timelapse:
        video_filename = FileNamingService.generate_timelapse_filename(
            file_paths=all_files,
            stack_mode=stack_mode,
            comet_fade_factor=args.fade if stack_mode == StackMode.COMET else None,
            fps=args.fps,
        )
        timelapse_output_path = output_dir / video_filename

    # 银河延时生成器
    milkyway_generator = None
    if args.milkyway:
        from core.timelapse_generator import TimelapseGenerator
        milkyway_path = output_dir / f"MilkyWayTimelapse_{all_files[0].stem}-{all_files[-1].stem}_{args.fps}FPS.mp4"
        milkyway_generator = TimelapseGenerator(
            output_path=milkyway_path,
            fps=args.fps,
        )

    # 蒙版功能已临时禁用
    sky_mask = None
    _first = None
    if args.mask:
        print("⚠️  蒙版功能已临时禁用，忽略 --mask / --fg-mode 参数")

    # 初始化引擎
    fg_mode = StackMode.COMET if getattr(args, 'fg_mode', 'average') == 'comet' else StackMode.AVERAGE
    engine = StackingEngine(
        stack_mode,
        enable_gap_filling=args.fill_gaps,
        gap_fill_method=args.gap_method,
        gap_size=args.gap_size,
        enable_timelapse=args.timelapse,
        timelapse_output_path=timelapse_output_path,
        video_fps=args.fps,
        sky_mask=sky_mask,
        fg_mode=fg_mode,
    )

    if stack_mode == StackMode.COMET:
        engine.set_comet_fade_factor(args.fade)

    # 划痕检测器
    sat_filter = None
    if args.remove_satellites:
        from core.satellite_filter import SatelliteFilter
        sat_filter = SatelliteFilter()

    total = len(all_files)
    raw_params = {"white_balance": "camera"}

    print("=" * 60)
    print("SuperStarTrail CLI - 星轨合成")
    print("=" * 60)
    print(f"  文件数量  : {total}")
    print(f"  堆栈模式  : {stack_mode.value}")
    print(f"  输出目录  : {output_dir}")
    print(f"  间隔填充  : {'启用 (' + args.gap_method + ')' if args.fill_gaps else '禁用'}")
    print(f"  去卫星划痕: {'启用' if args.remove_satellites else '禁用'}")
    print(f"  星轨延时  : {'启用 (' + str(args.fps) + 'FPS)' if args.timelapse else '禁用'}")
    print(f"  银河延时  : {'启用 (' + str(args.fps) + 'FPS)' if args.milkyway else '禁用'}")
    print("=" * 60)

    start_time = time.time()
    failed_files = []
    satellite_removed_count = 0

    _cached_first_img = _first if sky_mask is not None else None

    for i, path in enumerate(all_files):
        file_start = time.time()
        try:
            if i == 0 and _cached_first_img is not None:
                img = _cached_first_img
            else:
                img = processor.process(path, rotation=args.rotation, **raw_params)

            if milkyway_generator:
                milkyway_generator.add_frame(img)

            satellite_mask = None
            if sat_filter is not None:
                satellite_mask = sat_filter.detect_streaks(img)
                if satellite_mask.any():
                    satellite_removed_count += 1
                    print(f"  [{i+1:3d}/{total}] 🛸 检测到划痕 ({satellite_mask.sum():,} px)")

            engine.add_image(img, satellite_mask=satellite_mask)

            elapsed = time.time() - start_time
            avg = elapsed / (i + 1)
            remaining = avg * (total - i - 1)
            rem_str = f"{int(remaining//60)}m{int(remaining%60)}s" if remaining >= 60 else f"{int(remaining)}s"
            print(f"[{i+1:3d}/{total}] {path.name}  {time.time()-file_start:.1f}s  剩余≈{rem_str}")

        except Exception as e:
            print(f"[{i+1:3d}/{total}] ⚠️  跳过: {path.name} ({e})")
            failed_files.append((path.name, str(e)))

    total_duration = time.time() - start_time
    print("-" * 60)
    print(f"堆栈完成  总耗时: {total_duration:.1f}s  平均: {total_duration/total:.1f}s/张")
    if args.remove_satellites:
        print(f"卫星划痕  检测到: {satellite_removed_count}/{total} 张")

    success_count = total - len(failed_files)
    if success_count == 0:
        print("错误: 没有成功读取任何图像，请检查 RAW/TIFF 格式是否受支持，或文件是否已损坏")
        return 1

    # 应用间隔填充 + 获取最终结果
    if args.fill_gaps:
        print("应用间隔填充...")
        gap_start = time.time()

    result = engine.get_result(apply_gap_filling=True)

    if args.fill_gaps:
        print(f"间隔填充完成  耗时: {time.time()-gap_start:.1f}s")

    # 生成星轨延时视频
    if args.timelapse:
        print("生成星轨延时视频...")
        tl_start = time.time()
        if engine.finalize_timelapse(cleanup=True):
            print(f"✅ 星轨延时视频  耗时: {time.time()-tl_start:.1f}s  => {timelapse_output_path.name}")
        else:
            print("❌ 星轨延时视频生成失败")

    # 生成银河延时视频
    if args.milkyway and milkyway_generator:
        print("生成银河延时视频...")
        mw_start = time.time()
        try:
            if milkyway_generator.generate_video(cleanup=True):
                print(f"✅ 银河延时视频  耗时: {time.time()-mw_start:.1f}s  => {milkyway_path.name}")
            else:
                print("❌ 银河延时视频生成失败")
        except Exception as e:
            print(f"❌ 银河延时视频生成失败: {e}")

    # 导出结果
    exporter = ImageExporter()
    output_filename = FileNamingService.generate_output_filename(
        file_paths=all_files,
        stack_mode=stack_mode,
        enable_gap_filling=args.fill_gaps,
        comet_fade_factor=args.fade if stack_mode == StackMode.COMET else None,
        has_mask=False,
        fg_mode=None,
    )
    tiff_path = output_dir / output_filename
    print(f"保存 TIFF: {tiff_path.name} ...")
    if exporter.save_tiff(result, tiff_path):
        size_mb = tiff_path.stat().st_size / 1024 / 1024
        print(f"✅ 已保存  {size_mb:.1f} MB  => {tiff_path}")
    else:
        print(f"❌ TIFF 保存失败")
        return 1

    # 汇总
    print("=" * 60)
    if failed_files:
        print(f"⚠️  成功 {total - len(failed_files)}/{total}，失败 {len(failed_files)} 个文件:")
        for name, err in failed_files:
            print(f"    • {name}: {err}")
    else:
        print(f"✅ 全部 {total} 个文件处理成功")
    print("=" * 60)
    return 0


# ─────────────────────────────────────────────
# 子命令: export
# ─────────────────────────────────────────────

def cmd_export(args):
    """转换/导出已有图像文件"""
    from core.raw_processor import RawProcessor
    from core.exporter import ImageExporter

    src = Path(args.file)
    if not src.exists():
        print(f"错误: 文件不存在 - {src}")
        return 1

    processor = RawProcessor()
    print(f"读取: {src.name} ...")
    img = processor.process(src)

    exporter = ImageExporter()
    fmt = args.format.lower()
    out_path = Path(args.output) if args.output else src.with_suffix(f".{fmt}")

    print(f"导出: {out_path} ...")
    if fmt in ("tif", "tiff"):
        ok = exporter.save_tiff(img, out_path, bits=args.bits)
    elif fmt in ("jpg", "jpeg"):
        ok = exporter.save_jpeg(img, out_path, quality=args.quality)
    elif fmt == "png":
        ok = exporter.save_png(img, out_path)
    else:
        print(f"错误: 不支持的输出格式 - {fmt}")
        return 1

    if ok:
        size_mb = out_path.stat().st_size / 1024 / 1024
        print(f"✅ 已保存  {size_mb:.1f} MB  => {out_path}")
        return 0
    else:
        print("❌ 导出失败")
        return 1


# ─────────────────────────────────────────────
# 参数解析
# ─────────────────────────────────────────────

def build_parser():
    parser = argparse.ArgumentParser(
        prog="sst",
        description="SuperStarTrail CLI - 星轨合成工具",
    )
    sub = parser.add_subparsers(dest="command", metavar="<command>")
    sub.required = True

    # ── info ──────────────────────────────────
    p_info = sub.add_parser("info", help="查看 RAW 文件元数据")
    p_info.add_argument("file", help="RAW 文件路径")

    # ── stack ─────────────────────────────────
    p_stack = sub.add_parser("stack", help="星轨合成")
    p_stack.add_argument("dir", help="图片目录")
    p_stack.add_argument("-o", "--output", help="输出目录（默认: <dir>/SuperStarTrail）")
    p_stack.add_argument("--mode", default="lighten",
                         choices=["lighten", "comet", "average"],
                         help="堆栈模式（默认: lighten）")
    p_stack.add_argument("--fade", type=float, default=0.97,
                         help="彗星模式衰减因子（默认: 0.97）")
    p_stack.add_argument("--fill-gaps", action="store_true",
                         help="启用间隔填充")
    p_stack.add_argument("--gap-method", default="morphological",
                         choices=["morphological", "linear", "motion_blur", "directional"],
                         help="间隔填充方法（默认: morphological）")
    p_stack.add_argument("--gap-size", type=int, default=3,
                         help="间隔大小像素（默认: 3）")
    p_stack.add_argument("--remove-satellites", action="store_true",
                         help="启用卫星/飞机划痕去除")
    p_stack.add_argument("--timelapse", action="store_true",
                         help="生成星轨延时视频")
    p_stack.add_argument("--milkyway", action="store_true",
                         help="生成银河延时视频")
    p_stack.add_argument("--fps", type=int, default=30,
                         help="延时视频帧率（默认: 30）")
    p_stack.add_argument("--limit", type=int, default=0,
                         help="只处理前 N 张（0 = 全部）")
    p_stack.add_argument("--jpg", action="store_true",
                         help="同名 RAW+JPG 时优先使用 JPG（默认优先 RAW）")
    p_stack.add_argument("--rotation", type=int, default=0,
                         choices=[0, 90, 180, 270],
                         help="顺时针旋转角度，竖拍素材用 90 或 270（默认: 0）")
    p_stack.add_argument("--mask", default=None,
                         help="天空蒙版 PNG 路径（功能已临时禁用）")
    p_stack.add_argument("--fg-mode", default="average",
                         choices=["average", "comet"],
                         help="蒙版地景区域的堆栈模式（功能已临时禁用）")

    # ── export ────────────────────────────────
    p_export = sub.add_parser("export", help="转换/导出图像")
    p_export.add_argument("file", help="源文件路径（RAW / TIFF / JPG）")
    p_export.add_argument("-o", "--output", help="输出文件路径")
    p_export.add_argument("--format", default="tiff",
                          choices=["tiff", "tif", "jpg", "jpeg", "png"],
                          help="输出格式（默认: tiff）")
    p_export.add_argument("--bits", type=int, default=16, choices=[8, 16, 32],
                          help="TIFF 位深度（默认: 16）")
    p_export.add_argument("--quality", type=int, default=95,
                          help="JPEG 质量 1-100（默认: 95）")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    handlers = {
        "info":   cmd_info,
        "stack":  cmd_stack,
        "export": cmd_export,
    }
    sys.exit(handlers[args.command](args))


if __name__ == "__main__":
    main()
