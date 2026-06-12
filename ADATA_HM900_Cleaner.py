import cv2, os, itertools, subprocess, time, json
import numpy as np
from PIL import Image
import imagehash

# 讓底層的 OpenCV 與 FFmpeg 徹底閉嘴
os.environ["OPENCV_LOG_LEVEL"] = "OFF"
CACHE_FILE = "database_cache_F.json"

def load_cache():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: return {}
    return {}

def save_cache(db):
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f: json.dump(db, f, ensure_ascii=False, indent=4)
    except: pass

def get_sz(p):
    try:
        b = os.path.getsize(p)
        return f"{b/(1024*1024):.2f} MB" if b >= 1048576 else f"{b/1024:.2f} KB"
    except: return "未知"

def get_img_hash(p):
    try:
        img = Image.open(p); img.verify()
        pil_img = Image.open(p); pil_img.load()
        bgr = cv2.cvtColor(np.array(pil_img.convert('RGB')), cv2.COLOR_RGB2BGR)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        lab = cv2.cvtColor(bgr, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        nl = cv2.merge((clahe.apply(l), a, b))
        rgb = cv2.cvtColor(cv2.cvtColor(nl, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2RGB)
        return str(imagehash.phash(Image.fromarray(rgb)))
    except: return None

def get_vid_hashes(p):
    h = []
    try:
        cap = cv2.VideoCapture(p)
        tot = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        if tot > 10:
            for pt in [int(tot*0.25), int(tot*0.5), int(tot*0.75)]:
                cap.set(cv2.CAP_PROP_POS_FRAMES, pt)
                success, frame = cap.read()
                if success:
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
                    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    nl = cv2.merge((clahe.apply(l), a, b))
                    rgb = cv2.cvtColor(cv2.cvtColor(nl, cv2.COLOR_LAB2BGR), cv2.COLOR_BGR2RGB)
                    vh = imagehash.phash(Image.fromarray(rgb))
                    if str(vh) != "0000000000000000": h.append(str(vh))
        cap.release()
    except: pass
    return h

def ask_del(p1, p2, is_arc=False):
    n1, n2, s1, s2 = os.path.basename(p1), os.path.basename(p2), get_sz(p1), get_sz(p2)
    print(f"\n🎯 發現相似項目！\nA: {p1} ({s1})\nB: {p2} ({s2})")
    if not is_arc:
        try: os.startfile(p1); time.sleep(0.3); os.startfile(p2)
        except: pass
    print(f"[1] 刪 A: {n1}\n[2] 刪 B: {n2}\n[3] 刪全部\n[4] 開資料夾\n[0] 保留並跳過")
    c = input("👉 請輸入 (1/2/3/4/0): ").strip()
    if c == '1':
        try: os.remove(p1); print("🗑️ 已刪除 A"); return 1
        except Exception as e: print(f"失敗: {e}")
    elif c == '2':
        try: os.remove(p2); print("🗑️ 已刪除 B"); return 2
        except Exception as e: print(f"失敗: {e}")
    elif c == '3':
        try:
            if os.path.exists(p1): os.remove(p1)
            if os.path.exists(p2): os.remove(p2)
            print("💥 通通刪除"); return 3
        except Exception as e: print(f"失敗: {e}")
    elif c == '4':
        try:
            subprocess.Popen(f'explorer /select,"{p1}"')
            time.sleep(0.3)
            subprocess.Popen(f'explorer /select,"{p2}"')
        except: pass
        return ask_del(p1, p2, is_arc)
    return 0

def main():
    root = "F:\\"
    print("==============================================")
    print(" 🧠 【ADATA HM900 分流比對智慧優化版】啟動！")
    print("==============================================")
    print(" [ 1 ] 📷 只掃描並比對【圖片】 (PNG, JPG, JPEG)")
    print(" [ 2 ] 🎬 只掃描並比對【影片】 (MP4, AVI, MOV, MKV)")
    print(" [ 3 ] 📦 只掃描並比對【壓縮檔】(RAR, ZIP, 7Z)")
    print(" [ 4 ] 🔥 三雄聯手【全面分析】 (同時搜圖片+影片+壓縮檔)")
    print("==============================================")
    
    mode = input("👉 請選擇比對模式數字 (1/2/3/4): ").strip()
    
    if mode == '1':
        target_exts = ('.png', '.jpg', '.jpeg')
        print("\n🚀 已開啟【純圖片高速比對模式】")
    elif mode == '2':
        target_exts = ('.mp4', '.avi', '.mov', '.mkv')
        print("\n🚀 已開啟【純影片精準比對模式】")
    elif mode == '3':
        target_exts = ('.rar', '.zip', '.7z')
        print("\n🚀 已開啟【純壓縮檔光速比對模式】")
    elif mode == '4':
        target_exts = ('.png', '.jpg', '.jpeg', '.mp4', '.avi', '.mov', '.mkv', '.rar', '.zip', '.7z')
        print("\n🚀 已開啟【三位一體全面比對模式】")
    else:
        print("❌ 輸入錯誤，程式結束。")
        return

    db = load_cache()
    print("🔍 正在硬碟中撈取符合條件的檔案...")
    
    files = []
    for r, dirs, fls in os.walk(root):
        if any(x in r.lower() for x in ['$recycle.bin', 'system volume information', '.git', 'windows']): continue
        for f in fls:
            if f.lower().endswith(target_exts): files.append(os.path.join(r, f))
            
    print(f"📂 撈取完畢！找到 {len(files)} 個目標檔案。開始深入分析...")
    if len(files) < 2: 
        print("ℹ️ 符合格式的檔案數量少於 2 個，無法比對。")
        return
    
    img_db, vid_db, arc_db = {}, {}, {}
    for p in files:
        if not os.path.exists(p): continue
        ext = os.path.splitext(p)[1].lower()
        
        if ext in ('.rar', '.zip', '.7z'):
            try: arc_db[p] = (os.path.basename(p).lower(), os.path.getsize(p))
            except: pass
            continue
            
        mt = os.path.getmtime(p)
        if ext in ['.mp4', '.avi', '.mov', '.mkv']:
            if p in db and db[p].get("mtime") == mt and isinstance(db[p].get("hashes"), list): vh = db[p]["hashes"]
            else:
                vh = get_vid_hashes(p)
                if not vh: continue
                db[p] = {"hashes": vh, "mtime": mt, "ignored": db.get(p, {}).get("ignored", [])}
            vid_db[p] = vh
        elif ext in ['.png', '.jpg', '.jpeg']:
            if p in db and db[p].get("mtime") == mt and isinstance(db[p].get("hash"), str): ih = db[p]["hash"]
            else:
                ih = get_img_hash(p)
                if not ih: continue
                db[p] = {"hash": ih, "mtime": mt, "ignored": db.get(p, {}).get("ignored", [])}
            img_db[p] = imagehash.hex_to_hash(ih)

    del_fls = set()
    
    # 1. 比對壓縮檔
    if arc_db:
        print("🤖 正在執行壓縮檔指紋撞擊...")
        for p1, p2 in itertools.combinations(list(arc_db.keys()), 2):
            if p1 in del_fls or p2 in del_fls: continue
            if p2 in db.get(p1, {}).get("ignored", []) or p1 in db.get(p2, {}).get("ignored", []): continue
            if arc_db[p1][0] == arc_db[p2][0] and arc_db[p1][1] == arc_db[p2][1]:
                res = ask_del(p1, p2, is_arc=True)
                if res in [1, 3]: del_fls.add(p1)
                if res in [2, 3]: del_fls.add(p2)
                if res == 0:
                    db.setdefault(p1, {"ignored": []})["ignored"].append(p2)
                    db.setdefault(p2, {"ignored": []})["ignored"].append(p1)
                    save_cache(db)

    # 2. 比對影片
    if vid_db:
        print("🤖 正在執行影片三點聯防大數據交叉分析...")
        for p1, p2 in itertools.combinations(list(vid_db.keys()), 2):
            if p1 in del_fls or p2 in del_fls: continue
            if p2 in db.get(p1, {}).get("ignored", []) or p1 in db.get(p2, {}).get("ignored", []): continue
            l1, l2 = vid_db[p1], vid_db[p2]
            if len(l1) != len(l2) or len(l1) == 0: continue
            match = True
            for h1s, h2s in zip(l1, l2):
                if ((1 - ((imagehash.hex_to_hash(h1s) - imagehash.hex_to_hash(h2s)) / 64.0)) * 100) < 95.0:
                    match = False; break
            if match:
                res = ask_del(p1, p2, is_arc=False)
                if res == 1:
                    del_fls.add(p1)
                    if p1 in db: del db[p1]
                elif res == 2:
                    del_fls.add(p2)
                    if p2 in db: del db[p2]
                elif res == 3:
                    del_fls.add(p1); del_fls.add(p2)
                    if p1 in db: del db[p1]
                    if p2 in db: del db[p2]
                elif res == 0:
                    db.setdefault(p1, {"ignored": []})["ignored"].append(p2)
                    db.setdefault(p2, {"ignored": []})["ignored"].append(p1)
                save_cache(db)

    # 3. 比對照片
    if img_db:
        print("🤖 正在執行相片指紋高精準交叉分析...")
        for p1, p2 in itertools.combinations(list(img_db.keys()), 2):
            if p1 in del_fls or p2 in del_fls: continue
            if p2 in db.get(p1, {}).get("ignored", []) or p1 in db.get(p2, {}).get("ignored", []): continue
            if ((1 - ((img_db[p1] - img_db[p2]) / 64.0)) * 100) >= 95.0:
                res = ask_del(p1, p2, is_arc=False)
                if res == 1:
                    del_fls.add(p1)
                    if p1 in db: del db[p1]
                elif res == 2:
                    del_fls.add(p2)
                    if p2 in db: del db[p2]
                elif res == 3:
                    del_fls.add(p1); del_fls.add(p2)
                    if p1 in db: del db[p1]
                    if p2 in db: del db[p2]
                elif res == 0:
                    db.setdefault(p1, {"ignored": []})["ignored"].append(p2)
                    db.setdefault(p2, {"ignored": []})["ignored"].append(p1)
                save_cache(db)

    for k in list(db.keys()):
        if not os.path.exists(k):
            if k in db: del db[k]
    save_cache(db)
    print("\n🎉 所選模式之比對與清理任務圓滿完成！")

if __name__ == "__main__":
    main()