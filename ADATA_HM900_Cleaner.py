import cv2
import os
import itertools
import subprocess
import time
import json  # 🔥 引進大腦記憶庫模組
from glob import glob
from PIL import Image
import imagehash

# 記憶資料庫的檔名
CACHE_FILE = "database_cache.json"

def load_cache():
    """從硬碟讀取之前的偵測記憶"""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            print("ℹ️ 記憶檔案損壞，將建立新的記憶庫。")
            return {}
    return {}

def save_cache(cache_data):
    """將目前的偵測記憶寫入硬碟"""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"❌ 記憶寫入硬碟失敗: {e}")

def get_file_size_string(file_path):
    try:
        size_bytes = os.path.getsize(file_path)
        if size_bytes >= 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            return f"{size_bytes / 1024:.2f} KB"
    except:
        return "未知大小"

def get_image_for_hash(file_path):
    try:
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.mp4', '.avi', '.mov', '.mkv']:
            cap = cv2.VideoCapture(file_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            if fps > 0:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps / 2))
            success, frame = cap.read()
            cap.release()
            if success:
                return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        elif ext in ['.png', '.jpg', '.jpeg']:
            img = Image.open(file_path)
            img.verify()
            return Image.open(file_path)
    except:
        return None
    return None

def open_file_folder_and_select(file_path):
    try:
        if os.name == 'nt':
            subprocess.Popen(f'explorer /select,"{file_path}"')
    except Exception as e:
        print(f"❌ 無法開啟資料夾位置: {e}")

def show_and_ask_delete(p1, p2, score):
    name1, name2 = os.path.basename(p1), os.path.basename(p2)
    size1 = get_file_size_string(p1)
    size2 = get_file_size_string(p2)
    
    print(f"\n💡 正在為您喚醒 Windows 相片檢視器...")
    print(f"位置A: {p1} ({size1})")
    print(f"位置B: {p2} ({size2})")
    
    try:
        if os.name == 'nt':
            os.startfile(p1)
            time.sleep(0.2)
            os.startfile(p2)
    except Exception as e:
        print(f"無法自動開啟，請手動確認。錯誤: {e}")

    print(f"\n⚠️ 發現高度相似檔案！(相似度: {score:.2f}%)")
    print(f"[ 1 ] 刪除檔案 A: {name1} 🔴 大小: {size1}")
    print(f"[ 2 ] 刪除檔案 B: {name2} 🔴 大小: {size2}")
    print(f"[ 3 ] 🔥 通通刪除 (A 和 B 都不留)")
    print(f"[ 4 ] 📂 打開這兩個檔案在電腦裡的位置")
    print(f"[ 0 ] 🆗 暫不處理 (保留兩者且「永遠記住此選擇」)")
    
    choice = input("👉 請輸入數字選擇操作 (1/2/3/4/0): ").strip()
    
    if os.name == 'nt':
        photo_apps = ["PhotosApp.exe", "Microsoft.Photos.exe", "Microsoft.PhotosUI.exe", "dllhost.exe", "Video.UI.exe"]
        for app in photo_apps:
            os.system(f"taskkill /f /im {app} >nul 2>&1")
    
    if choice == '1':
        try:
            os.remove(p1)
            print(f"🗑️ 已成功刪除 A 檔")
            return 1
        except Exception as e:
            print(f"❌ 刪除失敗: {e}")
    elif choice == '2':
        try:
            os.remove(p2)
            print(f"🗑️ 已成功刪除 B 檔")
            return 2
        except Exception as e:
            print(f"❌ 刪除失敗: {e}")
    elif choice == '3':
        try:
            if os.path.exists(p1): os.remove(p1)
            if os.path.exists(p2): os.remove(p2)
            print(f"💥 已成功將 A 檔 與 B 檔「通通刪除」！")
            return 3
        except Exception as e:
            print(f"❌ 部分檔案刪除失敗: {e}")
    elif choice == '4':
        print(f"📂 正在為您打開這兩個檔案所在的資料夾位置...")
        open_file_folder_and_select(p1)
        time.sleep(0.3)
        open_file_folder_and_select(p2)
        return show_and_ask_delete(p1, p2, score)
    else:
        print("🆗 選擇暫不處理，已保留兩個檔案。")
        return 0
    return 0

# === 主程式開始 ===
target_folder_name = "telegram"
root_dir = "D:\\" 

print(f"🧠 【智慧大腦版】啟動！正在載入歷史偵測記憶...")
# 載入歷史快取資料庫
# 結構為：{ file_path: { "hash": "xxxx", "mtime": 123456, "checked_pairs": [...] } }
db_cache = load_cache()

