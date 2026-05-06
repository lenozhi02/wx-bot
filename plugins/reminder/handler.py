"""
Reminder Plugin — 定时提醒（支持提醒事项）

使用方法：
    r 30分钟后 吃药               → 相对时间 + 事项
    r 吃药 30分钟后               → 事项 + 相对时间
    r 2026-05-05 14:30 开会       → 完整时间 + 事项
    r 明天 14:30 提交报告         → 日期词 + 时间 + 事项
    r 5月5日 14:30 生日           → 中文月日 + 时间 + 事项
    r 14:30 休息                  → 今天 + 事项
    r 30分钟后                    → 仅时间（事项为空）
"""

import asyncio
import re
from datetime import datetime, timedelta, time as dt_time

from src.tasks.background import BackgroundTaskHandler
from src.tasks.base import TaskResult


def _now() -> datetime:
    """获取当前时间"""
    return datetime.now()


def _extract_time(text: str):
    """从文本中提取 HH:MM 时间"""
    if not text:
        return None
    m = re.search(r'(\d{1,2}):(\d{2})', text)
    if m:
        h, minute = int(m.group(1)), int(m.group(2))
        if 0 <= h < 24 and 0 <= minute < 60:
            return dt_time(h, minute)
    return None


def _remove_matched(text: str, start: int, end: int) -> str:
    """从文本中移除匹配到的片段，trim 后返回剩余文本"""
    result = (text[:start] + text[end:]).strip()
    # 清理多余的空格
    return re.sub(r'\s+', ' ', result)


def _parse_reminder(content: str) -> tuple[datetime | None, str]:
    """解析时间和提醒事项，返回 (datetime, subject)

    subject 为去掉时间部分后的剩余文本，可能为空字符串。
    """
    text = re.sub(r'^(r|remind|提醒)\s*', '', content, flags=re.IGNORECASE).strip()
    if not text:
        return None, ""

    now = _now()
    today = now.date()

    # ── 1. 相对时间：XX 秒后 / XX 分钟后 / XX 小时后 / XX 天后 ──
    for pattern, unit in [
        (r'(\d+)\s*秒(?:钟)?后', 'seconds'),
        (r'(\d+)\s*分钟(?:钟)?后', 'minutes'),
        (r'(\d+)\s*小时(?:后)?', 'hours'),
        (r'(\d+)\s*天后', 'days'),
    ]:
        m = re.search(pattern, text)
        if m:
            num = int(m.group(1))
            subject = _remove_matched(text, m.start(), m.end())
            delta_map = {
                'seconds': timedelta(seconds=num),
                'minutes': timedelta(minutes=num),
                'hours': timedelta(hours=num),
                'days': timedelta(days=num),
            }
            if unit == 'days':
                return datetime.combine(today + delta_map[unit], dt_time.min), subject
            return now + delta_map[unit], subject

    # ── 2. 标准格式 YYYY-MM-DD HH:MM / YYYY/MM/DD HH:MM / YYYY.MM.DD HH:MM ──
    m = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})\s+(\d{1,2}):(\d{2})', text)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        hour, minute = int(m.group(4)), int(m.group(5))
        subject = _remove_matched(text, m.start(), m.end())
        try:
            return datetime(year, month, day, hour, minute), subject
        except ValueError:
            pass

    # ── 3. 标准格式无时间：YYYY-MM-DD ──
    m = re.search(r'(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})', text)
    if m:
        year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
        time_part = _extract_time(text)
        subject = _remove_matched(text, m.start(), m.end())
        if time_part:
            time_str = f"{time_part.hour}:{time_part.minute:02d}"
            subject = subject.replace(time_str, "").strip()
            subject = re.sub(r'\s+', ' ', subject)
        try:
            if time_part:
                return datetime(year, month, day, time_part.hour, time_part.minute), subject
            return datetime(year, month, day), subject
        except ValueError:
            pass

    # ── 4. 特殊日期词：今天/明天/后天/大后天 ──
    date_words = {
        '今天': today,
        '明天': today + timedelta(days=1),
        '后天': today + timedelta(days=2),
        '大后天': today + timedelta(days=3),
    }
    for word, d in date_words.items():
        if word in text:
            idx = text.index(word)
            after_word = text[idx + len(word):]
            time_part = _extract_time(after_word)
            matched_end = idx + len(word)
            if time_part:
                # 检查时间是否紧跟在日期词后面
                time_str = f"{time_part.hour}:{time_part.minute:02d}"
                pos = after_word.find(time_str)
                if pos >= 0:
                    matched_end = idx + len(word) + pos + len(time_str)
            subject = _remove_matched(text, idx, matched_end)
            if time_part:
                return datetime.combine(d, time_part), subject
            return datetime.combine(d, dt_time.min), subject

    # ── 5. 中文月日：5月5日 / 5月5号 ──
    m = re.search(r'(\d{1,2})月\s*(\d{1,2})[日号]', text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = now.year
        time_part = _extract_time(text)
        subject = _remove_matched(text, m.start(), m.end())
        if time_part:
            time_str = f"{time_part.hour}:{time_part.minute:02d}"
            subject = subject.replace(time_str, "").strip()
            subject = re.sub(r'\s+', ' ', subject)
        try:
            base = datetime(year, month, day)
        except ValueError:
            return None, text
        if time_part:
            target = base.replace(hour=time_part.hour, minute=time_part.minute)
        else:
            target = base
        if target < now:
            target = target.replace(year=year + 1)
        return target, subject

    # ── 6. MM-DD / MM/DD 格式 ──
    m = re.search(r'\b(\d{1,2})[-/](\d{1,2})\b', text)
    if m:
        month, day = int(m.group(1)), int(m.group(2))
        year = now.year
        time_part = _extract_time(text)
        subject = _remove_matched(text, m.start(), m.end())
        if time_part:
            time_str = f"{time_part.hour}:{time_part.minute:02d}"
            subject = subject.replace(time_str, "").strip()
            subject = re.sub(r'\s+', ' ', subject)
        try:
            base = datetime(year, month, day)
        except ValueError:
            return None, text
        if time_part:
            target = base.replace(hour=time_part.hour, minute=time_part.minute)
        else:
            target = base
        if target < now:
            target = target.replace(year=year + 1)
        return target, subject

    # ── 7. 纯时间 HH:MM ──
    time_part = _extract_time(text)
    if time_part:
        time_str = f"{time_part.hour}:{time_part.minute:02d}"
        subject = text.replace(time_str, "").strip()
        subject = re.sub(r'\s+', ' ', subject)
        target = datetime.combine(today, time_part)
        if target < now:
            target += timedelta(days=1)
        return target, subject

    return None, text


def _format_countdown(seconds: float) -> str:
    """格式化为倒计时字符串"""
    if seconds < 60:
        return f"{int(seconds)}秒"
    if seconds < 3600:
        return f"{int(seconds // 60)}分{int(seconds % 60)}秒"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hours}小时{mins}分"


