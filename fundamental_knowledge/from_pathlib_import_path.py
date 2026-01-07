from pathlib import Path

print("===== 1. KHỞI TẠO PATH =====")
BASE_DIR = Path.cwd()          # thư mục hiện tại
print("BASE_DIR:", BASE_DIR)

PROJECT_DIR = BASE_DIR / "my_project"
DATA_DIR = PROJECT_DIR / "data"
MODEL_DIR = PROJECT_DIR / "models"

print("\n===== 2. TẠO THƯ MỤC (AN TOÀN) =====")
DATA_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print("Folders created")

print("\n===== 3. KIỂM TRA PATH =====")
print("DATA exists:", DATA_DIR.exists())
print("Is dir:", DATA_DIR.is_dir())
print("Is file:", DATA_DIR.is_file())

print("\n===== 4. LÀM VIỆC VỚI FILE =====")
file_path = DATA_DIR / "sample.txt"

file_path.write_text("Hello pathlib", encoding="utf-8")
print("File written")

content = file_path.read_text(encoding="utf-8")
print("File content:", content)

print("\n===== 5. TÁCH THÔNG TIN FILE =====")
print("Name:", file_path.name)
print("Stem:", file_path.stem)
print("Suffix:", file_path.suffix)
print("Parent:", file_path.parent)

print("\n===== 6. LIỆT KÊ FILE =====")
for p in DATA_DIR.iterdir():
    print(p, "| is file:", p.is_file())

print("\n===== 7. DUYỆT ĐỆ QUY (RẤT HAY DÙNG) =====")
for p in PROJECT_DIR.rglob("*.txt"):
    print("Found:", p)

print("\n===== 8. ĐỔI TÊN / DI CHUYỂN =====")
new_path = DATA_DIR / "renamed.txt"
file_path.rename(new_path)
print("File renamed")

print("\n===== 9. METADATA FILE =====")
stat = new_path.stat()
print("Size:", stat.st_size)
print("Modified:", stat.st_mtime)

print("\n===== 10. XÓA FILE =====")
new_path.unlink()
print("File deleted")

print("\n===== HOÀN THÀNH DEMO PATHLIB =====")
