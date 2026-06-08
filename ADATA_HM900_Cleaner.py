import cv2
import os
import itertools
import subprocess
import time
import json
from glob import glob
from PIL import Image
import imagehash

CACHE_FILE = "database_cache_F.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_cache(cache_data):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=4)
    except:
        pass

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

def show_and_ask_delete(p1, p2, score, is_archive=False):
    name1, name2 = os.path.basename(p1), os.path.basename(p2)
    size1 = get_file_size_string(p1)
    size2 = get_file_size_string(p2)
    
    if is_archive:
        print(f"\n📦 偵測到重複的壓縮檔案！")
        print(f"位置A: {p1} ({size1})")
        print(f"位置B: {p2} ({size2})")
    else:
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

    print(f"\n⚠️ 發現高度相似檔案！(判定依據: {'檔名與大小相同' if is_archive else f'影像相似度 {score:.2f}%'})")
    print(f"[ 1 ] 刪除檔案 A: {name1} 🔴 大小: {size1}")
    print(f"[ 2 ] 刪除檔案 B: {name2} 🔴 大小: {size2}")
    print(f"[ 3 ] 🔥 通通刪除 (A 和 B 都不留)")
    print(f"[ 4 ] 📂 打開這兩個檔案在電腦裡的位置")
    print(f"[ 0 ] 🆗 暫不處理 (保留兩者且「永遠記住此選擇」)")
    
    choice = input("👉 請輸入數字選擇操作 (1/2/3/4/0): ").strip()
    
    if os.name == 'nt' and not is_archive:
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
        return show_and_ask_delete(p1, p2, score, is_archive)
    else:
        print("🆗 選擇暫不處理，已保留兩個檔案。")
        return 0
    return 0

def main():
    root_dir = "F:\\" 

    print(f"🧠 【ADATA HM900 外接硬碟智慧版】已成功啟動！")
    print(f"載入 F 槽歷史快取記憶中...")
    db_cache = load_cache()

    print(f"🔍 開始全面掃描 F 槽的所有媒體與壓縮檔案...")

    media_extensions = ('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.mkv')
    archive_extensions = ('.rar', '.zip', '.7z')
    all_extensions = media_extensions + archive_extensions

    all_files = []
    
    for root, dirs, files in os.walk(root_dir):
        if any(x in root.lower() for x in ['$recycle.bin', 'system volume information', '.git', 'windows']):
            continue
        
        for file in files:
            if file.lower().endswith(all_extensions):
                all_files.append(os.path.join(root, file))

    print(f"📂 掃描完畢！在 F 槽總共找到了 {len(all_files)} 個符合格式的媒體與壓縮檔案。")
    
    if len(all_files) < 2:
        print(f"ℹ️ 目前 F 槽找到的有效檔案數為 {len(all_files)} 個。")
        print("由於檔案數量少於 2 個，無法進行兩兩重複比對，程式圓滿結束。")
        return

    print("🤖 開始進行大數據高速雙軌記憶比對...\n" + "="*50)

    hash_dict = {}
    archive_dict = {}

    for file_path in all_files:
        if not os.path.exists(file_path):
            continue
            
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in archive_extensions:
            try:
                archive_dict[file_path] = (os.path.basename(file_path).lower(), os.path.getsize(file_path))
            except:
                pass
            continue
            
        mtime = os.path.getmtime(file_path)
        if file_path in db_cache and db_cache[file_path].get("mtime") == mtime:
            file_hash = imagehash.hex_to_hash(db_cache[file_path]["hash"])
        else:
            pil_img = get_image_for_hash(file_path)
            if pil_img is None:
                continue
            try:
                file_hash = imagehash.phash(pil_img)
                db_cache[file_path] = {
                    "hash": str(file_hash),
                    "mtime": mtime,
                    "ignored_with": db_cache.get(file_path, {}).get("ignored_with", [])
                }
            except:
                continue
                
        hash_dict[file_path] = file_hash

    deleted_files = set()

    # 1. 執行壓縮檔（rar/zip）的比對
    for p1, p2 in itertools.combinations(list(archive_dict.keys()), 2):
        if p1 in deleted_files or p2 in deleted_files:
            continue
        if p2 in db_cache.get(p1, {}).get("ignored_with", []) or p1 in db_cache.get(p2, {}).get("ignored_with", []):
            continue
            
        if archive_dict[p1][0] == archive_dict[p2][0] and archive_dict[p1][1] == archive_dict[p2][1]:
            result = show_and_ask_delete(p1, p2, score=100.0, is_archive=True)
            if result in [1, 2, 3]:
                if result in [1, 3]: deleted_files.add(p1)
                if result in [2, 3]: deleted_files.add(p2)
            elif result == 0:
                db_cache.setdefault(p1, {"ignored_with": []})
                db_cache.setdefault(p2, {"ignored_with": []})
                db_cache[p1]["ignored_with"].append(p2)
                db_cache[p2]["ignored_with"].append(p1)
                save_cache(db_cache)

    # 2. 執行影像檔的比對
    for p1, p2 in itertools.combinations(list(hash_dict.keys()), 2):
        if p1 in deleted_files or p2 in deleted_files:
            continue
        if p2 in db_cache.get(p1, {}).get("ignored_with", []) or p1 in db_cache.get(p2, {}).get("ignored_with", []):
            continue
        
        distance = hash_dict[p1] - hash_dict[p2]
        score = (1 - (distance / 64.0)) * 100
        
        if score >= 90.0:
            print(f"\n🎯 匹配成功！偵測到未處理過的高相似媒體檔案。")
            result = show_and_ask_delete(p1, p2, score, is_archive=False)
            
            if result == 1:
                deleted_files.add(p1)
                if p1 in db_cache: del db_cache[p1]
            elif result == 2:
                deleted_files.add(p2)
                if p2 in db_cache: del db_cache[p2]
            elif result == 3:
                deleted_files.add(p1); deleted_files.add(p2)
                if p1 in db_cache: del db_cache[p1]
                if p2 in db_cache: del db_cache[p2]
            elif result == 0:
                db_cache.setdefault(p1, {"ignored_with": []})
                db_cache.setdefault(p2, {"ignored_with": []})
                db_cache[p1]["ignored_with"].append(p2)
                db_cache[p2]["ignored_with"].append(p1)
            save_cache(db_cache)
            print("="*50)

    for cached_path in list(db_cache.keys()):
        if not os.path.exists(cached_path):
            del db_cache[cached_path]
    save_cache(db_cache)

    print("\n🎉 ADATA HM900 全盤媒體與壓縮檔智慧檢查完成！")

if __name__ == "__main__":
    main()