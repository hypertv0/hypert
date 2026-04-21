import re
import sys
import time
import os
from playwright.sync_api import sync_playwright, Error as PlaywrightError

# --- Renk Kodları ---
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36'

def find_working_domain(context):
    """Taraftarium104x serisini otomatik tarar"""
    print(f"\n{YELLOW}🔍 Çalışan Taraftarium domain aranıyor...{RESET}\n")

    print(f"📈 Otomatik artış taraması yapılıyor (1041 → 1060)...")
    for num in range(1041, 1061):        
        test_url = f"https://taraftarium{num}.xyz/"
        print(f"   Deniyor → taraftarium{num}.xyz", end=" ")

        page = context.new_page()
        try:
            response = page.goto(test_url, timeout=12000, wait_until='domcontentloaded')
            if not response or not response.ok:
                print(f"{RED}❌{RESET}")
                continue

            final_url = page.url.rstrip('/')
            title = page.title().lower()

            if any(x in title for x in["giris", "cloudflare", "attention", "just a moment", "dikkat", "bekleyin"]):
                print(f"{YELLOW}⚠️ Koruma sayfası{RESET}")
                continue

            print(f"{GREEN}✅ BULUNDU!{RESET}")
            page.close()
            return final_url

        except Exception:
            print(f"{RED}❌{RESET}")
        finally:
            page.close()
            time.sleep(1.1)

    print(f"\n{RED}❌ Bu aralıkta çalışan domain bulunamadı.{RESET}")
    return None

