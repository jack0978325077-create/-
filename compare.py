import cv2
import os
import itertools
import subprocess
from glob import glob
from PIL import Image
import imagehash  # 引入超精準特徵指紋工具

def get_image_for_hash(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.mp4', '.avi', '.mov', '.mkv']:
        # 影片：為了提高精確度，改抓第 0.5 秒（通常比第 0 秒的黑畫面更準確）
        cap = cv2.VideoCapture(file_path)
        fps = cap.get(cv2.CAP_PROP_FPS)
        if fps > 0:
            cap.set(cv2.CAP_PROP_POS_FRAMES, int(fps / 2))
        success, frame = cap.read()
        cap.release()
        if success:
            # 轉換成 PIL 格式供 ImageHash 使用
            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    else:
        # 照片：直接讀取並轉成 PIL 格式
        try:
            return Image.open(file_path)
        except:
            return None
    return None

def calculate_p_hash_similarity(path1, path2):
    img1 = get_image_for_hash(path1)
    img2 = get_image_for_hash(path2)
    
    if img1 is None or img2 is None:
        return 0
        
    # 計算兩張圖的「感知雜湊指紋」
    hash1 = imagehash.phash(img1)
    hash2 = imagehash.phash(img2)
    
    # 計算兩個指紋之間的漢明距離 (Hamming Distance)，最大差異是 64 位元
    distance = hash1 - hash2
    
    # 將差異距離換算成「相似度百分比」
    # 距離 0 代表完全一模一樣 (100%)，距離越大越不接近
    similarity = (1 - (distance / 64.0)) * 100
    return similarity

def show_and_ask_delete(p1, p2):
    name1 = os.path.basename(p1)
    name2 = os.path.basename(p2)
    ext1 = os.path.splitext(p1)[1].lower()
    
    print(f"\n💡 正在為您打開檔案進行人工確認...")
    
    if ext1 in ['.mp4', '.avi', '.mov', '.mkv']:
        if os.name == 'nt': # Windows
            os.startfile(p1)
            os.startfile(p2)
        else: # Mac
            subprocess.call(['open', p1])
            subprocess.call(['open', p2])
    else:
        # 照片直接用 OpenCV 讀取並拼接顯示
        img1 = cv2.imread(p1)
        img2 = cv2.imread(p2)
        if img1 is not None and img2 is not None:
            h1, w1, _ = img1.shape
            img2_scaled = cv2.resize(img2, (w1, h1))
            import numpy as np
            combined = np.hstack((img1, img2_scaled))
            screen_w = 1000
            screen_h = int(h1 * (screen_w / (w1 * 2)))
            combined_resized = cv2.resize(combined, (screen_w, screen_h))
            cv2.imshow(f"Left: {name1}  |  Right: {name2}", combined_resized)
            cv2.waitKey(1)

    print(f"\n⚠️ 發現高度相似檔案 (精確度 >= 90%)！")
    print(f"[ 1 ] 刪除檔案 A: {name1}")
    print(f"[ 2 ] 刪除檔案 B: {name2}")
    print(f"[ 0 ] 暫不處理 (保留兩者)")
    
    choice = input("👉 請輸入數字選擇操作 (1/2/0): ").strip()
    cv2.destroyAllWindows()
    
    if choice == '1':
        os.remove(p1)
        print(f"🗑️ 已成功刪除: {name1}")
        return True
    elif choice == '2':
        os.remove(p2)
        print(f"🗑️ 已成功刪除: {name2}")
        return True
    return False

# 主程式
image_folder = "images"
extensions = ["*.png", "*.jpg", "*.jpeg", "*.mp4", "*.avi", "*.mov"]
file_paths = []

for ext in extensions:
    file_paths.extend(glob(os.path.join(image_folder, ext)))

print(f"📂 90%+ 精確度指紋掃描啟動！找到 {len(file_paths)} 個檔案。\n")

if len(file_paths) < 2:
    print("❌ 檔案數量不足，無法比對！")
else:
    deleted_files = set()
    for p1, p2 in itertools.combinations(file_paths, 2):
        if p1 in deleted_files or p2 in deleted_files: continue
        
        name1, name2 = os.path.basename(p1), os.path.basename(p2)
        
        # 使用超準確的 pHash 比對
        score = calculate_p_hash_similarity(p1, p2)
        
        print(f"🔍 結構比對: [{name1}] 🆚 [{name2}] -> 相似度指數: {score:.2f}%")
        
        # 這裡的 90% 門檻是真正的結構相似！
        if score >= 90.0:
            is_deleted = show_and_ask_delete(p1, p2)
            if is_deleted:
                if not os.path.exists(p1): deleted_files.add(p1)
                if not os.path.exists(p2): deleted_files.add(p2)
        print("-" * 50)

print("\n🎉 高精確度比對與清理完畢！")