class ReminderHandler(BackgroundTaskHandler):
    """定时提醒助手（支持提醒事项）"""
    name = "reminder"
    priority = 85
    description = "定时提醒（异步任务）"

    def can_handle(self, content: str, msg: dict) -> bool:
        """触发词：r 开头，或包含 remind/提醒"""
        stripped = content.strip().lower()
        if stripped.startswith('r ') or stripped == 'r':
            return True
        if 'remind' in stripped or '提醒' in content:
            return True
        return False

    async def run(self, content: str, msg: dict, **kwargs) -> TaskResult:
        """解析时间和事项，等待到点后发送提醒"""
        target, subject = _parse_reminder(content)
        now = _now()

        if not target:
            return TaskResult.fail(
                "无法解析时间，请使用以下格式之一：\n"
                "• r 30分钟后 吃药\n"
                "• r 明天 14:30 提交报告\n"
                "• r 2026-05-05 14:30 开会\n"
                "• r 14:30 休息"
            )

        if target < now:
            return TaskResult.fail(
                f"目标时间 {target.strftime('%Y-%m-%d %H:%M')} 已经过去啦"
            )

        wait_seconds = (target - now).total_seconds()
        subject_display = f"「{subject}」" if subject else ""

        # 上报初始状态
        self.report_progress(
            f"⏰ {subject_display} 提醒已设置，"
            f"将在 {_format_countdown(wait_seconds)} 后触发"
        )

        # 长等待时分段 sleep，同时上报倒计时
        if wait_seconds > 60:
            check_interval = 10
            elapsed = 0
            while elapsed < wait_seconds:
                remain = wait_seconds - elapsed
                if remain > 60:
                    self.report_progress(
                        f"{subject_display} 还剩 {_format_countdown(remain)}..."
                    )
                    await asyncio.sleep(min(check_interval, remain))
                    elapsed += check_interval
                else:
                    self.report_progress(
                        f"{subject_display} 还剩 {_format_countdown(remain)}，即将触发..."
                    )
                    await asyncio.sleep(min(5, remain))
                    elapsed += 5
        else:
            await asyncio.sleep(wait_seconds)

        self.report_progress(100, f"⏰ {subject_display} 时间到！")
        return TaskResult.success(
            f"⏰ 提醒时间到！{subject_display}\n"
            f"设定时间: {target.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"当前时间: {_now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
