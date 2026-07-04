# Nutrition Dashboard

A professional personal nutrition dashboard built as a Python-only Streamlit web application. It syncs with Google Sheets to visualize daily nutrition intake, macronutrient progress, micronutrient tracking, meal breakdowns, and weekly trends.

---

## Features

- **Google Sheets Integration**: Reads live data from `Food_Log` and `Daily_Targets` tabs. Automatically maps your column names to internal keys.
- **Daily Summary**: Prominent calorie card with donut chart and status indicators.
- **Macronutrient Tracking**: Protein, carbs, fat, fiber, and sugar with progress bars and status labels.
- **Micronutrient Tracking**: Vitamins, minerals, and other nutrients with horizontal progress bars.
- **Meal Breakdown**: Expandable sections for breakfast, lunch, snacks, dinner, and other meals.
- **Daily Insights**: Rule-based personalized insights (positive and warning messages).
- **Weekly Trends**: 7-day charts for calories, protein, and fiber with weekly averages.
- **Timezone Aware**: Defaults to today in **Asia/Kolkata** (India Standard Time).
- **Mock Data Fallback**: Runs with realistic demo data when Google Sheets is not configured.
- **Manual Refresh**: Clear cache and reload data on demand.

---

## Project Structure

```
nutrition-dashboard/
├── app.py                          # Main Streamlit application
├── requirements.txt                # Python dependencies
├── README.md                       # This file
├── .gitignore                      # Git ignore rules
├── .streamlit/
│   └── secrets.toml.example        # Example secrets file
├── services/
│   ├── sheets_service.py           # Google Sheets integration (with column mapping)
│   └── nutrition_service.py        # Nutrition calculations & insights
├── components/
│   ├── metric_cards.py             # Calorie, macro & micro cards
│   ├── charts.py                   # Plotly weekly trend charts
│   └── tables.py                   # Meal breakdown tables
├── config/
│   └── nutrients.py                # Nutrient defaults, metadata & column mapping
└── utils/
    └── date_utils.py               # India timezone date helpers
```

---

## Tech Stack

- **Streamlit** — Frontend and dashboard UI
- **pandas** — Data transformation and aggregation
- **gspread + Google Auth** — Google Sheets API integration
- **Plotly** — Interactive charts
- **pytz** — Timezone handling (Asia/Kolkata)
- **python-dotenv** — Environment variable support (optional)

---

## Setup

### 1. Clone / unzip the project