def main():
    with sync_playwright() as p:
        print(f"{GREEN}🚀 Otomatik M3U8 İndirici Başlatılıyor...{RESET}\n")

        browser_args =[
            '--autoplay-policy=no-user-gesture-required',
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-gpu',
        ]
        
        browser = p.chromium.launch(headless=True, args=browser_args)
        context = browser.new_context(
            user_agent=USER_AGENT,
            ignore_https_errors=True,
            viewport={'width': 1366, 'height': 768}
        )

        # ==================== DOMAIN BUL ====================
        domain = find_working_domain(context)
        
        if not domain:
            print(f"\n{RED}❌ Çalışan domain bulunamadı. X'ten güncel linki kontrol et.{RESET}")
            browser.close()
            sys.exit(1)

        print(f"\n{GREEN}📡 Kullanılan Domain: {domain}{RESET}\n")

        # ==================== KANALLAR ====================
        channels = {
            "taraftarium": ("BeIN Sports 1", "BeinSports"),
            "b2": ("BeIN Sports 2", "BeinSports"),
            "b3": ("BeIN Sports 3", "BeinSports"),
            "b4": ("BeIN Sports 4", "BeinSports"),
            "b5": ("BeIN Sports 5", "BeinSports"),
            "bm1": ("BeIN Sports 1 Max", "BeinSports"),
            "bm2": ("BeIN Sports 2 Max", "BeinSports"),
            "ss": ("S Sport 1", "S Sports"),
            "ss2": ("S Sport 2", "S Sports"),
            "t1": ("Tivibu Sports 1", "Tivibu"),
            "t2": ("Tivibu Sports 2", "Tivibu"),
            "t3": ("Tivibu Sports 3", "Tivibu"),
            "t4": ("Tivibu Sports 4", "Tivibu"),
            "smarts": ("Smart Spor", "Smart Sports"),
            "sms2": ("Smart Spor 2", "Smart Sports"),
            "trtspor": ("TRT Spor", "TRT"),
            "trtspor2": ("TRT Spor 2", "TRT"),
            "as": ("A Spor", "Ulusal"),
            "atv": ("ATV", "Ulusal"),
            "tv8": ("TV8", "Ulusal"),
            "tv85": ("TV8.5", "Ulusal"),
            "nbatv": ("NBA TV", "NBA"),
            "eu1": ("Eurosport 1", "Eurosport"),
        }

        # Klasörleri ve listeleri hazırla
        output_dir = "kanallar"
        os.makedirs(output_dir, exist_ok=True)
        global_m3u_content =[]
        created = 0
        debug_saved = False

        regex_fallback = re.compile(r'["\'](https?://[^"\'\s]+?\.(?:sbs|xyz|com|net)/?[^"\'\s]*?(?:mono|index|playlist)\.m3u8[^"\'\s]*)["\']', re.IGNORECASE)

        page = context.new_page()

        for i, (channel_id, (channel_name, category)) in enumerate(channels.items(), 1):
            try:
                print(f"[{i}/{len(channels)}] {channel_name} ({channel_id})...", end=' ')
                sys.stdout.flush()

                url = f"{domain.rstrip('/')}/channel.html?id={channel_id}"
                captured_m3u8 = None

                def handle_request(request):
                    nonlocal captured_m3u8
                    req_url = request.url.lower()
                    if ".m3u8" in req_url and any(x in req_url for x in ["mono", "index", "playlist"]):
                        captured_m3u8 = request.url

                page.on("request", handle_request)

                try:
                    page.goto(url, timeout=18000, wait_until='domcontentloaded')
                    page.wait_for_timeout(1200)

                    # Player tetikleme
                    try:
                        page.click('body', timeout=2000)
                        page.wait_for_timeout(800)
                        page.click('iframe', timeout=2000)
                    except:
                        pass

                    # m3u8 düşmesini bekle
                    start_time = time.time()
                    while time.time() - start_time < 10:
                        if captured_m3u8:
                            break
                        page.wait_for_timeout(700)

                    found_url = None
                    if captured_m3u8:
                        found_url = captured_m3u8
                        print(f"-> {GREEN}✅ Sniff OK{RESET}")
                    else:
                        content = page.content()
                        match = regex_fallback.search(content)
                        if match:
                            found_url = match.group(1)
                            print(f"-> {GREEN}✅ Regex OK{RESET}")
                        else:
                            print(f"-> {RED}❌ Link bulunamadı{RESET}")
                            if not debug_saved:
                                with open("debug_channel.html", "w", encoding="utf-8") as f:
                                    f.write(content)
                                debug_saved = True

                    # Eğer URL bulunduysa hem tekil dosyaya hem genel listeye yaz
                    if found_url:
                        # Dosya adındaki geçersiz karakterleri temizle
                        clean_name = re.sub(r'[\\/*?:"<>|]', "", channel_name).replace(" ", "_")
                        
                        # Kanal için oluşturulacak ortak M3U formatı
                        channel_data =[
                            f'#EXTINF:-1 tvg-name="{channel_name}" group-title="{category}",{channel_name}',
                            f'#EXTVLCOPT:http-user-agent={USER_AGENT}',
                            f'#EXTVLCOPT:http-referrer={domain}/',
                            f'#EXT-X-USER-AGENT:{USER_AGENT}',
                            f'#EXT-X-REFERER:{domain}/',
                            f'#EXT-X-ORIGIN:{domain}',
                            found_url
                        ]

                        # 1. Tekil Dosyayı Oluştur (kanallar/Kanal_Adi.m3u8)
                        single_file_content = ["#EXTM3U"] + channel_data
                        with open(os.path.join(output_dir, f"{clean_name}.m3u8"), "w", encoding="utf-8") as f:
                            f.write("\n".join(single_file_content))

                        # 2. Genel Listeye Ekle
                        global_m3u_content.extend(channel_data)
                        created += 1

                except Exception as e:
                    print(f"-> {RED}❌ Hata: {str(e)[:60]}{RESET}")
                finally:
                    page.remove_listener("request", handle_request)
                    page.wait_for_timeout(800)

            except Exception as e:
                print(f"-> {RED}❌ Genel hata: {e}{RESET}")
                continue

        browser.close()

        # En son tüm kanalları içeren Toplu Playlist'i oluştur
        if created > 0:
            with open("playlist.m3u", "w", encoding="utf-8") as f:
                f.write("#EXTM3U\n\n" + "\n".join(global_m3u_content))
            
            print(f"\n{GREEN}🎉 Tamamlandı! {created} kanal kaydedildi.{RESET}")
            print(f"{GREEN}📁 'kanallar' klasörüne tekil dosyalar ve ana dizine 'playlist.m3u' eklendi.{RESET}")
        else:
            print(f"\n{RED}❌ Hiçbir kanal için m3u8 linki yakalanamadı.{RESET}")

if __name__ == "__main__":
    main()
