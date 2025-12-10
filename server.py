# server.py
import socket
import threading
import random

HOST = "0.0.0.0"   # Lắng nghe trên mọi địa chỉ
PORT = 5000        # Port server sử dụng

# Trạng thái game
MIN_VALUE = 1
MAX_VALUE = 100
secret_number = None      # Số bí mật hiện tại
round_id = 0              # Số thứ tự ván chơi

# Quản lý client
clients = []              # Danh sách socket client
players = {}              # players[conn] = username

clients_lock = threading.Lock()  # bảo vệ clients + players
game_lock = threading.Lock()     # bảo vệ secret_number + round_id


def send_line(conn: socket.socket, message: str):
    """Gửi một dòng text kèm newline tới 1 client."""
    conn.sendall((message + "\n").encode("utf-8"))


def broadcast(message: str):
    """
    Gửi message tới TẤT CẢ client đang kết nối.
    Nếu client nào lỗi (disconnect), xóa khỏi danh sách.
    """
    dead_clients = []
    with clients_lock:
        for conn in clients:
            try:
                send_line(conn, message)
            except Exception:
                dead_clients.append(conn)

        for conn in dead_clients:
            print("[SERVER] Một client đã ngắt kết nối trong lúc broadcast.")
            clients.remove(conn)
            players.pop(conn, None)
            try:
                conn.close()
            except:
                pass


def new_game():
    """Sinh số bí mật mới và tăng số thứ tự ván chơi."""
    global secret_number, round_id
    with game_lock:
        round_id += 1
        secret_number = random.randint(MIN_VALUE, MAX_VALUE)
        current_round = round_id
        current_secret = secret_number
    print(f"[GAME] Ván mới #{current_round}. Số bí mật (debug): {current_secret}")


def handle_client(conn: socket.socket, addr):
    """Xử lý 1 client trong 1 thread riêng."""
    print(f"[KẾT NỐI] Client mới từ {addr}")
    username = None

    try:
        send_line(conn, "Chào mừng đến Game Đoán Số 🎲")
        send_line(conn, "Nhập tên (username):")

        # Đọc theo từng dòng từ socket
        with conn.makefile("r", encoding="utf-8") as f:
            # Nhập username
            while username is None:
                line = f.readline()
                if not line:
                    raise ConnectionError("Client đóng kết nối trước khi gửi username.")
                name = line.strip()
                if name:
                    username = name
                else:
                    send_line(conn, "Tên không được trống, nhập lại:")

            # Lưu username
            with clients_lock:
                players[conn] = username

            send_line(conn, f"Xin chào {username}! Số bí mật trong [{MIN_VALUE}, {MAX_VALUE}].")
            send_line(conn, "Nhập số đoán (hoặc 'quit' để thoát).")
            broadcast(f"📢 {username} đã tham gia.")

            # Vòng lặp đọc dự đoán
            for line in f:
                guess_str = line.strip()
                if not guess_str:
                    continue

                # Người chơi thoát
                if guess_str.lower() in ("quit", "exit"):
                    send_line(conn, "Tạm biệt! 👋")
                    break

                # Chuyển chuỗi sang số
                try:
                    guess = int(guess_str)
                except ValueError:
                    send_line(conn, "Nhập số nguyên hợp lệ.")
                    continue

                # So sánh với số bí mật
                global secret_number, round_id
                is_win = False
                winning_number = None
                current_round = None
                result_text = ""

                with game_lock:
                    if guess < secret_number:
                        result_text = "LỚN HƠN"
                    elif guess > secret_number:
                        result_text = "NHỎ HƠN"
                    else:
                        # Đoán đúng
                        is_win = True
                        winning_number = secret_number
                        current_round = round_id
                        # Sinh số mới cho ván tiếp theo
                        round_id += 1
                        secret_number = random.randint(MIN_VALUE, MAX_VALUE)
                        new_secret = secret_number

                # Mọi lần đoán đều hiện cho tất cả
                if not is_win:
                    broadcast(f"📣 {username} đoán {guess} → {result_text}")
                else:
                    # Đầu tiên thông báo lượt đoán thắng
                    broadcast(f"📣 {username} đoán {guess} → ĐÚNG ✅")
                    # Sau đó thông báo thắng & ván mới
                    win_msg = f"🎉 {username} đoán đúng {winning_number} (ván #{current_round})!"
                    print("[WIN]", win_msg)
                    broadcast(win_msg)
                    broadcast(f"🔄 Ván #{round_id} bắt đầu. Số trong [{MIN_VALUE},{MAX_VALUE}].")
                    print(f"[GAME] Số bí mật mới (debug): {new_secret}")

    except Exception as e:
        print(f"[LỖI] Client {addr}: {e}")
    finally:
        # Xóa client khỏi danh sách, đóng kết nối
        with clients_lock:
            if conn in clients:
                clients.remove(conn)
            if conn in players:
                left_name = players[conn]
                broadcast(f"📢 {left_name} đã thoát.")
                players.pop(conn, None)

        try:
            conn.close()
        except:
            pass

        print(f"[NGẮT] Client rời khỏi: {addr}")


def main():
    new_game()  # Khởi tạo ván đầu

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((HOST, PORT))
    server_socket.listen()

    print(f"[SERVER] Đang lắng nghe tại {HOST}:{PORT}...")

    try:
        while True:
            conn, addr = server_socket.accept()
            with clients_lock:
                clients.append(conn)

            thread = threading.Thread(target=handle_client, args=(conn, addr), daemon=True)
            thread.start()
    except KeyboardInterrupt:
        print("\n[SERVER] Đang tắt...")
    finally:
        with clients_lock:
            for conn in clients:
                try:
                    conn.close()
                except:
                    pass
            clients.clear()
            players.clear()
        server_socket.close()
        print("[SERVER] Đã tắt.")


if __name__ == "__main__":
    main()