```bash
cd nutrition-dashboard
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Google Sheets Configuration

### Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Enable the **Google Sheets API**:
   - Navigate to **APIs & Services > Library**.
   - Search for "Google Sheets API" and click **Enable**.

### Step 2: Create a Service Account

1. Go to **APIs & Services > Credentials**.
2. Click **Create Credentials > Service Account**.
3. Fill in the details:
   - **Service account name**: `nutrition-dashboard-sa`
   - **Service account ID**: (auto-generated)
   - **Description**: `Service account for nutrition dashboard`
4. Click **Create and Continue**.
5. On the "Grant this service account access" step, select **Role: Viewer**.
6. Click **Continue**, then **Done**.

### 2.3 Create & Download the JSON Key

1. Click on your service account's **email address** in the list.
2. Go to the **Keys** tab.
3. Click **Add Key > Create New Key**.
4. Select **JSON** and click **Create**.
5. A `.json` file downloads automatically. **Keep it safe**.
6. **Do not close this page** — you need the service account email in Step 3.

---

## Step 3: Prepare Your Google Sheet

Create a new Google Sheet with **exactly these two tab names** (case-sensitive):

### Tab 1: `Food_Log`

Use these exact column headers in **Row 1** (the app will automatically map them):

| Date | Meal | Food / Drink | Serving Size (g) | Calories (kcal) | Protein (g) | Carbs (g) | Fiber (g) | Total Sugar (g) | Added Sugar (g) | Fat (g) | Saturated Fat (g) | Trans Fat (g) | Monounsaturated Fat (g) | Polyunsaturated Fat (g) | Omega-3 (g) | Omega-6 (g) | Cholesterol (mg) | Sodium (mg) | Potassium (mg) | Calcium (mg) | Iron (mg) | Magnesium (mg) | Phosphorus (mg) | Zinc (mg) | Copper (mg) | Manganese (mg) | Selenium (mcg) | Iodine (mcg) | Vitamin A (mcg RAE) | Vitamin C (mg) | Vitamin D (mcg) | Vitamin E (mg) | Vitamin K (mcg) | Thiamin B1 (mg) | Riboflavin B2 (mg) | Niacin B3 (mg) | Vitamin B6 (mg) | Folate B9 (mcg DFE) | Vitamin B12 (mcg) | Choline (mg) | Water (ml) |
|------|------|--------------|------------------|-----------------|-------------|-----------|-----------|-----------------|-----------------|---------|-------------------|---------------|-------------------------|-------------------------|-------------|-------------|------------------|-------------|----------------|--------------|-----------|----------------|-----------------|-----------|-------------|----------------|----------------|--------------|---------------------|----------------|---------------|---------------|-----------------|-----------------|----------------------|----------------|-----------------|-----------------------|-------------------|--------------|------------|

> **Note:** You do **not** need to include all these columns. The app only needs the ones it recognizes (see below). Extra columns are safely ignored. Missing recognized columns are automatically filled with `0`.

**Columns the app actually uses:**

| Your Column Header | Maps To | Purpose |
|--------------------|---------|---------|
| `Date` | `Date` | Required. Format: `YYYY-MM-DD` |
| `Meal` | `Meal` | Required. Values: `Breakfast`, `Lunch`, `Snacks`, `Dinner`, `Other` |
| `Food / Drink` | `Food` | Required. Name of the food item |
| `Serving Size (g)` | `Quantity_g` | Required. Weight in grams |
| `Calories (kcal)` | `Calories_kcal` | Calories consumed |
| `Protein (g)` | `Protein_g` | Protein in grams |
| `Carbs (g)` | `Carbs_g` | Carbohydrates in grams |
| `Fiber (g)` | `Fiber_g` | Dietary fiber in grams |
| `Total Sugar (g)` | `Sugar_g` | Total sugar in grams (limit nutrient) |
| `Fat (g)` | `Fat_g` | Total fat in grams |
| `Saturated Fat (g)` | `Saturated_Fat_g` | Saturated fat in grams (limit) |
| `Cholesterol (mg)` | `Cholesterol_mg` | Cholesterol in mg (limit) |
| `Sodium (mg)` | `Sodium_mg` | Sodium in mg (limit) |
| `Potassium (mg)` | `Potassium_mg` | Potassium in mg (target) |
| `Calcium (mg)` | `Calcium_mg` | Calcium in mg (target) |
| `Iron (mg)` | `Iron_mg` | Iron in mg (target) |
| `Magnesium (mg)` | `Magnesium_mg` | Magnesium in mg (target) |
| `Zinc (mg)` | `Zinc_mg` | Zinc in mg (target) |
| `Vitamin A (mcg RAE)` | `Vitamin_A_mcg` | Vitamin A in mcg (target) |
| `Vitamin C (mg)` | `Vitamin_C_mg` | Vitamin C in mg (target) |
| `Vitamin D (mcg)` | `Vitamin_D_mcg` | Vitamin D in mcg (target) |
| `Vitamin E (mg)` | `Vitamin_E_mg` | Vitamin E in mg (target) |
| `Vitamin K (mcg)` | `Vitamin_K_mcg` | Vitamin K in mcg (target) |
| `Folate B9 (mcg DFE)` | `Folate_mcg` | Folate in mcg (target) |
| `Vitamin B12 (mcg)` | `Vitamin_B12_mcg` | Vitamin B12 in mcg (target) |
| `Omega-3 (g)` | `Omega_3_g` | Omega-3 in grams (target) |
| `Water (ml)` | `Water_ml` | Water in ml (target) |

> **Tip:** If you have extra columns (like `Added Sugar (g)`, `Trans Fat (g)`, `Omega-6 (g)`, etc.), they are safely ignored by the app. If you are missing some of the mapped columns, the app will simply show `0` for those nutrients.

### Tab 2: `Daily_Targets`

| Nutrient | Target | Unit | Type |
|----------|--------|------|------|
| Calories_kcal | 2200 | kcal | target |
| Protein_g | 120 | g | target |
| Sugar_g | 50 | g | limit |
| Sodium_mg | 2300 | mg | limit |
| ... | ... | ... | ... |

- **Nutrient**: Must use the **internal key names** from the table above (e.g., `Calories_kcal`, `Protein_g`, `Sugar_g`).
- **Target**: The numeric goal or limit.
- **Unit**: Display unit (e.g., `g`, `mg`, `kcal`).
- **Type**: Either `target` (goal to reach) or `limit` (maximum to stay under).

If the `Daily_Targets` tab is missing or incomplete, the app falls back to built-in default values.

### 3.2 Get the Sheet ID

1. Open your Google Sheet in the browser.
2. Look at the URL:
   ```
   https://docs.google.com/spreadsheets/d/1aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890/edit
   ```
3. Copy the long string between `/d/` and `/edit` — this is your **Sheet ID**.

### 3.3 Share the Sheet with the Service Account

1. In your Google Sheet, click **Share** (top right).
2. Paste the **service account email** from Step 2 (e.g., `nutrition-dashboard-sa@your-project.iam.gserviceaccount.com`).
3. Set permission to **Editor**.
4. Click **Send**.

---

## Step 4: Set Up `secrets.toml`

### 4.1 Copy the example file

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

### 4.2 Open the downloaded JSON key

Open the `.json` file from Step 2 in a text editor. It looks like this:

```json
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "abc123...",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n",
  "client_email": "nutrition-dashboard-sa@your-project.iam.gserviceaccount.com",
  "client_id": "123456789",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
}
```

### 4.3 Fill in `secrets.toml`

Open `.streamlit/secrets.toml` and copy the values from the JSON file.

**Important formatting rules:**
- For `private_key`, replace every actual newline with `\n` (two backslashes + n).
- All values must be wrapped in double quotes.

```toml
[google_sheets]
type = "service_account"
project_id = "your-project-id"
private_key_id = "abc123..."
private_key = "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----\n"
client_email = "nutrition-dashboard-sa@your-project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/nutrition-dashboard-sa%40your-project.iam.gserviceaccount.com"

