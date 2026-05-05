# Pipedrive → n8n → Cluster Label Automation

## Αρχεία
- `cluster_api.py` — Flask API που διαβάζει το CSV και επιστρέφει label
- `n8n_workflow.json` — Workflow που κάνεις import στο n8n
- `output.csv` — Το CSV με τα clusters (βάλε το δίπλα στο cluster_api.py)

---

## ΒΗΜΑ 1: Στήσε το Flask API

### Απαιτήσεις
```bash
pip install flask pandas
```

### Εκτέλεση
```bash
# Βάλε το output.csv στον ίδιο φάκελο με το cluster_api.py
python cluster_api.py
# Τρέχει στο http://0.0.0.0:5055
```

### Test
```bash
curl "http://localhost:5055/health"
curl "http://localhost:5055/lookup?tk=16674"
# Επιστρέφει: {"cluster_name":"...","extra_slots":168.0,"label":"Hot","municipal":"ΓΛΥΦΑΔΑΣ","name":"ΓΛΥΦΑΔΑ","tk":16674}
```

### Για production (systemd service)
```ini
# /etc/systemd/system/cluster-api.service
[Unit]
Description=Cluster API
After=network.target

[Service]
WorkingDirectory=/path/to/your/folder
ExecStart=/usr/bin/python3 cluster_api.py
Restart=always

[Install]
WantedBy=multi-user.target
```
```bash
systemctl enable cluster-api
systemctl start cluster-api
```

---

## ΒΗΜΑ 2: Import στο n8n

1. Άνοιξε n8n → **Workflows** → **Import from file**
2. Επίλεξε `n8n_workflow.json`
3. Κάνε τις παρακάτω αλλαγές:

---

## ΒΗΜΑ 3: Τα 5 σημεία που πρέπει να προσαρμόσεις

### 1. Stage ID (node: "IF: Correct Stage?")
- Pipedrive → Settings → Pipeline → αντέγραψε το ID του stage
- Αντικατάστησε `YOUR_STAGE_ID`

### 2. Email template (node: "Send Email Template")
- Βάλε το HTML template σου στο `message`
- Άλλαξε το `fromEmail`

### 3. Custom field keys (node: "Pipedrive: Save Address")
- Pipedrive → Settings → Custom Fields → αντέγραψε το API key
- Αντικατάστησε `ADDRESS_FIELD_KEY` και `TK_FIELD_KEY`

### 4. Server IP (node: "Cluster API Lookup")
- Αντικατάστησε `YOUR_SERVER_IP` με την IP του server που τρέχει το Flask API

### 5. Labels στο Pipedrive
- Pipedrive → Settings → Labels → δημιούργησε: **Very Low**, **Low**, **Medium**, **Hot**

---

## Λογική Labels

| extra_slots | Label    |
|-------------|----------|
| 0 – 50      | Very Low |
| 51 – 100    | Low      |
| 101 – 150   | Medium   |
| > 150       | Hot      |

---

## Σημείωση για το Gmail Reply detection

Το n8n δεν έχει native "wait for reply in thread". Η προτεινόμενη λύση:
- Το **Wait node** κάνει resume μετά από 10 μέρες (timeout path → Lost)
- Το **Gmail Trigger** παρακολουθεί το inbox και κάνει resume το Wait νωρίτερα αν έρθει reply
- Στο "IF: Got Reply?" ελέγχει αν το threadId ταιριάζει

Εναλλακτικά, αν θέλεις πιο απλή λύση: χρησιμοποίησε **polling** (Gmail node σε Schedule Trigger κάθε 1 ώρα) αντί για webhook.
