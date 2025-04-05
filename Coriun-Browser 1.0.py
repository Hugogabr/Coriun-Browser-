import cloudscraper
from bs4 import BeautifulSoup
import os
from urllib.parse import urljoin
import uuid
import atexit
import shutil
import mimetypes
import time
from colorama import Fore, Style, init

# ==== CONFIGURAÇÕES ====
IMG_DIR = "imgs"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Referer": "https://www.google.com"
}

# Inicializa colorama e scraper
init(autoreset=True)
scraper = cloudscraper.create_scraper()
os.makedirs(IMG_DIR, exist_ok=True)

# Histórico de navegação
history = []

def tem_catimg():
    return shutil.which("catimg") is not None

def exibir_imagem(nome):
    if os.system(f"catimg '{nome}'") != 0:
        if shutil.which("termux-open"):
            os.system(f"termux-open '{nome}'")
    else:
        print(f"(Visualização indisponível)")
        print(f"(Visualização indisponível. Imagem salva em {nome})")

@atexit.register
def limpar_imgs():
    shutil.rmtree(IMG_DIR, ignore_errors=True)

def limpar():
    os.system("clear" if os.name == "posix" else "cls")

def mostrar_imagens(soup, base_url):
    imgs = soup.find_all("img")
    print(f"\n{Fore.MAGENTA}Encontradas {len(imgs)} imagem(ns).{Style.RESET_ALL}")
    for img in imgs:
        src = img.get("src")
        if not src:
            continue
        src = urljoin(base_url, src)
        try:
            tipo = scraper.head(src, headers=HEADERS).headers.get("Content-Type", "")
            ext = mimetypes.guess_extension(tipo.split(";")[0]) or ".jpg"
            nome = f"{IMG_DIR}/img_{uuid.uuid4().hex}{ext}"
            img_res = scraper.get(src, headers=HEADERS)
            img_res.raise_for_status()
            with open(nome, "wb") as f:
                f.write(img_res.content)
            exibir_imagem(nome)
        except Exception as e:
            print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} ao baixar a imagem: {e}")

def exibir_links(url):
    limpar()
    print(f"Acessando: {url}\n")
    try:
        inicio = time.perf_counter()
        res = scraper.get(url, headers=HEADERS)
        res.raise_for_status()
        duracao = time.perf_counter() - inicio
        print(f"{Fore.YELLOW}[INFO]{Style.RESET_ALL} Carregado em {duracao:.2f}s")

        soup = BeautifulSoup(res.text, "html.parser")
        mostrar_imagens(soup, url)

        links = soup.find_all("a")
        opcoes = []

        for link in links:
            texto = (link.text or link.get('title') or '').strip()
            href = link.get('href')
            if not texto or not href:
                continue
            texto = (texto[:60] + '...') if len(texto) > 60 else texto
            print(f"{Fore.GREEN}[{len(opcoes)}] {texto}{Style.RESET_ALL}")
            opcoes.append(urljoin(url, href))

        if history:
            print(f"{Fore.CYAN}[b] Voltar para página anterior{Style.RESET_ALL}")

        escolha = input("\nEscolha um link (ou 'b' para voltar): ")
        if escolha == 'b' and history:
            exibir_links(history.pop())
        elif escolha.isdigit() and int(escolha) < len(opcoes):
            history.append(url)
            exibir_links(opcoes[int(escolha)])
        else:
            print("Entrada inválida. Pressione ENTER para continuar...")
            input()

    except Exception as e:
        print(f"{Fore.RED}[ERRO]{Style.RESET_ALL} ao acessar a página: {e}")
        input("Pressione ENTER pra continuar...")

# Execução inicial
if __name__ == "__main__":
    url = input("URL inicial: ").strip()
    if not url.startswith("http"):
        url = "https://" + url
    exibir_links(url)