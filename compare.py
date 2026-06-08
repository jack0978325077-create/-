import cv2
import os
import itertools
import subprocess
from glob import glob

def get_image_data(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.mp4', '.avi', '.mov', '.mkv']:
        cap = cv2.VideoCapture(file_path)
        success, frame = cap.read()
        cap.release()
        if success:
            return frame, cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    else:
        img = cv2.imread(file_path)
        if img is not None:
            return img, cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return None, None

def calculate_similarity(path1, path2):
    color1, gray1 = get_image_data(path1)
    color2, gray2 = get_image_data(path2)
    
    if gray1 is None or gray2 is None:
        return 0, None, None
        
    h, w = gray1.shape
    gray2_resized = cv2.resize(gray2, (w, h))
    color2_resized = cv2.resize(color2, (w, h))
    
    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([gray2_resized], [0], None, [256], [0, 256])
    cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
    cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)
    
    similarity = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return max(0, similarity) * 100, color1, color2_resized

def show_and_ask_delete(p1, p2, img1, img2):
    name1 = os.path.basename(p1)
    name2 = os.path.basename(p2)
    
    ext1 = os.path.splitext(p1)[1].lower()
    ext2 = os.path.splitext(p2)[1].lower()
    
    print(f"\n💡 正在為您打開檔案進行人工確認...")
    
    # 如果其中一個是影片，用系統預設播放器打開它們
    if ext1 in ['.mp4', '.avi', '.mov', '.mkv'] or ext2 in ['.mp4', '.avi', '.mov', '.mkv']:
        print(f"🎬 偵測到影片，正在啟動電腦播放器打開這兩個檔案...")
        if os.name == 'nt': # Windows
            os.startfile(p1)
            os.startfile(p2)
        else: # Mac / Linux
            subprocess.call(['open', p1])
            subprocess.call(['open', p2])
    else:
        # 如果兩個都是照片，左右拼接顯示在同一個視窗
        import numpy as np
        h1, w1, _ = img1.shape
        img2_scaled = cv2.resize(img2, (w1, h1))
        combined = np.hstack((img1, img2_scaled))
        
        # 縮放視窗以免圖片太大超出螢幕
        screen_w = 1000
        screen_h = int(h1 * (screen_w / (w1 * 2)))
        combined_resized = cv2.resize(combined, (screen_w, screen_h))
        
        cv2.imshow(f"Left: {name1}  |  Right: {name2}", combined_resized)
        cv2.waitKey(1) # 讓視窗順利渲染出來

    # 在黑視窗詢問使用者
    print(f"\n⚠️ 發現高相似度檔案！")
    print(f"[ 1 ] 刪除檔案 A: {name1}")
    print(f"[ 2 ] 刪除檔案 B: {name2}")
    print(f"[ 0 ] 暫不處理 (保留兩者)")
    
    choice = input("👉 請輸入數字選擇操作 (1/2/0): ").strip()
    
    # 關閉 OpenCV 照片視窗
    cv2.destroyAllWindows()
    
    if choice == '1':
        try:
            os.remove(p1)
            print(f"🗑️ 已成功刪除: {name1}")
            return True # 代表 p1 被刪了
        except Exception as e:
            print(f"❌ 刪除失敗: {e}")
    elif choice == '2':
        try:
            os.remove(p2)
            print(f"🗑️ 已成功刪除: {name2}")
            return True # 代表 p2 被刪了
        except Exception as e:
            print(f"❌ 刪除失敗: {e}")
    else:
        print("🆗 已保留兩個檔案。")
        
    return False

# 主程式開始
image_folder = "images"
extensions = ["*.png", "*.jpg", "*.jpeg", "*.mp4", "*.avi", "*.mov"]
file_paths = []

for ext in extensions:
    file_paths.extend(glob(os.path.join(image_folder, ext)))

print(f"📂 自動掃描完成！找到 {len(file_paths)} 個照片或影片檔案。\n")

if len(file_paths) < 2:
    print("❌ 檔案數量不足，無法比對！")
else:
    print("🤖 開始進行智慧交叉比對並清理...\n" + "-"*50)
    
    deleted_files = set()
    
    for p1, p2 in itertools.combinations(file_paths, 2):
        # 如果檔案在前面的關卡已經被刪除了，就跳過
        if p1 in deleted_files or p2 in deleted_files:
            continue
            
        if not os.path.exists(p1) or not os.path.exists(p2):
            continue
            
        name1, name2 = os.path.basename(p1), os.path.basename(p2)
        score, img1, img2 = calculate_similarity(p1, p2)
        
        print(f"🔍 比對中: [{name1}] 🆚 [{name2}] -> 相似度: {score:.2f}%")
        
        # 設定相似度門檻，超過 85% 就跳出提示
        if score > 85:
            is_deleted = show_and_ask_delete(p1, p2, img1, img2)
            if is_deleted:
                if not os.path.exists(p1): deleted_files.add(p1)
                if not os.path.exists(p2): deleted_files.add(p2)
        print("-" * 50)

print("\n🎉 全數比對與清理完成！")