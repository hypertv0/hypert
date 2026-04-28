import re
import sys
import time
import os
from playwright.sync_api import sync_playwright

# --- Ayarlar ---
# Playerların çoğu kısa User-Agent sever, o yüzden "Mozilla/5.0" olarak kısalttım.
USER_AGENT = "Mozilla/5.0"

def find_working_domain(context):
    print("\n🔍 Çalışan Taraftarium domain aranıyor...")
    for num in range(1053, 1075):        
        test_url = f"https://taraftarium{num}.xyz/"
        page = context.new_page()
        try:
            response = page.goto(test_url, timeout=10000, wait_until='domcontentloaded')
            if response and response.ok:
                final_url = page.url.rstrip('/')
                if not any(x in page.title().lower() for x in ["cloudflare", "just a moment", "bekleyin"]):
                    print(f"✅ Bulundu: {final_url}")
                    page.close()
                    return final_url
        except:
            pass
        finally:
            page.close()
    return None

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)

        domain = find_working_domain(context)
        if not domain:
            print("❌ Domain bulunamadı.")
            return

        # Kanallar ve tvg-id eşleşmeleri (Senin eski listendeki id'ler)
        channels = {
            "taraftarium": ("Bein Sports 1 HD", "BeinSports1.tr"),
            "b2": ("Bein Sports 2 HD", "BeinSports2.tr"),
            "b3": ("Bein Sports 3 HD", "BeinSports3.tr"),
            "b4": ("Bein Sports 4 HD", "BeinSports4.tr"),
            "b5": ("Bein Sports 5 HD", "BeinSports5.tr"),
            "bm1": ("Bein Max 1 HD", "BeinMax1.tr"),
            "bm2": ("Bein Max 2 HD", "BeinMax2.tr"),
            "ss": ("S Sport 1 HD", "SSport1.tr"),
            "ss2": ("S Sport 2 HD", "SSport2.tr"),
            "t1": ("Tivibu Spor 1 HD", "TivibuSpor1.tr"),
            "t2": ("Tivibu Spor 2 HD", "TivibuSpor2.tr"),
            "t3": ("Tivibu Spor 3 HD", "TivibuSpor3.tr"),
            "smarts": ("Smart Spor 1 HD", "SmartSpor1.tr"),
            "sms2": ("Smart Spor 2 HD", "SmartSpor2.tr"),
            "trtspor": ("TRT Spor HD", "TRTSpor.tr"),
            "trtspor2": ("TRT Spor Yıldız HD", "TRTSporYildiz.tr"),
            "as": ("A Spor HD", "ASpor.tr"),
            "atv": ("ATV HD", "ATV.tr"),
            "tv8": ("TV8 HD", "TV8.tr"),
            "tv85": ("TV8.5 HD", "TV85.tr"),
            "nbatv": ("NBA TV HD", "NBATV.tr")
        }

        output_dir = "kanallar"
        os.makedirs(output_dir, exist_ok=True)
        global_playlist = ["#EXTM3U"]
        
        regex_fallback = re.compile(r'["\'](https?://[^"\'\s]+?\.(?:sbs|xyz|com|net)/?[^"\'\s]*?\.m3u8[^"\'\s]*)["\']', re.IGNORECASE)
        page = context.new_page()

        for channel_id, (name, tvg_id) in channels.items():
            print(f"📡 Çekiliyor: {name}...", end=" ")
            try:
                url = f"{domain}/channel.html?id={channel_id}"
                captured_url = None

                def handle_req(request):
                    nonlocal captured_url
                    if ".m3u8" in request.url.lower(): captured_url = request.url

                page.on("request", handle_req)
                page.goto(url, timeout=15000)
                page.wait_for_timeout(3000) # Linkin düşmesi için bekle

                if not captured_url:
                    match = regex_fallback.search(page.content())
                    if match: captured_url = match.group(1)

                if captured_url:
                    # --- DOSYA İÇERİĞİ (Senin istediğin o eski çalışan format) ---
                    content = [
                        "#EXTM3U",
                        f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}',
                        f"#EXTVLCOPT:http-user-agent={USER_AGENT}",
                        f"#EXTVLCOPT:http-referrer={domain}/",
                        captured_url
                    ]

                    # 1. Tekil Dosya
                    clean_name = re.sub(r'[\\/*?:"<>|]', "", name).replace(" ", "_")
                    with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                        f.write("\n".join(content))

                    # 2. Genel Liste (Playlist.m3u)
                    global_playlist.append(f'#EXTINF:-1 tvg-id="{tvg_id}" tvg-name="{name}",{name}')
                    global_playlist.append(f"#EXTVLCOPT:http-user-agent={USER_AGENT}")
                    global_playlist.append(f"#EXTVLCOPT:http-referrer={domain}/")
                    global_playlist.append(captured_url)
                    
                    print("✅")
                else:
                    print("❌")

            except:
                print("⚠️ Hata")
            finally:
                page.remove_listener("request", handle_req)

        # Playlist'i kaydet
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(global_playlist))

        browser.close()
        print("\n🎉 İşlem bitti. Dosyalar ExoPlayer uyumlu hale getirildi.")

if __name__ == "__main__":
    main()
