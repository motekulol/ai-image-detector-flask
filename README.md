# Aplikacja Flask – Detekcja Obrazów AI

Temat pracy magisterskiej: **Metody detekcji treści generowanej przez sztuczną inteligencję w obszarze rozwiązań graficznych.**.

---

## Opis

Aplikacja pozwala użytkownikowi przesłać obraz i określić jego kategorię (`animal`, `building`, `food`), a następnie:
  - korzysta z 3 detektorów online służących ocenie zdjęcia pod kątem SI (z użyciem Selenium),
  - integruje wyniki w ramach **trzech komitetów decyzyjnych** (`K1`, `K2`, `K3`),
  - wyświetla końcową decyzję: czy obraz jest wygenerowany przez SI.

---

## Wymagania

- Python 3.10+ (testowano na 3.11)
- Microsoft Edge (zainstalowany)
- **Microsoft Edge WebDriver** – wersja zgodna z przeglądarką  
  (https://developer.microsoft.com/en-us/microsoft-edge/tools/webdriver/)

---

## Instalacja i uruchomienie

```bash
# 1. Klonowanie repozytorium
git clone https://github.com/motekulol/ai-image-detector-flask.git
cd ai-image-detector-flask

# 2. Instalacja zależności
pip install -r requirements.txt

# 3. Uruchomienie aplikacji Flask
python app.py