# Your Google Sheet ID from Step 3.2
sheet_id = "1aBcDeFgHiJkLmNoPqRsTuVwXyZ1234567890"
```

> **Security tip:** `.streamlit/secrets.toml` is already in `.gitignore`, so it will never be committed to Git.

---

## Running Locally

```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`.

If Google Sheets credentials are **not configured**, the app runs with realistic **mock/demo data**.

---

## Deployment to Streamlit Community Cloud

### Step 1: Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Deploy

1. Go to [Streamlit Community Cloud](https://streamlit.io/cloud).
2. Sign in with GitHub.
3. Click **New App**.
4. Select your repository, branch (`main`), and file (`app.py`).
5. In **Advanced Settings**, paste your secrets from `.streamlit/secrets.toml` into the secrets manager.
6. Click **Deploy**.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Food_Log sheet missing required columns after mapping` | Make sure Row 1 of your `Food_Log` tab has the exact headers shown above. The app needs at least `Date`, `Meal`, `Food / Drink`, and `Serving Size (g)`. |
| `Could not load Google Sheets data` | Check that the service account email has access to the sheet and the **Google Sheets API** is enabled. |
| `private_key` format error | In `secrets.toml`, use `\n` for every newline in the private key. |
| `SpreadsheetNotFound` | Verify the `sheet_id` is correct and the sheet is shared with the service account. |
| Data doesn't update after editing | Click **Refresh Data** in the sidebar to clear the 5-minute cache. |
| App shows 0 for all nutrients | Check that your `Food_Log` column headers match the expected names exactly (including spaces and parentheses). |

---

## License

MIT License — feel free to use and modify for personal or commercial projects.
