from flask import Flask, request, render_template
import os, tempfile, pickle, re, time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

app = Flask(__name__)

# Załadowanie modeli
with open("meta_clf.pkl","rb") as f:
    meta_clf = pickle.load(f)
df_wagi = pd.read_pickle("df_wagi_per_kat.pkl")

# Konfiguracja detektorów
SITES = [
    {
        "name": "AI Image Detector",
        "url": "https://aiimagedetector.org/",
        "file_input_selector": "input[type='file']",
        "result_selector": "h4.text-lg span.text-base",
        "analyze_button_selector": "//button[contains(text(),'Analyze')]",
        "invert": True 
    },
    {
        "name": "The Detector AI",
        "url": "https://thedetector.ai/",
        "file_input_selector": "input[type='file']",
        "result_selector": "p.text-gray-400",
        "analyze_button_selector": "//button[contains(text(),'Analyze Image')]",
        "invert": False
    },
    {
        "name": "Ai Detect Content",   
        "url": "https://aidetectcontent.com/ai-generated-image-detector/",
        "file_input_selector": "input[type='file']",
        "result_section_id": "result-section",
        "fake_percentage_id": "fake_percentage",
        "analyze_button_selector": "//button[contains(text(),'Check Image')]",
        "invert": False
    }
]

modele = {
    'ai_image_detector': 'AI Image Detector',
    'the_detector_ai':   'The Detector AI',
    'ai_detect_content': 'Ai Detect Content' 
}

# Flaga i wartości symulowane
SIMULATE_AI_IMAGE_DETECTOR = True
SIMULATED_VALUES = {
    "animal": 0.506102,
    "building": 0.501020,
    "food": 0.481286
}

def analyze_image_on_site(driver, site, img_path, category=None):
    if site["name"] == "AI Image Detector" and SIMULATE_AI_IMAGE_DETECTOR:
        val = SIMULATED_VALUES.get(category, 0.5)
        print(f"⚠️ AI Image Detector jest offline. Zwracam symulowaną wartość: {val} dla kategorii: {category}")
        return val

    driver.get(site["url"])
    wait = WebDriverWait(driver, 30)
    inp = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, site["file_input_selector"])))
    inp.send_keys(img_path)
    try:
        btn = wait.until(EC.element_to_be_clickable((By.XPATH, site["analyze_button_selector"])))
        btn.click()
    except:
        inp.send_keys(Keys.ENTER)

    if site["name"] == "Ai Detect Content":
        wait.until(EC.visibility_of_element_located((By.ID, site["result_section_id"])))
        txt = driver.find_element(By.ID, site["fake_percentage_id"]).text
    elif site["name"] == "The Detector AI":
        txt = ""
        for _ in range(3):
            elems = driver.find_elements(By.CSS_SELECTOR, site["result_selector"])
            txt = next((e.text for e in elems if "%" in e.text), "")
            if txt:
                break
            time.sleep(5)
        if not txt:
            txt = driver.execute_script("""
                return [...document.querySelectorAll('p.text-gray-400')]
                  .find(el=>el.innerText.includes('%'))?.innerText||""
            """)
    else:
        elem = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, site["result_selector"])))
        txt = elem.text.strip()

    m = re.search(r'(\d+(?:\.\d+)?)', txt)
    if not m:
        return None
    val = float(m.group(1))
    if site.get("invert", False):
        val = 100 - val
    return val / 100.0

def get_category_from_user(cat_str):
    if cat_str.lower() in ("building","animal","food"):
        return cat_str.lower()
    raise ValueError("Nieobsługiwana kategoria")

def load_selenium():
    opts = webdriver.EdgeOptions()
    opts.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Edge(options=opts)

def compute_k1(probs, df_wagi, cat):
    votes = []
    for key, model_name in modele.items():
        T_loc = df_wagi.loc[(cat, model_name), 'Prog T']
        votes.append(int(probs[key] >= T_loc))
    return sum(votes) >= 2

def compute_k2(probs, df_wagi, cat, prog=0.5):
    P_K2 = sum(
        df_wagi.loc[(cat, model_name), 'w_i'] * probs[key]
        for key, model_name in modele.items()
    )
    return P_K2 >= prog

@app.route("/", methods=["GET","POST"])
def index():
    if request.method=="POST":
        f = request.files["image"]
        cat = get_category_from_user(request.form["category"])
        _, ext = os.path.splitext(f.filename)
        tmp = tempfile.NamedTemporaryFile(suffix=ext, delete=False)
        f.save(tmp.name)

        driver = load_selenium()
        probs = {}
        simulated = {}
        for site in SITES:
            key = next(k for k,v in modele.items() if v == site["name"])
            is_sim = site["name"] == "AI Image Detector" and SIMULATE_AI_IMAGE_DETECTOR
            p = analyze_image_on_site(driver, site, tmp.name, cat)
            probs[key] = p
            simulated[key] = is_sim
        driver.quit()
        time.sleep(0.5)
        try:
            os.unlink(tmp.name)
        except PermissionError:
            pass

        decision_k1 = compute_k1(probs, df_wagi, cat)
        decision_k2 = compute_k2(probs, df_wagi, cat)
        decision_k3 = bool(meta_clf.predict(pd.DataFrame([probs]))[0])

        return render_template("result.html",
            category=cat,
            probs=probs,
            k1=decision_k1,
            k2=decision_k2,
            k3=decision_k3,
            simulated=simulated
        )
    return render_template("index.html")

if __name__=="__main__":
    app.run(debug=True)