print(f"🔍 開始全面掃描 D 槽中包含 '{target_folder_name}' 的照片與影片檔案...")

extensions = ('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.mkv')
all_files = []
exclude_sub_path = os.path.join("新增資料夾", "images").lower()

for root, dirs, files in os.walk(root_dir):
    if any(x in root.lower() for x in ['$recycle.bin', 'system volume information', '.git', 'windows']):
        continue
    if exclude_sub_path in root.lower():
        continue
    if target_folder_name in root.lower():
        for file in files:
            if file.lower().endswith(extensions):
                all_files.append(os.path.join(root, file))

print(f"📂 掃描完畢！共找到 {len(all_files)} 個媒體檔案。")
print("🤖 開始進行大數據高速智慧記憶比對...\n" + "="*50)

# 1. 第一階段：快速更新或計算所有檔案的指紋（如果記憶庫裡有且沒被改過，直接秒跳過不重複計算）
hash_dict = {}
file_count = 0

for file_path in all_files:
    if not os.path.exists(file_path):
        continue
        
    mtime = os.path.getmtime(file_path) # 獲取檔案最後修改時間
    
    # 檢查記憶庫是否有這個檔案，且檔案沒有被修改過
    if file_path in db_cache and db_cache[file_path].get("mtime") == mtime:
        # 直接從記憶大腦讀取舊指紋，不用耗費 CPU 重新開圖計算！
        file_hash = imagehash.hex_to_hash(db_cache[file_path]["hash"])
    else:
        # 記憶庫沒有，或是檔案被動過，才重新計算指紋
        pil_img = get_image_for_hash(file_path)
        if pil_img is None:
            continue
        try:
            file_hash = imagehash.phash(pil_img)
            # 存入記憶大腦
            db_cache[file_path] = {
                "hash": str(file_hash),
                "mtime": mtime,
                "ignored_with": db_cache.get(file_path, {}).get("ignored_with", [])
            }
        except:
            continue
            
    hash_dict[file_path] = file_hash

# 2. 第二階段：兩兩配對比對（加入歷史記憶過濾機制）
deleted_files = set()

# 使用兩兩交叉組合
for p1, p2 in itertools.combinations(list(hash_dict.keys()), 2):
    if p1 in deleted_files or p2 in deleted_files:
        continue
    if not os.path.exists(p1) or not os.path.exists(p2):
        continue
        
    # 🔥 關鍵判斷：檢查使用者以前是不是對這一對檔案選過 [0] 暫不處理
    # 如果以前選過保留，大腦會記得，這次開新視窗就會「直接自動判定通過」！
    if p2 in db_cache.get(p1, {}).get("ignored_with", []) or p1 in db_cache.get(p2, {}).get("ignored_with", []):
        continue
        
    # 計算指紋差異
    distance = hash_dict[p1] - hash_dict[p2]
    score = (1 - (distance / 64.0)) * 100
    
    if score >= 90.0:
        print(f"\n🎯 匹配成功！偵測到未處理過的高相似檔案。")
        result = show_and_ask_delete(p1, p2, score)
        
        if result == 1:
            deleted_files.add(p1)
            if p1 in db_cache: del db_cache[p1]
            save_cache(db_cache) # 立刻存檔記憶
        elif result == 2:
            deleted_files.add(p2)
            if p2 in db_cache: del db_cache[p2]
            save_cache(db_cache) # 立刻存檔記憶
        elif result == 3:
            deleted_files.add(p1)
            deleted_files.add(p2)
            if p1 in db_cache: del db_cache[p1]
            if p2 in db_cache: del db_cache[p2]
            save_cache(db_cache) # 立刻存檔記憶
        elif result == 0:
            # 使用者選擇暫不處理（保留兩者）：將此配對寫入彼此的「放行黑名單」大腦中
            if "ignored_with" not in db_cache[p1]: db_cache[p1]["ignored_with"] = []
            if "ignored_with" not in db_cache[p2]: db_cache[p2]["ignored_with"] = []
            
            db_cache[p1]["ignored_with"].append(p2)
            db_cache[p2]["ignored_with"].append(p1)
            save_cache(db_cache) # 立刻存檔記憶，下次開新視窗自動跳過這一對！
        print("="*50)

# 清理已經在硬碟中被刪除的無效記憶，保持資料庫乾淨
for cached_path in list(db_cache.keys()):
    if not os.path.exists(cached_path):
        del db_cache[cached_path]
save_cache(db_cache)

print("\n🎉 Telegram 智慧大腦大檢查完成！所有進度已安全儲存至硬碟。")