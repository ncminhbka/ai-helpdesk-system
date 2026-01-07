import os
import time

print("===== 1. THÔNG TIN CƠ BẢN =====")
print("OS name:", os.name)          # nt / posix
print("Current working dir:", os.getcwd())
print("Process ID:", os.getpid())

print("\n===== 2. THƯ MỤC LÀM VIỆC =====")
os.chdir(os.getcwd())
print("After chdir:", os.getcwd())

print("\n===== 3. TẠO / XÓA THƯ MỤC =====")
if not os.path.exists("demo"):
    os.mkdir("demo")

os.makedirs("demo/sub1/sub2", exist_ok=True)
print("Folders created")

print("\n===== 4. LIỆT KÊ FILE & FOLDER =====")
print("Listdir:", os.listdir("demo"))

print("\n===== 5. KIỂM TRA PATH =====")
print("Exists:", os.path.exists("demo"))
print("Is dir:", os.path.isdir("demo"))
print("Is file:", os.path.isfile("demo"))

print("\n===== 6. OS.PATH =====")
path = os.path.join("demo", "sub1", "file.txt")
print("Join path:", path)
print("Basename:", os.path.basename(path))
print("Dirname:", os.path.dirname(path))
print("Splitext:", os.path.splitext(path))
print("Absolute path:", os.path.abspath(path))

print("\n===== 7. LÀM VIỆC VỚI FILE =====")
with open(path, "w", encoding="utf-8") as f:
    f.write("Hello OS module")

print("File created")

print("\n===== 8. ĐỔI TÊN / DI CHUYỂN FILE =====")
new_path = os.path.join("demo", "sub1", "file_renamed.txt")
os.rename(path, new_path)
print("File renamed")

print("\n===== 9. DUYỆT TOÀN BỘ THƯ MỤC (os.walk) =====")
for root, dirs, files in os.walk("demo"):
    print("ROOT:", root)
    print("DIRS:", dirs)
    print("FILES:", files)
    print("------")

print("\n===== 10. BIẾN MÔI TRƯỜNG =====")
os.environ["MY_ENV"] = "hello_world"
print("MY_ENV:", os.environ.get("MY_ENV"))
print("PATH exists:", "PATH" in os.environ)

print("\n===== 11. THỜI GIAN & FILE STATS =====")
stat = os.stat(new_path)
print("Size:", stat.st_size)
print("Last modified:", time.ctime(stat.st_mtime))

print("\n===== 12. QUYỀN FILE (CHỦ YẾU LINUX/MAC) =====")
# os.chmod(new_path, 0o777)

print("\n===== 13. THỰC THI LỆNH HỆ THỐNG =====")
if os.name == "nt":
    os.system("echo Hello from Windows")
else:
    os.system("echo Hello from Unix")

print("\n===== 14. XÓA FILE / THƯ MỤC =====")
os.remove(new_path)
os.removedirs("demo/sub1/sub2")
print("Cleanup done")

print("\n===== HOÀN THÀNH DEMO OS MODULE =====")
