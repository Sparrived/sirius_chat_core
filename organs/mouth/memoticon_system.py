import hashlib
from io import BytesIO
from pathlib import Path
import random
import sqlite3
import os
import base64
from typing import Optional
from PIL import Image
from ncatbot.utils import get_log
from ncatbot.plugin_system import EventBus
import asyncio

from ..base_system import BaseSystem, SystemConfig
from ...models.memoticon_model import MemoticonModel
from ...message import MessageSender

class MemoticonConfig(SystemConfig):
    send_prob: float = 0.5  # 发送表情包的概率
    max_image_edge: int = 128  # 表情包图片保存的最大边长，超过则缩放
    

class MemoticonSystem(BaseSystem[MemoticonConfig]):
    """表情包管理系统, 包括表情包判别、存储、查询等功能，使用SQLite存储表情包信息"""
    log = get_log("SiriusChatCore-MemoticonSystem")

    def __init__(self,event_bus: EventBus, work_path: Path, model: MemoticonModel) :
        super().__init__(event_bus, work_path, MemoticonConfig(work_path))
        self._db_path = self._work_path / "memoticons.db"
        self._img_dir = self._work_path / "memoticon_images"
        self._model = model
        os.makedirs(self._img_dir, exist_ok=True)
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS memoticon (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                hash TEXT UNIQUE,
                tags TEXT,
                description TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def judge_meme(self, img_base64: str) -> Optional[str]:
        """判断图片是否为表情包"""
        img_base64 = self.resize_image(img_base64)
        img_hash = hashlib.sha256(img_base64.encode()).hexdigest()
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute('SELECT hash FROM memoticon WHERE hash=?', (img_hash,))
        if c.fetchone():
            conn.close()
            return None
        result = self._model.judge_meme(img_base64)
        if result["is_meme"]:
            if result["meme_type"]:
                return self.save_image(img_base64, tags=",".join(result["meme_type"]), description=result["desp"])
        return None
    
    def send_meme(self, source, emotion: str = "平静"):
        """发送表情包"""
        img_path = self.get_image(emotion)
        if not img_path:
            return
        if random.random() <= self.config.send_prob:
            self.log.info(f"发送表情包到 {source}: {img_path}")
            asyncio.run(MessageSender.send_message_to_source(source, image=img_path))

    def resize_image(self, img_base64: str) -> str:
        """缩放图片，确保其在QQ内显示大小合理，返回base64编码。支持 GIF 和 JPG/PNG。"""
        img_bytes = base64.b64decode(img_base64)
        img = Image.open(BytesIO(img_bytes))
        w, h = img.size
        scale = min(self.config.max_image_edge / max(w, h), 1.0)
        new_size = (int(w * scale), int(h * scale))

        buffer = BytesIO()
        # 处理 GIF 动图
        if getattr(img, "is_animated", False):
            frames = []
            n_frames = getattr(img, "n_frames", 1)
            for frame in range(n_frames):
                img.seek(frame)
                frame_img = img.copy().resize(new_size, Image.Resampling.NEAREST)
                frames.append(frame_img)
            frames[0].save(
                buffer,
                format="GIF",
                save_all=True,
                append_images=frames[1:],
                loop=img.info.get("loop", 0),
                duration=img.info.get("duration", 100)
            )
        else:
            img_resized = img.resize(new_size, Image.Resampling.NEAREST)
            img_resized.save(buffer, format=img.format or "JPEG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    
    def calculate_hash(self, base64_str: str):
        return hashlib.sha256(base64_str.encode()).hexdigest()
    
    def has_resized_image(self, base64_str: str) -> bool:
        img_hash = self.calculate_hash(self.resize_image(base64_str))
        return self.has_image(img_hash)

    def has_image(self, img_hash: str) -> bool:
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            c.execute('SELECT hash FROM memoticon WHERE hash=?', (img_hash,))
            if c.fetchone():
                conn.close()
                return True
            conn.close()
            return False

    def save_image(self, base64_str: str, tags: str = "", description: str = "") -> Optional[str]:
        # 预防输出标签输出非预期的词语
        tags = tags.replace("可爱", "喜悦")
        # 计算图片哈希
        img_hash = self.calculate_hash(base64_str)
        img_path = os.path.join(self._img_dir, f"{img_hash}.jpg")
        try:
            if not self.has_image(img_hash):
                return None
            conn = sqlite3.connect(self._db_path)
            c = conn.cursor()
            # 保存图片到本地
            with open(img_path, "wb") as f:
                f.write(base64.b64decode(base64_str))
            # 保存属性到数据库
            c.execute('''
                INSERT OR REPLACE INTO memoticon (hash, tags, description)
                VALUES (?, ?, ?)
            ''', (img_hash, tags, description))
            conn.commit()
            conn.close()
            result_msg = f"保存表情包成功，哈希值: {img_hash}，标签: {tags}，描述: {description}，路径: {img_path}"
            return result_msg
        except Exception as e:
            raise ValueError(f"保存表情包失败: {e}")

    def get_image(self, tag: str) -> Optional[str]:
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute('SELECT hash FROM memoticon WHERE tags LIKE ?', (f"%{tag}%",))
        rows = c.fetchall()
        conn.close()
        if rows:
            img = random.choice(rows)
            img_path = os.path.join(self._img_dir, f"{img[0]}.jpg")
            return img_path
        return None

    def get_info(self, hash: str) -> Optional[dict]:
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute('SELECT hash, tags, description FROM memoticon WHERE hash=?', (hash,))
        row = c.fetchone()
        conn.close()
        if row:
            return {
                "hash": row[0],
                "tags": row[1],
                "description": row[2]
            }
        return None

    def list_memoticons(self) -> list:
        conn = sqlite3.connect(self._db_path)
        c = conn.cursor()
        c.execute('SELECT hash FROM memoticon')
        rows = c.fetchall()
        conn.close()
        return [r[0] for r in rows]