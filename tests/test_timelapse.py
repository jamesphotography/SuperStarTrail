"""
延时视频功能测试

测试使用 3 张图片生成延时视频
"""

from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.raw_processor import RawProcessor
from core.stacking_engine import StackingEngine, StackMode
import time

# 找到测试文件
test_dir = Path("/Users/jameszhenyu/PycharmProjects/SuperStarTrail/startrail-test/star-test")
raw_files = sorted(list(test_dir.glob("*.NEF")))[:5]  # 使用前 5 张

if not raw_files:
    print("❌ 未找到测试文件")
    exit(1)

print(f"找到 {len(raw_files)} 个文件:")
for f in raw_files:
    print(f"  - {f.name}")

print("\n" + "=" * 60)
print("开始测试延时视频生成")
print("=" * 60)

# 初始化处理器和引擎
processor = RawProcessor()

# 生成视频输出路径
output_video = test_dir / "test_timelapse.mp4"

engine = StackingEngine(
    mode=StackMode.LIGHTEN,
    enable_timelapse=True,
    timelapse_output_path=output_video,
)

# 处理每一张图片
start_time = time.time()

for i, raw_file in enumerate(raw_files):
    print(f"\n处理 [{i+1}/{len(raw_files)}]: {raw_file.name}")
    file_start = time.time()

    # 读取 RAW 文件
    img = processor.process(raw_file, white_balance="camera")

    # 添加到堆栈
    engine.add_image(img)

    file_duration = time.time() - file_start
    print(f"  完成，耗时: {file_duration:.2f} 秒")

# 获取最终结果
result = engine.get_result()
print(f"\n✅ 堆栈完成！形状: {result.shape}")

# 生成视频
print("\n" + "-" * 60)
print("生成延时视频...")
print("-" * 60)

video_start = time.time()
success = engine.finalize_timelapse(cleanup=True)
video_duration = time.time() - video_start

if success:
    print(f"✅ 视频生成成功！")
    print(f"   耗时: {video_duration:.2f} 秒")
    print(f"   保存至: {output_video}")
    print(f"   总帧数: {engine.timelapse_generator.get_frame_count()}")
    print(f"   视频时长: {engine.timelapse_generator.get_duration():.2f} 秒")
else:
    print(f"❌ 视频生成失败")

total_duration = time.time() - start_time
print(f"\n" + "=" * 60)
print(f"测试完成！总耗时: {total_duration:.2f} 秒")
print("=" * 60)
