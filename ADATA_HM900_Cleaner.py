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
# 🔥 關鍵修改 1：將偵測根目錄直接鎖定在你的外接硬碟 F 槽！
root_dir = "F:\\" 

print(f"🔍 【ADATA HM900 啟動】開始全面掃描 F 槽的所有照片與影片檔案...")

extensions = ('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.mkv')
all_files = []

for root, dirs, files in os.walk(root_dir):
    # 基礎系統防護過濾（外接硬碟通常會有 $RECYCLE.BIN，一定要跳過）
    if any(x in root.lower() for x in ['$recycle.bin', 'system volume information', '.git', 'windows']):
        continue
    
    # 🔥 關鍵修改 2：因為這是外接硬碟，我們不需要像 Telegram 那樣限制特定資料夾名稱
    # 程式會直接掃描 F 槽「所有」不是系統檔的資料夾！
    for file in files:
        if file.lower().endswith(extensions):
            all_files.append(os.path.join(root, file))

print(f"📂 掃描完畢！在 ADATA (F:) 硬碟中總共找到 {len(all_files)} 個媒體檔案。")
print("🤖 開始進行大數據高速指紋比對...\n" + "="*50)