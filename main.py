import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
from datetime import datetime

# Renk kodları ve loglama için başlıklar
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'
INFO = f"{GREEN}[INFO]{RESET}"
WARN = f"{YELLOW}[UYARI]{RESET}"
ERROR = f"{RED}[HATA]{RESET}"

def siteyi_bul():
    """Belirtilen aralıktaki trgoals domainlerini tarar ve çalışan ilk siteyi bulur."""
    print(f"\n{INFO} Çalışan trgoals sitesi aranıyor...")
    
    # Arama aralığını geniş tutalım
    urls_to_check = [f"https://trgoals{i}.xyz/" for i in range(1000, 1600)]
    
    def check_site(url):
        try:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            # allow_redirects=True, sitenin yönlendirmelerini takip etmesini sağlar
            r = requests.get(url, headers=headers, timeout=8, allow_redirects=True)
            if r.status_code == 200 and "channel.html?id=" in r.text:
                return url, True
            return url, False
        except requests.RequestException:
            return url, None

    with ThreadPoolExecutor(max_workers=30) as executor:
        future_to_url = {executor.submit(check_site, url): url for url in urls_to_check}
        for future in as_completed(future_to_url):
            url, status = future.result()
            if status is True:
                print(f"{GREEN}[OK] Çalışan site bulundu: {url}{RESET}")
                executor.shutdown(wait=False) # Diğerlerini bekleme
                return url

    print(f"{ERROR} Belirtilen aralıkta çalışan hiçbir trgoals sitesi bulunamadı.")
    return None

def kanallari_cek(base_url):
    """Ana sayfadan tüm kanal isimlerini ve ID'lerini çeker."""
    print(f"\n{INFO} Kanallar çekiliyor: {base_url}")
    kanallar = {}
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for link in soup.find_all('a', href=re.compile(r'channel\.html\?id=\d+')):
            kanal_id = link['href'].split('id=')[-1]
            kanal_adi = link.text.strip()
            if not kanal_adi:
                img_tag = link.find('img')
                if img_tag and img_tag.get('alt'):
                    kanal_adi = img_tag['alt'].strip()
            
            if kanal_id and kanal_adi:
                # Dosya adları için geçersiz karakterleri temizle ve boşlukları _ ile değiştir
                dosya_adi = re.sub(r'[\\/*?:"<>|]', "", kanal_adi).replace(" ", "_")
                kanallar[dosya_adi] = kanal_id
        
        print(f"{GREEN}[OK] Toplam {len(kanallar)} kanal bulundu.{RESET}")
        return kanallar
    except Exception as e:
        print(f"{ERROR} Kanallar çekilirken bir sorun oluştu: {e}")
        return {}

def m3u8_dosyalarini_olustur_ve_guncelle(kanallar, base_url):
    """
    Her kanal için 'kanallar' klasörüne ayrı bir .m3u8 dosyası oluşturur.
    Eğer hiç kanal bulunamazsa, klasörün içine bir bilgi notu bırakır.
    """
    output_dir = "kanallar"
    print(f"\n{INFO} '{output_dir}' klasörü kontrol ediliyor ve dosyalar oluşturuluyor...")
    os.makedirs(output_dir, exist_ok=True)
    
    if not kanallar:
        print(f"{WARN} Hiç kanal bulunamadı. '{output_dir}/bilgi.txt' dosyası oluşturuluyor.")
        with open(os.path.join(output_dir, 'bilgi.txt'), 'w', encoding='utf-8') as f:
            f.write(f"Kanal listesi son kontrol edildiğinde ({datetime.utcnow().isoformat()}Z) aktif bir site bulunamadı.")
        return 0

    kanallar_olusturuldu = 0
    for dosya_adi, kanal_id in kanallar.items():
        # trgoals'un yönlendirme yaptığı nihai p2p linkini kullanıyoruz
        yayin_linki = f"https://www.trgoals.xyz/p2p.php?id={kanal_id}"
        
        m3u8_icerik = f"#EXTM3U\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2000000\n{yayin_linki}"
        
        dosya_yolu = os.path.join(output_dir, f"{dosya_adi}.m3u8")
        try:
            with open(dosya_yolu, 'w', encoding='utf-8') as f:
                f.write(m3u8_icerik)
            kanallar_olusturuldu += 1
        except Exception as e:
            print(f"{ERROR} Dosya yazılırken sorun oluştu ({dosya_yolu}): {e}")
            
    print(f"{GREEN}[OK] {kanallar_olusturuldu} adet M3U8 dosyası başarıyla oluşturuldu/güncellendi.{RESET}")
    return kanallar_olusturuldu

if __name__ == "__main__":
    aktif_site = siteyi_bul()
    if aktif_site:
        bulunan_kanallar = kanallari_cek(aktif_site)
        m3u8_dosyalarini_olustur_ve_guncelle(bulunan_kanallar, aktif_site)
        print(f"\n{GREEN}İşlem başarıyla tamamlandı!{RESET}")
    else:
        # Çalışan site bulunamasa bile klasörün varlığını garanti altına al
        m3u8_dosyalarini_olustur_ve_guncelle({}, None)
        print(f"\n{RED}İşlem başarısız oldu. Çalışan site bulunamadı.{RESET}")
