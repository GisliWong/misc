import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, scrolledtext, END
from pathlib import Path
import subprocess, threading, json, struct

MP4_BOX_SIGNS = [b"ftyp", b"moov", b"mdat"]
LOG_LEVELS = ["DEBUG", "INFO", "WARN", "ERROR"]


class BiliMergeModern(ttk.Window):
    def __init__(self):
        super().__init__(title="B站视频合并工具", themename="minty")
        self.geometry("900x700")
        self.minsize(800, 600)

        self.has_ffmpeg = self.check_ffmpeg()
        self.running = False

        main = ttk.Frame(self)
        main.pack(fill=BOTH, expand=True, padx=20, pady=20)

        ttk.Label(
            main, text="B站视频合并工具",
            font=("Segoe UI", 16, "bold"),
            bootstyle="inverse-primary"
        ).pack(pady=10)

        ttk.Label(
            main,
            text="✓ FFmpeg 可用" if self.has_ffmpeg else "⚠ 未检测到 FFmpeg",
            bootstyle="success" if self.has_ffmpeg else "warning"
        ).pack()

        cfg = ttk.LabelFrame(main, text="配置")
        cfg.pack(fill=X, pady=10)

        ttk.Label(cfg, text="视频目录").grid(row=0, column=0, padx=10, pady=6, sticky=W)
        self.video_entry = ttk.Entry(cfg)
        self.video_entry.grid(row=0, column=1, sticky=EW, padx=5)
        ttk.Button(cfg, text="选择", command=self.choose_video_dir).grid(row=0, column=2, padx=5)

        ttk.Label(cfg, text="输出目录").grid(row=1, column=0, padx=10, pady=6, sticky=W)
        self.output_entry = ttk.Entry(cfg)
        self.output_entry.grid(row=1, column=1, sticky=EW, padx=5)
        ttk.Button(cfg, text="选择", command=self.choose_output_dir).grid(row=1, column=2, padx=5)

        cfg.columnconfigure(1, weight=1)

        bar = ttk.Frame(cfg)
        bar.grid(row=2, column=0, columnspan=3, sticky=EW, pady=6)

        self.log_level = ttk.StringVar(value="INFO")
        ttk.OptionMenu(bar, self.log_level, "INFO", *LOG_LEVELS).pack(side=LEFT, padx=5)

        self.progress = ttk.DoubleVar()
        ttk.Progressbar(bar, variable=self.progress).pack(side=LEFT, fill=X, expand=True, padx=10)

        self.start_btn = ttk.Button(bar, text="开始合并", bootstyle="danger", command=self.start_merge)
        self.start_btn.pack(side=RIGHT, padx=5)

        log_frame = ttk.LabelFrame(main, text="日志")
        log_frame.pack(fill=BOTH, expand=True)

        self.log_box = scrolledtext.ScrolledText(
            log_frame, font=("Consolas", 9), wrap="word"
        )
        self.log_box.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.status = ttk.StringVar(value="就绪")
        ttk.Label(main, textvariable=self.status).pack(fill=X)

    # ---------------- 工具函数 ----------------

    def log(self, msg, level="INFO"):
        if LOG_LEVELS.index(level) >= LOG_LEVELS.index(self.log_level.get()):
            self.log_box.insert(END, f"[{level}] {msg}\n")
            self.log_box.see(END)
        self.status.set(msg)

    def log_ffmpeg_bytes(self, data: bytes, tag):
        if not data:
            return
        text = data.decode("utf-8", errors="replace")
        for line in text.splitlines():
            if line.strip():
                self.log(f"{tag} {line}", "DEBUG")

    def choose_video_dir(self):
        p = filedialog.askdirectory()
        if p:
            self.video_entry.delete(0, END)
            self.video_entry.insert(0, p)

    def choose_output_dir(self):
        p = filedialog.askdirectory()
        if p:
            self.output_entry.delete(0, END)
            self.output_entry.insert(0, p)

    def check_ffmpeg(self):
        try:
            subprocess.run(
                ["ffmpeg", "-version"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=2
            )
            return True
        except Exception:
            return False

    # ---------------- 核心逻辑 ----------------

    def remove_m4s_header(self, src: Path, dst: Path):
        data = src.read_bytes()
        for sig in MP4_BOX_SIGNS:
            i = data.find(sig)
            if i != -1:
                dst.write_bytes(data[i - 4:])
                return
        dst.write_bytes(data)

    def detect_stream(self, f: Path):
        try:
            out = subprocess.check_output(
                ["ffprobe", "-v", "error", "-show_entries", "stream=codec_type",
                 "-of", "default=nw=1", str(f)],
                stderr=subprocess.DEVNULL
            )
            if b"video" in out:
                return "video"
            if b"audio" in out:
                return "audio"
        except Exception:
            pass
        return None

    def run_ffmpeg(self, cmd):
        self.log("执行 ffmpeg", "INFO")
        if self.log_level.get() == "DEBUG":
            p = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.log_ffmpeg_bytes(p.stdout, "[FFMPEG-OUT]")
            self.log_ffmpeg_bytes(p.stderr, "[FFMPEG-ERR]")
            if p.returncode != 0:
                raise RuntimeError("ffmpeg 失败")
        else:
            subprocess.run(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=True
            )

    def process_dir(self, d: Path, out_base: Path):
        info_file = d / "videoInfo.json"
        if not info_file.exists():
            self.log("缺少 videoInfo.json", "WARN")
            return

        info = json.loads(info_file.read_text(encoding="utf-8"))
        out_dir = out_base / info.get("groupTitle", "default")
        out_dir.mkdir(parents=True, exist_ok=True)

        video = audio = None
        cover = d / "image.jpg"

        for m4s in d.glob("*.m4s"):
            binf = d / (m4s.stem + ".bin")
            self.remove_m4s_header(m4s, binf)
            t = self.detect_stream(binf)
            if t == "video":
                video = binf
            elif t == "audio":
                audio = binf

        if not video:
            self.log("未找到视频流", "WARN")
            return

        out = out_dir / f"{info.get('title','video')}.mp4"

        cmd = ["ffmpeg", "-y", "-i", str(video)]
        if audio:
            cmd += ["-i", str(audio)]
        if cover.exists():
            cmd += ["-i", str(cover)]

        cmd += ["-map", "0:v:0"]
        if audio:
            cmd += ["-map", "1:a:0"]
        if cover.exists():
            cmd += ["-map", "2:v:0"]

        cmd += ["-c:v", "copy"]
        if audio:
            cmd += ["-c:a", "copy"]
        if cover.exists():
            cmd += ["-disposition:v:1", "attached_pic"]

        cmd.append(str(out))
        self.run_ffmpeg(cmd)
        self.log(f"完成: {out}", "INFO")

    # ---------------- 线程入口 ----------------

    def start_merge(self):
        if self.running:
            return
        v = self.video_entry.get()
        o = self.output_entry.get()
        if not v or not o:
            self.log("路径未设置", "ERROR")
            return

        self.running = True
        self.start_btn.config(state="disabled")
        threading.Thread(
            target=self.worker,
            args=(Path(v), Path(o)),
            daemon=True
        ).start()

    def worker(self, vdir: Path, odir: Path):
        subs = [x for x in vdir.iterdir() if x.is_dir()]
        total = len(subs)
        for i, d in enumerate(subs):
            self.progress.set(i / total * 100)
            self.process_dir(d, odir)
        self.progress.set(100)
        self.running = False
        self.start_btn.config(state="normal")
        self.log("全部完成", "INFO")


if __name__ == "__main__":
    BiliMergeModern().mainloop()
