import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re

# Renk kodları (GitHub Actions loglarında daha iyi görünüm için)
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def siteyi_bul():
    """
    Belirtilen aralıktaki trgoals domainlerini tarar ve çalışan ilk siteyi bulur.
    """
    print(f"\n{GREEN}[*] Çalışan trgoals sitesi aranıyor...{RESET}")
    
    # Daha geniş bir aralıkta arama yapalım
    urls_to_check = [f"https://trgoals{i}.xyz/" for i in range(1300, 1500)]
    
    def check_site(url):
        try:
            # Kendimizi normal bir tarayıcı gibi tanıtıyoruz
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
            r = requests.get(url, headers=headers, timeout=7, allow_redirects=True)
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
                # Çalışan ilk siteyi bulduğumuzda diğerlerini iptal et ve adresi döndür
                executor.shutdown(wait=False, cancel_futures=True)
                return url
            elif status is False:
                print(f"{YELLOW}[-] {url} aktif ama aranan içerik yok.{RESET}")
            # else:
            #     # Çok fazla log olmaması için erişilemeyenleri yazdırmayalım
            #     # print(f"{RED}[-] {url} erişilemedi.{RESET}")
    
    print(f"{RED}[HATA] Belirtilen aralıkta çalışan hiçbir trgoals sitesi bulunamadı.{RESET}")
    return None

def kanallari_cek(base_url):
    """
    Ana sayfadan tüm kanal isimlerini ve ID'lerini çeker.
    """
    print(f"\n{GREEN}[*] Kanallar çekiliyor: {base_url}{RESET}")
    kanallar = {}
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(base_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Kanal linkleri genellikle 'a' etiketleri ve 'channel.html?id=' kalıbıyla bulunur
        for link in soup.find_all('a', href=re.compile(r'channel\.html\?id=\d+')):
            kanal_id = link['href'].split('id=')[-1]
            # Kanal adını linkin metninden veya içindeki bir resmin alt etiketinden almaya çalış
            kanal_adi = link.text.strip()
            if not kanal_adi:
                img_tag = link.find('img')
                if img_tag and img_tag.get('alt'):
                    kanal_adi = img_tag['alt'].strip()
            
            # Kanal adı ve ID'si geçerliyse listeye ekle
            if kanal_id and kanal_adi:
                # Dosya adları için geçersiz karakterleri temizle
                dosya_adi = re.sub(r'[\\/*?:"<>|]', "", kanal_adi).replace(" ", "_")
                kanallar[dosya_adi] = kanal_id
                print(f"  [+] Bulundu: {kanal_adi} (ID: {kanal_id})")
        
        print(f"{GREEN}[OK] Toplam {len(kanallar)} kanal bulundu.{RESET}")
        return kanallar
    except Exception as e:
        print(f"{RED}[HATA] Kanallar çekilirken bir sorun oluştu: {e}{RESET}")
        return {}

def m3u8_dosyalarini_olustur(kanallar):
    """
    Her kanal için 'kanallar' klasörüne ayrı bir .m3u8 dosyası oluşturur.
    """
    if not kanallar:
        print(f"{YELLOW}[-] Oluşturulacak kanal bulunmadığı için işlem atlanıyor.{RESET}")
        return

    # 'kanallar' adında bir klasör oluştur (eğer yoksa)
    output_dir = "kanallar"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"\n{GREEN}[*] M3U8 dosyaları '{output_dir}' klasörüne oluşturuluyor...{RESET}")
    
    for dosya_adi, kanal_id in kanallar.items():
        # Yayın linki, sitenin kendi player'ının kullandığı linktir.
        # Bu link doğrudan M3U8'e yönlendirme yapar.
        yayin_linki = f"https://www.trgoals.xyz/p2p.php?id={kanal_id}"
        
        m3u8_icerik = f"#EXTM3U\n#EXT-X-STREAM-INF:PROGRAM-ID=1,BANDWIDTH=2000000\n{yayin_linki}"
        
        dosya_yolu = os.path.join(output_dir, f"{dosya_adi}.m3u8")
        try:
            with open(dosya_yolu, 'w', encoding='utf-8') as f:
                f.write(m3u8_icerik)
            print(f"  [+] Oluşturuldu: {dosya_yolu}")
        except Exception as e:
            print(f"{RED}[HATA] Dosya yazılırken sorun oluştu ({dosya_yolu}): {e}{RESET}")

if __name__ == "__main__":
    aktif_site = siteyi_bul()
    if aktif_site:
        bulunan_kanallar = kanallari_cek(aktif_site)
        m3u8_dosyalarini_olustur(bulunan_kanallar)
        print(f"\n{GREEN}İşlem başarıyla tamamlandı!{RESET}")
    else:
        print(f"\n{RED}İşlem başarısız oldu. Çalışan site bulunamadı.{RESET}")
