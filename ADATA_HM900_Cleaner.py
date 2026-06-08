import cv2
import os
import itertools
import subprocess
import time
from glob import glob
from PIL import Image
import imagehash

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
    print(f"[ 0 ] 🆗 暫不處理 (保留兩者)")
    
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
root_dir = "F:\\" 

print(f"🔍 【ADATA HM900 啟動】開始全面掃描 F 槽的照片與影片檔案... (這可能需要一點時間)")

extensions = ('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.mkv')
all_files = []

# 設定 F 槽也要精準排除的子路徑
exclude_sub_path = os.path.join("新增資料夾", "images").lower()

for root, dirs, files in os.walk(root_dir):
    if any(x in root.lower() for x in ['$recycle.bin', 'system volume information', '.git', 'windows']):
        continue
    
    # 🔥 排除 F 槽底下的「新增資料夾\images」
    if exclude_sub_path in root.lower():
        continue
        
    for file in files:
        if file.lower().endswith(extensions):
            all_files.append(os.path.join(root, file))

print(f"📂 掃描完畢！共找到 {len(all_files)} 個媒體檔案。")

if len(all_files) < 2:
    print("ℹ️ 找不到足夠的檔案進行比對，或檔案都在排除名單內。")
else:
    print("🤖 開始進行大數據高速指紋比對...\n" + "="*50)

    hash_dict = {}

    for file_path in all_files:
        if not os.path.exists(file_path):
            continue
            
        pil_img = get_image_for_hash(file_path)
        if pil_img is None:
            continue
            
        try:
            current_hash = imagehash.phash(pil_img)
        except:
            continue

        is_duplicate = False
        for saved_hash, saved_path in list(hash_dict.items()):
            if not os.path.exists(saved_path):
                del hash_dict[saved_hash]
                continue
                
            distance = current_hash - saved_hash
            score = (1 - (distance / 64.0)) * 100
            
            if score >= 90.0:
                print(f"\n🎯 匹配成功！")
                result = show_and_ask_delete(saved_path, file_path, score)
                
                if result == 1:
                    del hash_dict[saved_hash]
                    hash_dict[current_hash] = file_path
                    is_duplicate = True
                    break
                elif result == 2:
                    is_duplicate = True
                    break
                elif result == 3:
                    del hash_dict[saved_hash]
                    is_duplicate = True
                    break
                print("="*50)

        if not is_duplicate:
            hash_dict[current_hash] = file_path

print("\n🎉 ADATA HM900 檔案檢查完畢！")