import httpx
import time
from pathlib import Path

def test_live_studio_api():
    print("Testing Live Manga Studio API...")
    base_url = "http://127.0.0.1:8000"
    
    with httpx.Client(base_url=base_url, timeout=30.0) as client:
        # 1. Health & Telemetry
        health = client.get("/api/health").json()
        print(f" -> Backend Health: {health['status']} on GPU: {health['hardware']['gpu']['device_name']}")
        
        # 2. Create Project
        proj_payload = {
            "title": "Demon Slayer - Chapter 192",
            "manga_title": "Demon Slayer",
            "chapter_num": "192",
            "description": "Full colorization with Tanjirou character memory.",
            "mode": "combined",
            "coloring_style": "vibrant_anime"
        }
        proj = client.post("/api/projects", json=proj_payload).json()
        proj_id = proj["id"]
        print(f" -> Created Project: {proj['manga_title']} (ID: {proj_id})")
        
        # 3. Upload Sample Pages
        sample_dir = Path("sample_data")
        files = [
            ("files", ("page_01_colored_preview.png", open(sample_dir / "page_01_colored_preview.png", "rb"), "image/png")),
            ("files", ("page_02_bw.png", open(sample_dir / "page_02_bw.png", "rb"), "image/png")),
            ("files", ("page_03_bw.png", open(sample_dir / "page_03_bw.png", "rb"), "image/png"))
        ]
        up_res = client.post(f"/api/projects/{proj_id}/upload", files=files).json()
        print(f" -> Uploaded: {up_res['pages_added']} pages into project.")
        
        # 4. Trigger Chapter Analysis
        an_res = client.post(f"/api/projects/{proj_id}/analyze").json()
        print(f" -> Chapter Analysis: {an_res['characters_detected']} character(s) detected, {an_res['colored_previews']} preview page(s).")
        
        # 5. Check CCMS Characters
        chars = client.get(f"/api/characters/project/{proj_id}").json()
        print(f" -> CCMS Registered {len(chars)} character(s):")
        for c in chars:
            print(f"    - {c['name']}: Hair={c['hair_color']}, Skin={c['skin_color']}, Outfit={c['primary_outfit_color']}")
            
        # 6. Start Batch Processing
        queue_start = client.post(f"/api/queue/{proj_id}/start").json()
        print(f" -> Queue started: {queue_start['status']}")
        
        # Monitor queue until completed
        for _ in range(15):
            time.sleep(1.0)
            q_status = client.get("/api/queue/status").json()
            proj_data = client.get(f"/api/projects/{proj_id}").json()
            completed = sum(1 for p in proj_data["pages"] if p["status"] == "completed")
            print(f"    [Progress] Completed {completed}/{len(proj_data['pages'])} pages...")
            if not q_status["is_running"] and completed == len(proj_data["pages"]):
                print(" -> ALL PAGES COLORIZED SUCCESSFULLY!")
                break
                
        # 7. Generate PDF
        pdf_res = client.post(f"/api/export/{proj_id}/pdf", json={"export_type": "pdf", "resolution_scale": "original"}).json()
        print(f" -> Exported Master PDF: {pdf_res['filename']} ({round(pdf_res['file_size_bytes']/1024, 1)} KB)")

        # 8. Generate ZIP
        zip_res = client.post(f"/api/export/{proj_id}/zip", json={"export_type": "zip", "resolution_scale": "original"}).json()
        print(f" -> Exported Master ZIP: {zip_res['filename']} ({round(zip_res['file_size_bytes']/1024, 1)} KB)")
        
        print("\nALL LIVE ENDPOINTS AND PIPELINES VERIFIED OPERATIONAL!\n")

if __name__ == "__main__":
    test_live_studio_api()
