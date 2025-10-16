import requests, json, time, os, sys
from requests.exceptions import RequestException
from rich.console import Console
from rich import print as printf
from rich.panel import Panel
from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn, TimeRemainingColumn
from faker import Faker
from fake_useragent import UserAgent

# Counters
SUKSES, GAGAL, LOOPING, ERROR = (0, 0, 0, 0)

def tampilkan_logo():
    os.system('cls' if os.name == 'nt' else 'clear')
    printf(Panel("[bold red]Free Instagram Likes - [green]Nakrutka Version", width=60))

def parameter_palsu(link: str) -> dict:
    fake = Faker()
    return {
        "username": fake.user_name(),
        "link": link,
        "email": fake.email(domain='gmail.com')
    }

def kirimkan_suka(link: str) -> bool:
    global SUKSES, GAGAL, LOOPING, ERROR
    try:
        with requests.Session() as session:
            headers = {
                "User-Agent": UserAgent().random,
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/x-www-form-urlencoded",
                "Referer": "https://nakrutka.com/my/freelikes.php"
            }

            # ⚠️ Replace this payload with Nakrutka's actual required form data
            payload = parameter_palsu(link)

            response = session.post(
                "https://nakrutka.com/my/freelikes.php",
                data=payload,
                headers=headers,
                timeout=15
            )

            LOOPING += 1

            if response.status_code == 200:
                printf(f"[green]Request sent successfully to Nakrutka for {link}")
                SUKSES += 1
                return True
            else:
                printf(f"[red]Request failed: HTTP {response.status_code}")
                GAGAL += 1
                return False

    except RequestException as e:
        printf(f"[red]Network error: {e}")
        ERROR += 1
        time.sleep(3)
        return False

def main():
    tampilkan_logo()
    link = Console().input("[bold white]Enter your Instagram post link: ")
    if not link.startswith("https://www.instagram.com/"):
        printf("[red]Invalid Instagram link!")
        sys.exit()

    with Progress(TextColumn("[progress.description]{task.description}"),
                  BarColumn(),
                  TimeElapsedColumn()) as progress:
        task = progress.add_task("Sending Likes", total=1)
        kirimkan_suka(link)
        progress.update(task, advance=1)

    printf(Panel(f"[bold white]Done! Success: {SUKSES}, Failed: {GAGAL}, Errors: {ERROR}"))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit()
