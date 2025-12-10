# client_gui.py
import socket
import threading
import queue
import tkinter as tk
from tkinter import scrolledtext, messagebox

SERVER_HOST = "127.0.0.1"   # Đổi nếu server chạy máy khác
SERVER_PORT = 5000


class GuessClientGUI:
    def __init__(self, master):
        self.master = master
        self.master.title("Game Đoán Số Nhiều Người Chơi 🎲")

        # Hàng trên: username + nút kết nối
        top_frame = tk.Frame(master)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(top_frame, text="Tên:").pack(side=tk.LEFT)
        self.username_var = tk.StringVar()
        self.username_entry = tk.Entry(top_frame, textvariable=self.username_var, width=15)
        self.username_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="IP:").pack(side=tk.LEFT)
        self.host_var = tk.StringVar(value=SERVER_HOST)
        self.host_entry = tk.Entry(top_frame, textvariable=self.host_var, width=12)
        self.host_entry.pack(side=tk.LEFT, padx=5)

        tk.Label(top_frame, text="Port:").pack(side=tk.LEFT)
        self.port_var = tk.StringVar(value=str(SERVER_PORT))
        self.port_entry = tk.Entry(top_frame, textvariable=self.port_var, width=6)
        self.port_entry.pack(side=tk.LEFT, padx=5)

        self.connect_button = tk.Button(top_frame, text="Kết nối", command=self.connect_to_server)
        self.connect_button.pack(side=tk.LEFT, padx=5)

        # Khung hiển thị log
        self.text_area = scrolledtext.ScrolledText(master, height=20, state=tk.DISABLED)
        self.text_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Khung nhập số đoán
        bottom_frame = tk.Frame(master)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)

        tk.Label(bottom_frame, text="Số đoán:").pack(side=tk.LEFT)
        self.guess_var = tk.StringVar()
        self.guess_entry = tk.Entry(bottom_frame, textvariable=self.guess_var)
        self.guess_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        self.guess_entry.bind("<Return>", self.send_guess_event)

        self.send_button = tk.Button(bottom_frame, text="Gửi", command=self.send_guess)
        self.send_button.pack(side=tk.LEFT, padx=5)

        # Trạng thái mạng
        self.sock = None
        self.listener_thread = None
        self.running = False
        self.recv_queue = queue.Queue()

        # Ban đầu chưa cho đoán
        self.set_input_enabled(False)

        # Poll queue để cập nhật GUI từ thread khác
        self.master.after(100, self.process_messages)

    # ================== HÀM HỖ TRỢ GUI ==================

    def log(self, message: str):
        """In một dòng vào khung text."""
        self.text_area.config(state=tk.NORMAL)
        self.text_area.insert(tk.END, message + "\n")
        self.text_area.see(tk.END)
        self.text_area.config(state=tk.DISABLED)

    def set_input_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        self.guess_entry.config(state=state)
        self.send_button.config(state=state)

    # ================== KẾT NỐI SERVER ==================

    def connect_to_server(self):
        if self.sock is not None:
            messagebox.showinfo("Thông báo", "Đã kết nối rồi.")
            return

        username = self.username_var.get().strip()
        if not username:
            messagebox.showwarning("Lỗi", "Vui lòng nhập tên.")
            return

        host = self.host_var.get().strip() or SERVER_HOST
        port_str = self.port_var.get().strip() or str(SERVER_PORT)

        try:
            port = int(port_str)
        except ValueError:
            messagebox.showerror("Lỗi", "Port không hợp lệ.")
            return

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((host, port))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không kết nối được tới server:\n{e}")
            return

        self.sock = s
        self.running = True
        self.log(f"Kết nối tới {host}:{port}")
        self.connect_button.config(state=tk.DISABLED)

        # Gửi username
        try:
            self.sock.sendall((username + "\n").encode("utf-8"))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Gửi username thất bại:\n{e}")
            self.close_connection()
            return

        # Bắt đầu thread nhận dữ liệu
        self.listener_thread = threading.Thread(target=self.listen_server, daemon=True)
        self.listener_thread.start()

        # Cho phép nhập số đoán
        self.set_input_enabled(True)
        self.guess_entry.focus_set()

    # ================== NHẬN DỮ LIỆU TỪ SERVER ==================

    def listen_server(self):
        try:
            with self.sock.makefile("r", encoding="utf-8") as f:
                for line in f:
                    if not line:
                        break
                    text = line.rstrip("\n")
                    self.recv_queue.put(text)
        except Exception as e:
            self.recv_queue.put(f"[LỖI] Mất kết nối server: {e}")
        finally:
            self.recv_queue.put("[SYSTEM] Kết nối server đã đóng.")
            self.running = False

    def process_messages(self):
        """Lấy message từ queue và in ra GUI. Hàm này chạy định kỳ bằng after()."""
        while not self.recv_queue.empty():
            msg = self.recv_queue.get()
            # Xử lý một vài thông điệp hệ thống
            if msg.startswith("[SYSTEM]"):
                self.log(msg)
                self.set_input_enabled(False)
                self.connect_button.config(state=tk.NORMAL)
                self.sock = None
            else:
                self.log(msg)
        # Lặp lại
        self.master.after(100, self.process_messages)

    # ================== GỬI DỮ LIỆU LÊN SERVER ==================

    def send_guess_event(self, event):
        self.send_guess()

    def send_guess(self):
        if self.sock is None:
            messagebox.showwarning("Chưa kết nối", "Hãy kết nối server trước.")
            return

        guess = self.guess_var.get().strip()
        if not guess:
            return

        try:
            self.sock.sendall((guess + "\n").encode("utf-8"))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không gửi được dữ liệu:\n{e}")
            self.close_connection()
            return

        # Nếu người chơi gõ quit thì tự đóng
        if guess.lower() in ("quit", "exit"):
            self.set_input_enabled(False)

        self.guess_var.set("")

    # ================== ĐÓNG KẾT NỐI ==================

    def close_connection(self):
        self.running = False
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None
        self.set_input_enabled(False)
        self.connect_button.config(state=tk.NORMAL)


def main():
    root = tk.Tk()
    app = GuessClientGUI(root)

    def on_close():
        if messagebox.askokcancel("Thoát", "Thoát chương trình?"):
            app.close_connection()
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()


if __name__ == "__main__":
    main()
